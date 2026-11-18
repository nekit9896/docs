---
id: KB-HM-WORKER-001
title: SessionWorker — полный алгоритм сохранения (фазы, цикл чтения, ошибки)
service: hydro-history-and-model
group: saver
source: confluence/repo_description_hydro-history-and-model#3.5, #6.4
requires: [KB-HM-SAVE-001, KB-HM-WATERMARK-001]
related: [KB-HM-EXEC-001, KB-HM-STORAGE-001, KB-HM-CONFIG-001]
status: verified
---

# SessionWorker — детальный алгоритм

## Инициализация сессии сохранения

1. `ServiceCommandListener` подписывается на сервисный топик (`historySaver.commands`).
2. `ServiceCommandListener.onMessage()` парсит JSON в `ServiceCommand`.
3. `ServiceCommandDispatcherImpl.handle()` находит хендлер по типу команды.
4. `StartSessionCommandHandler.handle()` вызывает
   `WorkerExecutorImpl.ensureRunning(sessionId, SaveSessionType.VALUE/ALARM)`.
5. `ensureRunning(sessionId, type)`:
   - проверяет существование сессии в `save_sessions`;
   - если статус терминальный (SAVED, ERROR, CANCELLED) — завершает;
   - создаёт начальное состояние ватермарка: `SaverWatermarkState.initial(sessionId, type, topic)`;
   - вызывает `WatermarkService.tryAcquire()`; при успехе передаёт
     `WatermarkLease` и `SaverWatermarkState` в `ensureRunning(lease, state)`.
6. `ensureRunning(lease, state)`:
   - проверяет соответствие `serviceName` и `resourceKey`;
   - создаёт пул воркеров (если ещё не создан);
   - создаёт ключ `WorkerKey(sessionId, type)`;
   - в `ConcurrentHashMap<WorkerKey, ActiveWorker>`: воркер с тем же epoch —
     возвращает его; воркер другого epoch — прерывает старый и создаёт новый;
   - поднимает воркер через `pool.submit(workerFactory.create(...))`.
7. `SessionWorkerFactoryImpl.create()`: для VALUE — `valueMapper`
   (`KafkaRecordMapper<SessionRecord>`) + `valueWriter`
   (`ClickHouseSessionRecordsWriter`); для ALARM — `alarmMapper`
   (`KafkaRecordMapper<AlarmRecord>`) + `alarmWriter` (`ClickHouseAlarmRecordsWriter`).

## Структура данных воркера

`sessionId`; `saveSessionType` (VALUE/ALARM); `props` — `WorkerProperties`
(**batchSize, pollTimeout, maxRuntime, statusCheckEvery**); `consumerFactory`;
`mapper` (`KafkaRecordMapper<R>`); `writer` (`RecordWriter<R>`); `saveSessionRepository`
(`save_sessions`); `progressRepository` (`save_session_progress`); `tx`
(`TransactionTemplate`); `watermarkService`; `watermarkLease`;
`watermarkRenewEvery`; `lastWatermarkTouch`.

## Основной цикл `SessionWorker.run()` — 7 фаз

### Фаза 1: Загрузка сессии и проверка статуса
`sessionId` в MDC; `SaveSessionRepository.findById(entityId)`; сессия не
найдена — освободить ватермарк и завершить; запомнить `topic` из сессии.

### Фаза 2: Валидация и перевод статуса в SAVING
В транзакции: проверка терминальности; `CREATED` → `SAVING`; уже `SAVING`/
`CANCELLING` — сбросить ошибки и продолжить; очистить `errorCode`,
`errorMessage`, `finishedAt`; сохранить.

### Фаза 3: Метаданные топика и целевые офсеты
Kafka-консьюмер с изолированным `group.id = "historySaver-source-" + sessionId`;
`consumer.partitionsFor(topic)`; партиций нет → `FAILED` с кодом `TOPIC_NOT_FOUND`;
`TopicPartition` для ручного назначения; целевые офсеты: `target = endOffset - 1`
(последняя существующая запись); `endOffset <= 0` или `begin >= end` →
`target = -1` (партиция пуста).

### Фаза 4: Инициализация/восстановление прогресса
`SaveSessionProgressEntity` из БД; для каждой партиции: нет записи — новая с
`lastFlushedOffset = -1`; `targetHighWatermark` обновляется до вычисленного
`target`; сохранить прогресс и состояние ватермарка (`saveWatermarkState()`).

### Фаза 5: Позиционирование консьюмера
`startOffset = max(beginningOffset, lastFlushedOffset + 1)`; `endExclusive = target + 1`;
`endExclusive <= 0` или `startOffset >= endExclusive` — партиция завершена
(`donePartitions`, `consumer.pause`); остальные — `consumer.seek(tp, startOffset)`.

### Фаза 6: Основной цикл чтения и записи
Пока `donePartitions.size() < partitions.size()`:
1. Таймаут: `Duration.between(startedAt, now) > maxRuntime` → `timeout = true`.
2. Раз в `statusCheckEvery` — сверка статуса в БД; `CANCELLING` → `cancelling = true`.
3. Выход: `cancelling || timeout` и `batch.isEmpty()`.
4. `consumer.poll(pollTimeout)`; `polledCount == 0` → `emptyPollCount++`, иначе сброс.
5. Обработка записей: офсет `> target` → пропуск (`skippedBeyondTarget++`);
   `mapper.map(sessionId, r)` → в `batch`; `totalRecordsProcessed++`;
   `batchMaxOffset.merge(partition, offset, max)`; `batch.size() >= batchSize`
   → `flush(...)` + `updateDoneAndPause(...)`.
6. `skippedBeyondTarget > 0` и batch не пуст → сразу `flush`; `records.isEmpty()`
   и batch не пуст → тоже `flush`.
7. Завершённые партиции: `lastFlushedOffset >= target` → `donePartitions` +
   `consumer.pause(tp)`.

### Фаза 7: Завершение сессии
`cancelling` → статус `CANCELLED`; `timeout` → статус `ERROR` с кодом `TIMEOUT`;
иначе → `SAVED`. Затем `refreshManagerStatus()` (обновление статуса в
`session_manager`) и `releaseWatermark()`.

## Функции (псевдокод)

- **flush(batch, batchMaxOffset, progressByPartition)**: `writer.writeBatch(batch)`
  (падение → `RuntimeException("Ошибка записи в ClickHouse")`); в транзакции —
  обновление `lastFlushedOffset` для затронутых партиций и
  `progressRepository.saveAll()`; `saveWatermarkState(progressByPartition)`;
  очистка `batch`/`batchMaxOffset`.
- **updateDoneAndPause(...)**: для незавершённых партиций с
  `lastFlushedOffset >= target` — добавить в `donePartitions`, `consumer.pause(toPause)`.
- **finish(status, code, message)**: в транзакции — статус/`finishedAt`/`errorCode`/
  `errorMessage`; `refreshManagerStatus()`.
- **fail(code, message)**: в транзакции — статус `ERROR`, `errorCode = code.name()`;
  `refreshManagerStatus()`.

## Управление ватермарком (во время работы)

1. `renewWatermarkIfNeeded(now)`: раз в `watermarkRenewEvery` —
   `watermarkService.renew(lease)`; renewal отклонён → `LostWatermarkOwnershipException`.
2. `saveWatermarkState(progressByPartition)`: `SaverWatermarkState.fromProgress(...)`
   → `watermarkService.saveState(lease, state)`; отклонён → `LostWatermarkOwnershipException`.
3. `releaseWatermark()`: `watermarkService.release(lease)`; отклонён —
   предупреждение в лог.

## Обработка исключений

| Исключение | Реакция |
|---|---|
| `OffsetOutOfRangeException` (офсет удалён из Kafka, retention) | сессия → `FAILED`, код `OFFSET_OUT_OF_RANGE`; освободить ватермарк |
| `IllegalStateException` (сессия уже в терминальном статусе) | освободить ватермарк |
| `LostWatermarkOwnershipException` | освободить ватермарк |
| `RuntimeException` «Ошибка записи в ClickHouse» | сессия → `FAILED`, код `CLICKHOUSE_WRITE_ERROR` |
| прочие `Exception` (ошибка чтения из Kafka) | сессия → `FAILED`, код `KAFKA_READ_ERROR` |

⚠ Расхождение источника (G12): в тексте исключений статус называется `FAILED`,
а в таблице статусов сохранятельной сессии такого статуса нет (только `ERROR`;
`fail()` фактически ставит `ERROR`, лог — «помечена как FAILED»). См.
`meta/discrepancies-2026-11-17.md`.
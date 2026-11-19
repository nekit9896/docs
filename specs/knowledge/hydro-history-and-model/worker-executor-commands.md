---
id: KB-HM-EXEC-001
title: WorkerExecutor и Kafka-команды (ServiceCommand, listener, dispatcher)
service: hydro-history-and-model
group: saver
source: confluence/repo_description_hydro-history-and-model#6.2, #6.3
requires: [KB-HM-SAVE-001, KB-HM-WATERMARK-001]
related: [KB-HM-WORKER-001, KB-HM-CLEANUP-001, KB-HM-STORAGE-001]
status: verified
---

# WorkerExecutor и Kafka-команды

## WorkerExecutor (saver.worker)

### ensureRunning(sessionId, type)
1. Проверяет существование сессии в БД.
2. Если статус терминальный — возвращает.
3. Создаёт начальное состояние ватермарка.
4. `WatermarkService.tryAcquire(SERVICE_NAME, resourceKey, initialState)`.
5. При успехе — `ensureRunning(lease, initialState)`.

### ensureRunning(lease, state)
1. Проверяет соответствие `serviceName` и `resourceKey`.
2. Создаёт пул воркеров (если ещё не создан).
3. Ключ `WorkerKey(sessionId, type)`; в `ConcurrentHashMap`: тот же epoch —
   вернуть запущенного; другой epoch — прервать старый, создать новый;
   подъём через `pool.submit(workerFactory.create(...))`.

### requestCancel(sessionId, type)
1. Загружает сессию из БД.
2. Если статус `SAVING` или `CREATED` — переводит в `CANCELLING`.
3. Вызывает `ensureRunning(sessionId, type)` — гарантирует, что воркер проснётся
   и корректно завершится (фаза 6 SessionWorker, KB-HM-WORKER-001).

## Kafka-команды (сервисный топик `historySaver.commands`)

### ServiceCommand (базовый интерфейс)
- `CURRENT_VERSION = 1`; `v()` — версия команды; `createdAt()` — время создания;
  `partitionKey()` — ключ партиционирования (по умолчанию 0);
  `printInfo()` — строковое представление для логов;
  `@JsonTypeInfo` + `@JsonSubTypes` — сериализация по типу.

### StartSessionCommand
Поля: `v`, `sessionType`, `sessionId`, `topic`, `createdAt`;
`partitionKey() = sessionId` — гарантирует упорядоченность команд одной сессии;
`of(sessionId, sessionType, topic)` — фабрика.

### CancelSessionCommand
Поля: `v`, `sessionType`, `sessionId`, `createdAt`; `partitionKey() = sessionId`;
`of(sessionId, sessionType)`.

### CleanupImportedSessionsCommand
Поля: `v`, `createdAt`; глобальная команда (не привязана к сессии);
обрабатывается `CleanupImportedSessionsCommandHandler` (KB-HM-CLEANUP-001).

### ServiceCommandDispatcherImpl
1. Конструктор принимает `List<ServiceCommandHandler>`.
2. Создаёт `Map<Class, Handler>` — каждый тип команды должен иметь ровно
   один хендлер.
3. `handle(command)`: проверка версии команды → поиск хендлера по типу →
   `handler.handle(command)`.

### ServiceCommandListener
1. Подписывается на сервисный топик Kafka.
2. `run(args)`: `DefaultKafkaConsumerFactory`; `ConcurrentKafkaListenerContainerFactory`
   с `setSyncCommits(true)`, `setAckMode(MANUAL_IMMEDIATE)`, `setConcurrency(1)`;
   `ConcurrentMessageListenerContainer`; listener: вызов `onMessage` обёрнут в
   `ExecutorService`, при ошибке — лог и сообщение **не ack-ится**.
3. `onMessage(key, msg)`: парсинг JSON в `ServiceCommand` → `dispatcher.handle(command)`.
4. `shutdown()`: закрывает `ExecutorService`.
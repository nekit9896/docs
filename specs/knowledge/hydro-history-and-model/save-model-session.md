---
id: KB-HM-SAVE-001
title: Сохранение модельной сессии: команды, save_sessions, статусы
service: hydro-history-and-model
group: save
source: confluence/repo_description_hydro-history-and-model#3.4, #3.5.1, «Статусы Сессии» (сохранятельные)
requires: [KB-HM-SESSIONS-001]
related: [KB-HM-WORKER-001, KB-HM-EXEC-001, KB-HM-WATERMARK-001, KB-HM-STORAGE-001]
status: verified
---

# Сохранение модельной сессии

## Приём POST-запроса на сохранение

1. Запрос принимаем в `ModHistController.saveSession()`.
2. Статус Сессии переводим в `SAVING`.
3. Уничтожаем процессы Сессии (Прикладные сессии, Плеерные потоки данных),
   **НО ТОПИКИ KAFKA НЕ УНИЧТОЖАЕМ**.
4. Создание двух Сохранятельных сессий (таблица `save_sessions`):
   - для Сообщений (Алармы) — тип ALARM;
   - для Значений — тип VALUE.
5. Создание команды на старт процесса сохранения в сервисный топик Kafka
   (по умолчанию `historySaver.commands`).
6. Отвечаем Клиенту, что запрос обработан (поставлен в очередь).

## Взятие в работу команды из очереди

1. `ServiceCommandListener.run()` инициирует подписку на сервисный топик Kafka.
2. Обработка сообщений делегируется в `ServiceCommandDispatcherImpl.handle()`.
3. Делегирование хендлеру `StartSessionCommandHandler`
   (`ServiceCommand = StartSessionCommand`) →
   `saver.worker.WorkerExecutorImpl.ensureRunning()` (KB-HM-EXEC-001).

## Процесс сохранения

Отказоустойчивый процесс, связка `WatermarkService` + `WorkerExecutorImpl`:
1. Сверка статуса Сохранятельной сессии.
2. Создание Watermark-записи под Владение этим процессом (KB-HM-WATERMARK-001).
3. Через `ensureRunning()` создаётся/восстанавливается `SessionWorker`
   (детально — KB-HM-WORKER-001):
   - прогресс воркера — таблица `save_session_progress`, детализация на каждую
     партицию топика Kafka;
   - воркер перекладывает данные из модельного топика Kafka в спец-таблицу
     ClickHouse, добавляя в каждую запись принадлежность к `sessionId`;
   - по окончании данных Сохранятельная сессия → `SAVED`.
4. Уведомление `SessionManagerServiceImpl.refreshSessionStatusFromWorker` —
   попытка смены статуса основной Сессии:
   - сверка статусов всех Сохранятельных сессий для `sessionId`;
   - если все `SAVED` — Сессия плеера тоже переводится в `SAVED`.

## Статусы сохранятельной сессии (save_sessions)

| Статус | Описание |
|---|---|
| `CREATED` | Сессия создана, ожидает запуска |
| `SAVING` | Воркер запущен, данные читаются из Kafka |
| `SAVED` | Все данные записаны в ClickHouse |
| `CANCELLING` | Запрошена отмена пользователем |
| `CANCELLED` | Сессия отменена |
| `ERROR` | Ошибка выполнения (timeout, clickhouse error, kafka error) |

Отмена: `WorkerExecutor.requestCancel()` переводит `SAVING`/`CREATED` →
`CANCELLING` (KB-HM-EXEC-001). Коды ошибок воркера — KB-HM-WORKER-001.
---
id: KB-HM-FAULT-001
title: Отказоустойчивость: watermark-recover, isHalted, слежка за прикладными сессиями
service: hydro-history-and-model
group: fault-tolerance
source: confluence/repo_description_hydro-history-and-model#3.2, #3.3 (время), «Ключевые элементы»
requires: [KB-HM-SESSIONS-001, KB-HM-WATERMARK-001]
related: [KB-HM-EXEC-001, KB-HM-CONFIG-001]
status: verified
---

# Отказоустойчивость

## Жизнеспособность Сессии

Отслеживается в связке `WatermarkService` + `ModellingService`.

## В случае, когда жизнь Сессии прервалась

1. `WatermarkService` найдёт и заберёт Владение процессом Сессии
   (recovery по истёкшему lease — KB-HM-WATERMARK-001).
2. Передаст Владение в `ModellingService.recover()`.
3. Делегирует работу в `ModellingService.ensureRunning()` (KB-HM-SESSIONS-001).

## Слежка за наличием Прикладных сессий

Реализована в `ModellingService`:
- По всем активным Сессиям идёт опрос Приложений (каждые
  `tn-scada.history-model.remote-session-check-interval` = **PT10S**,
  KB-HM-CONFIG-001).
- В случае недостатка Прикладных сессий:
  - обработка Сессии приостанавливается (`isHalted = true`);
  - производятся попытки создать Прикладные сессии;
  - когда Прикладные сессии обеспечены — Сессия возобновляется (`isHalted = false`).

Создание-удаление Прикладных сессий — `service/components/RemotesWalker`
(через endpoint `/v1/sessions` приложений, KB-HM-STORAGE-001). Отказ при
инициации/работе: статус `CLOSED`, ресурсы освобождаются, прикладные сессии
уничтожаются (KB-HM-SESSIONS-001).

Для сохранения модельной сессии отказоустойчивость обеспечивают связка
`WatermarkService` + `WorkerExecutorImpl` (KB-HM-SAVE-001, KB-HM-WORKER-001).
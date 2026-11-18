---
id: KB-HM-CLEANUP-001
title: Очистка импортированных сессий (CleanupImportedSessionsCommandHandler)
service: hydro-history-and-model
group: cleanup
source: confluence/repo_description_hydro-history-and-model#3.7, #8.2, «Параметры» (cleanup.*)
requires: [KB-HM-WATERMARK-001, KB-HM-ZIP-001]
related: [KB-HM-CONFIG-001]
status: needs-review
---

# Очистка импортированных сессий

⚠ Фрагмент помечен `needs-review`: направление неравенства в фильтре TTL
(пункт 3) похоже на опечатку источника — см. G11 в
`meta/discrepancies-2026-11-17.md`. Остальное перенесено точно.

## Запуск планировщика

1. `@Scheduled(cron = "${tn-scada.history-model.cleanup.imported-sessions.cron}")`
   запускает `CleanupImportedSessionsCommandHandler.run()`.
2. Параметры (KB-HM-CONFIG-001):

| Параметр | Default (metadata) | Переопределение в yml |
|---|---|---|
| `cron` | `0 0 3 * * *` (3:00 AM ежедневно) | `0 0 0 * * *` |
| `enabled` | `true` | — |
| `lock-at-least-for` | `PT1M` | `PT30S` |
| `lock-at-most-for` | `PT5M` | `PT50S` |
| `soft` | `true` | — |
| `ttl` | `PT72H` | `P7D` |

## Логика очистки

1. Запрашивает у `WatermarkService` владение ресурсом
   `resourceKey = "importedSessionsCleanup"` (KB-HM-WATERMARK-001).
2. Если захват лока не удался — пропускает итерацию.
3. Загружает импортированные сессии из БД: фильтр `source = SourceMode.imported`;
   фильтр по времени **`createdAt + ttl > now`** (⚠ G11: для удаления
   просроченных ожидается `createdAt + ttl < now`).
4. Для каждой сессии:
   - пропускает, если идёт сохранение (`status = SAVING` или `CANCELLING`);
   - если статус терминальный — удаляет: `soft = true` → статус `DELETED`
     (запись остаётся в БД); `soft = false` → полное удаление из БД;
   - удаляет партиции в ClickHouse через `partitionService.dropPartitionIfExists()`.
5. После обработки всех сессий — освобождает лока ватермарка.

Альтернативный запуск: Kafka-команда `CleanupImportedSessionsCommand`
(глобальная, KB-HM-EXEC-001).
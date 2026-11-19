---
id: KB-HM-WATERMARK-001
title: Watermark-сервис: владение асинхронным процессом (lease, epoch, recovery)
service: hydro-history-and-model
group: watermark
source: confluence/repo_description_hydro-history-and-model#6.1, «Параметры» (watermark.*)
requires: []
related: [KB-HM-FAULT-001, KB-HM-WORKER-001, KB-HM-EXEC-001, KB-HM-CLEANUP-001, KB-HM-STORAGE-001]
status: verified
---

# Watermark-сервис

Механика владения асинхронным процессом в конкурентной среде резервных
сущностей приложения (пакет `/watermark/`). Таблица `watermarks`
(service_name, resource_key, state_json, owner_node_id, lease_until, epoch,
created_at, updated_at) + последовательность `watermark_epoch_seq`
(SQL — диалект PostgreSQL, см. G7 в `meta/discrepancies-2026-11-17.md`).

## Захват (WatermarkService.tryAcquire)

1. Сериализует начальное состояние в JSON; `leaseUntil = now + leaseDuration`.
2. `WatermarkRepository.acquire(serviceName, resourceKey, stateJson, nodeId, leaseUntil)`:
   ```sql
   INSERT INTO watermarks (service_name, resource_key, state_json, owner_node_id, lease_until, created_at, updated_at)
   VALUES (?, ?, ?, ?, ?, now(), now())
   ON CONFLICT (service_name, resource_key) DO UPDATE
   SET owner_node_id = excluded.owner_node_id,
       lease_until = excluded.lease_until,
       epoch = CASE
           WHEN watermarks.owner_node_id = excluded.owner_node_id
               AND watermarks.lease_until >= now() THEN watermarks.epoch
           ELSE nextval('watermark_epoch_seq')
       END,
       updated_at = now()
   WHERE watermarks.lease_until < now()
      OR (watermarks.owner_node_id = excluded.owner_node_id
          AND watermarks.lease_until >= now())
   RETURNING ...
   ```
3. Если запись уже существует и принадлежит той же ноде с неистекшим lease —
   обновляет epoch. Возвращает `WatermarkAcquisition(lease, snapshot)`.

## Продление (renew)

`leaseUntil = now + leaseDuration`; `WatermarkRepository.renew`:
```sql
UPDATE watermarks SET lease_until = ?, updated_at = now()
WHERE service_name = ? AND resource_key = ? AND owner_node_id = ?
  AND epoch = ? AND lease_until >= now()
```
`true` если обновлена 1 запись, иначе `false`.

## Сохранение состояния (saveState)

Сериализация состояния в JSON; `WatermarkRepository.saveState` — тот же UPDATE
с добавлением `state_json = ?` и `lease_until = ?` по условиям
owner + epoch + `lease_until >= now()`.

## Освобождение (release)

```sql
DELETE FROM watermarks
WHERE service_name = ? AND resource_key = ? AND owner_node_id = ?
  AND epoch = ? AND lease_until >= now()
```
`true` если удалена 1 запись.

## Поиск истекших (findExpired)

`SELECT ... FROM watermarks WHERE lease_until < ? ORDER BY lease_until ASC`.

## Recovery истекших (WatermarkRecoveryService.recoverExpired)

1. `@Scheduled(fixedDelayString = "${tn-scada.history-model.watermark.recovery-scan-interval}")`.
2. `findExpired(now)`; для каждого истёкшего: найти хендлер по `serviceName`,
   `tryAcquire(serviceName, resourceKey, stateJson)`; захват успешен —
   `handler.recover(lease, snapshot)`; проигрыш гонки — пропуск.

Использование: жизнеспособность Сессии плеера (KB-HM-FAULT-001), владение
процессом сохранения (KB-HM-WORKER-001), очистка импортированных сессий
(KB-HM-CLEANUP-001, resourceKey `importedSessionsCleanup`).

## Параметры

| Параметр | Default | Описание |
|---|---|---|
| `tn-scada.history-model.watermark.lease-duration` | `PT10S` | Длительность итерации владения процессом |
| `tn-scada.history-model.watermark.recovery-scan-interval` | `PT4S` | Интервал поиска процессов с просроченным Владением |
| `tn-scada.history-model.watermark.node-id` | `${HOSTNAME}` (yml: `${WATERMARK_NODE_ID:${HOSTNAME:}}`) | ID сущности приложения; без указания — случайная строка |
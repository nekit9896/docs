---
case_conflu: HY-HIST-013
title: TTL: автозакрытие неактивной
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-013
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SESSIONS-001]
related: [HY-HIST-007, HY-HIST-044]
status: verified
---

# HY-HIST-013 — TTL: автозакрытие неактивной

**Требование:** R-HYDR-057
**Описание:** Сессия PAUSED > TTL → автозакрытие.

**Обоснование:** TTL = 24 ч в проде (`sessionTTL`). В тесте: временно 50 с через
конфиг.

**Предусловие:**

- TTL временно = 50 с _(уточнить механизм: Redis key / actuator / env — чек-лист
  п.14)_
- Сессия PAUSED

**Действия:**

1. `api.createModelling({"targets":["MT1.LU1"]})`
2. `api.start(id)` ⚠️
3. `api.pause(id)` ⚠️
4. `WAIT(55)` — 50 с TTL + 5 с margin
5. `api.get(id)` ⚠️
6. `api.list({status: 11})` ⚠️

**Ожидаемый результат:**

- Шаг 5: `status = 11` (CLOSED) — автоматически
- `closedAt` заполнен
- `closeReason = "TTL_EXCEEDED"` _(допущение 15: формат поля)_

**Примечание:** Механизм изменения TTL в тесте: **уточнить** (Redis / config /
env variable).

**Teardown:** `RESET()` (с возвратом TTL к 24 ч)

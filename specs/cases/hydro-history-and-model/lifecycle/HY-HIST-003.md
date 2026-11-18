---
case_conflu: HY-HIST-003
title: Создание: startTime > targetTime
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-003
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-001, HY-HIST-004]
status: verified
---

# HY-HIST-003 — Создание: startTime > targetTime

**Требование:** R-HYDR-050
**Описание:** Логическая ошибка: startTime позже targetTime. Невозможно
обработать из будущего в прошлое.

**Действия:**

1. `api.createHistorical({"startTime":"2026-11-09T12:00:00Z","targetTime":"2026-11-09T08:00:00Z","speedRatio":2000,"targets":["MT1.LU1"]})`
2. Проверить ответ

**Ожидаемый результат:**

- HTTP 400, `{"error":"startTime must be before targetTime"}`
- `api.list({})` ⚠️ → пустой массив

**Teardown:** `RESET()`

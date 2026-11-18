---
case_conflu: HY-HIST-004
title: Создание: пустой список targets
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-004
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-001, HY-HIST-003]
status: verified
---

# HY-HIST-004 — Создание: пустой список targets

**Требование:** R-HYDR-050
**Описание:** `targets = []` — система не знает, что считать.

**Действия:**

1. `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T12:00:00Z","speedRatio":2000,"targets":[]})`
2. Проверить ответ

**Ожидаемый результат:**

- HTTP 400, `{"error":"targets must contain at least one element"}`

**Teardown:** `RESET()`

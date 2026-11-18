---
case_conflu: HY-CALC-046
title: "Активность сегмента: без группы задвижек"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-046
requires: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-045, HY-CALC-047]
status: verified
---

# HY-CALC-046 — Активность сегмента: без группы задвижек

**Требование:** R-HYDR-039
**Описание:** Сегмент без задвижек (прямой перегон) всегда активен — его нельзя
«закрыть».

**Предусловие:**

- `SGLU2_PARTGRZDV` — пуст (сегмент не привязан к задвижкам)

**Действия:**

1. `hmi.get("MT1.LU1.SGLU2.State.Activity")`

**Ожидаемый результат:**

- `SGLU2_ACTIVITY = true` (всегда, без задвижек)

**Teardown:** `RESET()`
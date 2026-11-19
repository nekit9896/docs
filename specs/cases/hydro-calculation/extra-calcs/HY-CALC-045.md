---
case_conflu: HY-CALC-045
title: "Активность сегмента: группа задвижек"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-045
requires: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-046, HY-CALC-047, HY-CALC-048, HY-CALC-083]
status: verified
---

# HY-CALC-045 — Активность сегмента: группа задвижек

**Требование:** R-HYDR-039, R-HYDR-042
**Описание:** Сегмент активен, если его группа задвижек открыта. Если задвижек
нет — всегда активен.

**Логика (GrzdvStateAlg → SgluPartGrzdvActivityAlg):**

```
GrzdvStateAlg:
  Type 1 (OR): GRZDV_STATUS = 1, если хотя бы одна ZDV_STATUS = 2
  Type 2 (AND): GRZDV_STATUS = 1, только если все ZDV_STATUS = 2
  Без ZDV: GRZDV_STATUS = 1

SgluPartGrzdvActivityAlg:
  PartGRZDV пуст → SGLU_ACTIVITY = true
  GRZDV_STATUS = 1 → SGLU_ACTIVITY = true
  GRZDV_STATUS = 0 → SGLU_ACTIVITY = false
```

> **Важно:** `GRZDV_STATUS` принимает только 0 и 1. `ZDV_STATUS` принимает
> 0 (закрыта), 2 (открыта), 3 (ремонт).

**Обоснование:**

- GRZDV1: Type=1 (OR), содержит ZDV1 и ZDV2
- ZDV1_STATUS = 0, ZDV2_STATUS = 0 → GRZDV_STATUS = 0 → Activity = false
- ZDV1_STATUS = 2, ZDV2_STATUS = 0 → GRZDV_STATUS = 1 (OR) → Activity = true

**Предусловие:**

- `SGLU1_PARTGRZDV = ["GRZDV1"]`
- `GRZDV1_TYPE = 1` (OR)
- `GRZDV1_PART = ["ZDV1", "ZDV2"]`
- `ZDV1_STATUS = 0`, `ZDV2_STATUS = 0`
- `GRZDV1_STATUS = 0`
- `SGLU1_ACTIVITY = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.GRZDV1.ZDV1.Status", 2)` — открыть ZDV1
2. `WAIT(event)` — GrzdvStateAlg → SgluPartGrzdvActivityAlg
3. `hmi.get("MT1.LU1.SGLU1.GRZDV1.Status")`
4. `hmi.get("MT1.LU1.SGLU1.State.Activity")`
5. `hmi.set("MT1.LU1.SGLU1.GRZDV1.ZDV1.Status", 0)` — закрыть ZDV1
6. `WAIT(event)`
7. `hmi.get("MT1.LU1.SGLU1.State.Activity")`

**Ожидаемый результат:**

- Шаг 3: `GRZDV1_STATUS = 1` (OR: хотя бы одна открыта)
- Шаг 4: `SGLU1_ACTIVITY = true`
- Шаг 7: `SGLU1_ACTIVITY = false` (все закрыты)

**Teardown:** `RESET()`
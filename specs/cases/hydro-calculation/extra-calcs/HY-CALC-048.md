---
case_conflu: HY-CALC-048
title: "Состояние группы задвижек: OR и AND"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-048
requires: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-045, HY-CALC-046]
status: verified
---

# HY-CALC-048 — Состояние группы задвижек: OR и AND

**Требование:** R-HYDR-042
**Описание:** Группа задвижек — логическая сущность. Type 1 (OR): открыта если
хотя бы одна открыта. Type 2 (AND): открыта только если все открыты.

**Таблица:**

| Type | ZDV1 | ZDV2 | GRZDV_STATUS |
|---|---|---|---|
| 1 (OR) | 2 (открыта) | 0 (закрыта) | 1 (открыта) |
| 1 (OR) | 0 | 0 | 0 (закрыта) |
| 2 (AND) | 2 | 2 | 1 (открыта) |
| 2 (AND) | 2 | 0 | 0 (закрыта) |
| любой | без ZDV | — | 1 (открыта) |

**Предусловие:**

- `GRZDV1_TYPE = 1` (OR)
- `GRZDV1_PART = ["ZDV1", "ZDV2"]`
- `ZDV1_STATUS = 0`, `ZDV2_STATUS = 0`
- `GRZDV1_STATUS = 0`

**Действия:**

1. `hmi.set("ZDV1.Status", 2)` → OR: одна открыта
2. `WAIT(event)` → проверить GRZDV_STATUS = 1
3. `hmi.set("ZDV2.Status", 2)` → OR: обе открыты
4. `WAIT(event)` → GRZDV_STATUS = 1
5. `hmi.set("ZDV1.Status", 0)` → OR: одна закрыта
6. `WAIT(event)` → GRZDV_STATUS = 1 (вторая открыта)
7. `hmi.set("ZDV2.Status", 0)` → OR: все закрыты
8. `WAIT(event)` → GRZDV_STATUS = 0

**Для AND (Type=2):**

9. `hmi.set("GRZDV1.Type", 2)` — переключить на AND
10. `hmi.set("ZDV1.Status", 2)` → AND: одна открыта
11. `WAIT(event)` → GRZDV_STATUS = 0 (не все открыты)
12. `hmi.set("ZDV2.Status", 2)` → AND: обе открыты
13. `WAIT(event)` → GRZDV_STATUS = 1

**Ожидаемый результат:**

- OR: шаги 2,4,6 → 1; шаг 8 → 0
- AND: шаг 11 → 0; шаг 13 → 1

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-016
title: "Давление ровно на границе диапазона: аларм не генерируется"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-016
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-014, HY-CALC-015]
status: verified
---

# HY-CALC-016 — Давление ровно на границе диапазона: аларм не генерируется

**Требование:** R-HYDR-028
**Описание:** Граничный случай: давление ровно на границе. Условие строгое
(`>` / `<`). Это похоже защита от шума алармов при колебаниях вокруг границы.

**Предусловие:**

- `LU1_CONTROL = 1`
- `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9`
- `KIP1_DISABLE = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.2)` — ровно верхняя
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`
4. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.9)` — ровно нижняя
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_ALMDEVMAXRANGE = false` (5.2 = 5.2, условие `>` не выполнено)
- Шаг 6: `KIP1_ALMDEVMINRANGE = false` (4.9 = 4.9, условие `<` не выполнено)

**Teardown:** `RESET()`
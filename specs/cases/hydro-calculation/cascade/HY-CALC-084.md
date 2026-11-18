---
case_conflu: HY-CALC-084
title: "Каскад: Control=1, все KIP отключены"
service: hydro-calculation
group: cascade
source: confluence/test-plan-hydro-calculation.md#HY-CALC-084
requires: [KB-CALC-ALGO-LU-IND-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-035, HY-CALC-037, HY-CALC-083]
status: verified
---

# HY-CALC-084 — Каскад: Control=1, все KIP отключены

**Требование:** R-HYDR-038, R-HYDR-028
**Описание:** При Control=1 все датчики отключены. `CounterKIP = 0` →
`AlmKIPAllLink = true`. Алармы давления не генерируются (все Disable=true). Нет
противоречия: аларм связи есть, алармов давления нет.

**Предусловие:**

- `LU1_CONTROL = 1` (на контроле)
- `KIP1_PRESSSTATION = 5.0`, `KIP1_PRESSRANGEMAX = 5.2` (зафиксированы)
- `KIP1_PRESS = 5.5` (высоко, но датчик отключён)
- Все 5 KIP: `Disable = true`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", true)` (и все остальные)
2. `WAIT(2c)`
3. `hmi.get("MT1.LU1.State.CounterKIP")`
4. `hmi.get("MT1.LU1.Alm.AlmKIPAllLink")`
5. `hmi.get("MT1.LU1.State.IndicatorLink")`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`
7. `hmi.get("MT1.LU1.Alm.AlmPressDev")`
8. `hmi.get("MT1.LU1.State.IndicatorControl")`

**Ожидаемый результат:**

- Шаг 3: `LU1_COUNTERKIP = 0`
- Шаг 4: `LU1_ALMKIPALLLINK = true`
- Шаг 5: `LU1_INDICATORLINK = 2` (красный)
- Шаг 6: `KIP1_ALMDEVMAXRANGE = false` (Disable=true, не участвует)
- Шаг 7: `LU1_ALMPRESSDEV = false` (нет активных отклонений)
- Шаг 8: `LU1_INDICATORCONTROL = 1` (Norm — нет отклонений) или `0` (зависит от реализации)

**Критерий:** Нет противоречия — аларм связи (IndicatorLink=2) сосуществует с
отсутствием алармов давления. Диспетчер видит: «нет связи, но и нет аварийного
давления».

**Teardown:** `RESET()`
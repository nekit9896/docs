---
case_conflu: HY-CALC-076
title: "KIP_HEADSTATION: фиксация базового напора"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-076
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-005, HY-CALC-062]
status: verified
---

# HY-CALC-076 — KIP_HEADSTATION: фиксация базового напора

**Требование:** R-HYDR-022
**Описание:** При постановке на контроль (`Control=1`) фиксируется
`KIP_HEADSTATION` — базовый напор. Он используется для расчёта `HeadDelta`.
При снятии с контроля → `invalid`.

**Предусловие:**

- `LU1_CONTROL = 0`
- `KIP1_PRESS = 5.0`, `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`
- `KIP1_HEAD = 663.2` (рассчитан)

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetControlOn", true)`
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadStation")`
4. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)` — изменить давление
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadStation")` — не должно измениться
7. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadDelta")` — должно быть ≠ 0
8. `hmi.set("MT1.LU1.TU.SetControlOff", true)`
9. `WAIT(event)`
10. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadStation")` — invalid

**Ожидаемый результат:**

- Шаг 3: `KIP1_HEADSTATION = 663.2` м (зафиксировано)
- Шаг 6: `KIP1_HEADSTATION = 663.2` м (не обновляется при изменении Press)
- Шаг 7: `KIP1_HEADDELTA = 36.1` м (699.3 − 663.2)
- Шаг 10: `KIP1_HEADSTATION.invalid = true`

**Teardown:** `RESET()`
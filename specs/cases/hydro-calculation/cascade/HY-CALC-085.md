---
case_conflu: HY-CALC-085
title: "Каскад: SGLU_CONTROLON=false → KipPressRangeAlg vs KipAlmDevRangeMaxMinAlg"
service: hydro-calculation
group: cascade
source: confluence/test-plan-hydro-calculation.md#HY-CALC-085
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-073, HY-CALC-014, HY-CALC-083]
status: verified
---

# HY-CALC-085 — Каскад: SGLU_CONTROLON=false → KipPressRangeAlg vs KipAlmDevRangeMaxMinAlg

**Требование:** R-HYDR-028
**Описание:** `KipPressRangeAlg` требует `SGLU_CONTROLON=true`.
`KipAlmDevRangeMaxMinAlg` — требует только `Control=1 AND Disable=0`. При
`SGLU_CONTROLON=false`: `AlmDevMaxRange` может быть true, но `PressRangeAlarm` —
false.

**Предусловие:**

- `LU1_CONTROL = 1`
- `SGLU1_CONTROLON = false`
- `KIP1_DISABLE = false`
- `KIP1_PRESSSTATION = 5.0`, `KIP1_PRESSRANGEMAX = 5.2`
- `KIP1_PRESS = 5.5` (выше границы)

**Действия:**

1. `WAIT(event)`
2. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`
4. `hmi.set("MT1.LU1.SGLU1.State.ControlOn", true)`
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`
7. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`

**Ожидаемый результат:**

- Шаг 2: `KIP1_ALMDEVMAXRANGE = true` (5.5 > 5.2, Control=1, Disable=false)
- Шаг 3: `KIP1_PRESSRANGEALARM = false` (SGLU_CONTROLON=false → #9 не срабатывает)
- Шаг 6: `KIP1_ALMDEVMAXRANGE = true`
- Шаг 7: `KIP1_PRESSRANGEALARM = true` (SGLU_CONTROLON=true → #9 срабатывает)

**Обоснование:** Два разных аларма с разными условиями. `AlmDevMaxRange` —
«давление выше границы», `PressRangeAlarm` — «давление вне диапазона на
контролируемом сегменте».

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-073
title: "Комбинированный аларм диапазона (KipPressRangeAlg)"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-073
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-014, HY-CALC-015, HY-CALC-085]
status: verified
---

# HY-CALC-073 — Комбинированный аларм диапазона (KipPressRangeAlg)

**Требование:** R-HYDR-028
**Описание:** `KipPressRangeAlg` (#9) генерирует комбинированный флаг
`KIP_PRESSRANGEALARM` — `true` если давление вне диапазона (с любой стороны).
В отличие от `KipAlmDevRangeMaxMinAlg` (#5), требует дополнительно
`SGLU_CONTROLON = true`.

**Формула:**

```
Если (Control=1 AND Disable=0 AND SGLU_CONTROLON=true)
AND (Press > PressRangeMax OR Press < PressRangeMin)
→ KIP_PRESSRANGEALARM = true
```

**Предусловие:**

- `LU1_CONTROL = 1`
- `SGLU1_CONTROLON = true`
- `KIP1_DISABLE = false`
- `KIP1_PRESSSTATION = 5.0`, `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9`
- `KIP1_PRESSRANGEALARM = false`

**Действия (часть 1: штатное срабатывание):**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)` — выше границы
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`
4. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.8)` — ниже границы
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`
7. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — вернуть
8. `WAIT(event)`
9. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`

**Действия (часть 2: SGLU_CONTROLON=false → аларм не генерируется):**

1. `hmi.set("MT1.LU1.SGLU1.State.ControlOn", false)`
2. `WAIT(event)`
3. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)`
4. `WAIT(event)`
5. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`
6. `hmi.set("MT1.LU1.SGLU1.State.ControlOn", true)` — восстановить

**Ожидаемый результат:**

- Шаг 3: `KIP1_PRESSRANGEALARM = true` (5.3 > 5.2)
- Шаг 6: `KIP1_PRESSRANGEALARM = true` (4.8 < 4.9)
- Шаг 9: `KIP1_PRESSRANGEALARM = false` (5.0 в диапазоне)
- Шаг 14: `KIP1_PRESSRANGEALARM = false` (SGLU_CONTROLON=false, хотя Press вне диапазона)

**Teardown:** `RESET()`
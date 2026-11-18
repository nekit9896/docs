---
case_conflu: HY-CALC-035
title: "Потеря связи со всеми датчиками"
service: hydro-calculation
group: link-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-035
requires: [KB-CALC-ALGO-LU-IND-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-036, HY-CALC-037, HY-CALC-040]
status: verified
---

# HY-CALC-035 — Потеря связи со всеми датчиками

**Требование:** R-HYDR-038, R-HYDR-020
**Описание:** Все датчики теряют связь → `CounterKIP = 0` → аларм `AlmKIPAllLink`,
индикатор связи = 2.

> **Важно:** `LuCounterKipAlg` считает датчики по **валидности** `KIP_PRESS`
> (не invalid, не NaN, не Infinity). «Потеря связи» = `KIP_PRESS.invalid = true`.

**Предусловие:**

- 5 KIP на ТУ1: KIP1–KIP5, все `Press` валидны
- `LU1_COUNTERKIP = 5`
- `LU1_LIMITKIP = 3` (из ИМ)
- `LU1_INDICATORLINK = 0`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=true)`
2. `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.0, invalid=true)`
3. `hmi.set("MT1.LU1.SGLU1.KIP3.TI.Press", 5.0, invalid=true)`
4. `hmi.set("MT1.LU1.SGLU2.KIP4.TI.Press", 5.0, invalid=true)`
5. `hmi.set("MT1.LU1.SGLU2.KIP5.TI.Press", 5.0, invalid=true)`
6. `WAIT(2c)` — LuCounterKipAlg (каждые 2 с)
7. `hmi.get("MT1.LU1.State.CounterKIP")`
8. `hmi.get("MT1.LU1.Alm.AlmKIPAllLink")`
9. `hmi.get("MT1.LU1.State.IndicatorLink")`
10. Восстановить все: `invalid=false` для всех 5
11. `WAIT(2c)`
12. `hmi.get("MT1.LU1.State.CounterKIP")`
13. `hmi.get("MT1.LU1.State.IndicatorLink")`

**Ожидаемый результат:**

- Шаг 7: `LU1_COUNTERKIP = 0`
- Шаг 8: `LU1_ALMKIPALLLINK = true`
- Шаг 9: `LU1_INDICATORLINK = 2` (красный)
- Алармы давления не генерируются (нет валидных данных)
- Шаг 12: `LU1_COUNTERKIP = 5`
- Шаг 13: `LU1_INDICATORLINK = 0` (норма)

**Teardown:** `RESET()`
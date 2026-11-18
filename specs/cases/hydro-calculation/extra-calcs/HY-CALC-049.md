---
case_conflu: HY-CALC-049
title: "Трассировка: включение и накопление"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-049
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-050, HY-CALC-066]
status: verified
---

# HY-CALC-049 — Трассировка: включение и накопление

**Требование:** R-HYDR-027
**Описание:** По команде `TracesOn` система накапливает историю параметров в
оперативном буфере. Каждые `TraceInterval` записывается пара `[value, timestamp]`.

**Предусловие:**

- `LU1_TRACEINTERVAL = 10` с (из ИМ)
- `LU1_TRACETTL = 60` с (из ИМ)
- `LU1_TRACESAVE = false`
- `LU1_TU_TRACESON = false`
- `KIP1_PRESS = 5.0` (стабилен)

**Действия:**

1. `hmi.set("MT1.LU1.TU.TracesOn", true)`
2. `WAIT(1c)` — LuTracingAlg (event-driven на команду)
3. `WAIT(10c)` — первая итерация трассировки
4. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")`
5. `WAIT(10c)` — вторая итерация
6. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")`
7. `hmi.set("MT1.LU1.TU.TracesOff", true)`
8. `WAIT(event)`
9. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")`

**Ожидаемый результат:**

- Шаг 4: `KIP1_TRACESPRESS = [[5.0, ts1]]` (одна запись)
- Шаг 6: `KIP1_TRACESPRESS = [[5.0, ts1], [5.0, ts2]]` (две записи)
- Шаг 9: `KIP1_TRACESPRESS = []` (очищен при TracesOff)

**Teardown:** `RESET()`
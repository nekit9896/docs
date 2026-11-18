---
case_conflu: HY-CALC-066
title: "Расширение: трассировка — TracesSave=true и TracesOff"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-066
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-049, HY-CALC-050]
status: verified
---

# HY-CALC-066 — Расширение: трассировка — TracesSave=true и TracesOff

**Требование:** R-HYDR-027
**Описание:** Дополнительные проверки трассировки:

1. При `TracesSave = true` — записи старше TTL **не удаляются**
2. При `TracesOff = true` — массивы очищаются, флаг сбрасывается

**Предусловие:**

- `LU1_TRACEINTERVAL = 10` с
- `LU1_TRACETTL = 60` с
- `LU1_TRACESON = true` (активна)
- `KIP1_PRESS = 5.0` (стабилен)

**Действия (часть 1: TracesSave=true):**

1. `hmi.set("MT1.LU1.State.TracesSave", true)`
2. Накопить 90 с (9 итераций)
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")` — проверить длину

**Действия (часть 2: TracesOff):**

4. `hmi.set("MT1.LU1.TU.TracesOff", true)`
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")` — пуст
7. `hmi.get("MT1.LU1.TU.TracesOff")` — сброшен

**Ожидаемый результат:**

- Шаг 3: В массиве **9 записей** (90с / 10с), несмотря на TTL = 60с (TracesSave=true → ничего не удаляется)
- Шаг 6: `KIP1_TRACESPRESS = []` (очищен)
- Шаг 7: `LU1_TU_TRACESOFF = false` (сброшен)

**Teardown:** `RESET()`
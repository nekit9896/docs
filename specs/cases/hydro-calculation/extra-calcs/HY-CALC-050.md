---
case_conflu: HY-CALC-050
title: "Трассировка: TTL и сохранение"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-050
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-049, HY-CALC-066]
status: verified
---

# HY-CALC-050 — Трассировка: TTL и сохранение

**Требование:** R-HYDR-027
**Описание:** При `TracesSave = false`: записи старше TTL удаляются. При
`TracesSave = true`: вся история сохраняется.

**Предусловие:**

- `LU1_TRACESAVE = false`
- `LU1_TRACETTL = 60` с
- `LU1_TRACEINTERVAL = 10` с
- Трассировка активна (`TracesOn = true`)

**Действия:**

1. Включить трассировку
2. Накопить 90 с (9 итераций по 10 с)
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")` — проверить TTL
4. `hmi.set("MT1.LU1.State.TracesSave", true)` — включить сохранение
5. Ещё 90 с
6. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")` — проверить, что всё сохранено

**Ожидаемый результат:**

- Шаг 3: В массиве ~6 записей (90с / 10с = 9, минус старше 60с = 3 удалены → 6 осталось)
- Шаг 6: В массиве ~18 записей (9 + 9, ничего не удалено, TracesSave=true)

**Teardown:** `RESET()`
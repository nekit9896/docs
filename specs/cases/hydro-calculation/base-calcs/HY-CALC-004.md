---
case_conflu: HY-CALC-004
title: Расчётный напор: невалидное давление
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-004
requires: [KB-CALC-FORMULA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-001, HY-CALC-040, HY-CALC-041]
status: verified
---

# HY-CALC-004 — Расчётный напор: невалидное давление

**Требование:** R-HYDR-001
**Описание:** Давление от СДКУ помечено `invalid = true`. Невалидные данные не
должны порождать расчётные значения — это может привести к ложным алармам.
Расчётный движок обязан пометить результат `invalid = true`.

**Обоснование:** Проверяем, что цепочка invalid распространяется:
Press.invalid → Head.invalid. Без валидного напора невозможны проверки несущей
и самотеков.

**Предусловие:**

- `KIP1_HEIGHT = 63.5 м`, `KIP1_RO = 850`, `KIP1_MANUAL = false`
- До теста — штатная работа: `KIP1_HEAD = 663.2 м`, `invalid = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=true)` — записать невалидное давление
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")`

**Ожидаемый результат:**

- `KIP1_HEAD.invalid = true` (или тег отсутствует)
- Числовое значение `KIP1_HEAD` не имеет значения (не используется)
- Алармы по невалидным данным не генерируются

**Teardown:** `RESET()`
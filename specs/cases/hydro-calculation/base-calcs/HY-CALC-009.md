---
case_conflu: HY-CALC-009
title: Повторная постановка на контроль: базовое состояние не обнуляется
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-009
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-005, HY-CALC-007]
status: verified
---

# HY-CALC-009 — Повторная постановка на контроль: базовое состояние не обнуляется

**Требование:** R-HYDR-022
**Описание:** Повторная команда `SetControlOn` при уже активном контроле (Control=1)
не перефиксирует базовое состояние. Иначе все алармы сработали бы заново, а старые
отклонения «исчезли» — ложная стабилизация.

**Предусловие:**

- `LU1_CONTROL = 1`
- `KIP1_PRESSSTATION = 5.0` (зафиксировано давно)
- `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9`
- `LU1_TU_SETCONTROLON = false`

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetControlOn", true)` — повторная команда
2. `WAIT(event)`
3. Проверить теги

**Ожидаемый результат:**

- `KIP1_PRESSSTATION` остаётся 5.0 (не перефиксируется)
- `LU1_CONTROL` остаётся 1
- `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9` (не изменяются)
- `LU1_GRAVITYSEGSREG` **не перефиксируется** (остаётся как было при первой постановке) — если бы перефиксировался, потерялась бы информация о самотеках на момент первой постановки
- `SGLU1_CONTROLON` остаётся `true` (не сбрасывается) — если бы сбрасывался, `KipPressRangeAlg` перестал бы срабатывать на этом сегменте
- `LU1_TU_SETCONTROLON → false` (сброшен)

**Teardown:** `RESET()`
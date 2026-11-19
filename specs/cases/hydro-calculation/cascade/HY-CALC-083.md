---
case_conflu: HY-CALC-083
title: "Каскад: SGLU Activity=false → влияние на датчики"
service: hydro-calculation
group: cascade
source: confluence/test-plan-hydro-calculation.md#HY-CALC-083
requires: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-ALGO-LU-IND-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-045, HY-CALC-047, HY-CALC-061, HY-CALC-084]
status: needs-review
---

# HY-CALC-083 — Каскад: SGLU Activity=false → влияние на датчики

> `needs-review`: критический вопрос источника — `CounterKIP` считает по
> `KIP_PRESS.invalid` или по `KIP_VISIBLE`? Зафиксировать фактическое поведение.

**Требование:** R-HYDR-039, R-HYDR-041
**Описание:** Когда группа задвижек закрыта (GRZDV_STATUS=0) →
SGLU_ACTIVITY=false → SGLU_VISIBLE=false (если Priority=1, ControlOn=false) →
KIP_VISIBLE=false. Проверяем полный каскад.

**Предусловие:**

- `SGLU1_PARTGRZDV = ["GRZDV1"]`
- `GRZDV1_TYPE = 1` (OR), `GRZDV1_PART = ["ZDV1"]`
- `ZDV1_STATUS = 0` (закрыта) → `GRZDV1_STATUS = 0` → `SGLU1_ACTIVITY = false`
- `SGLU1_PRIORITY = 1`, `SGLU1_CONTROLON = false`
- `SGLU1_VISIBLE = false` (Priority=1, ControlOn=false, Activity=false)
- `KIP1_DISABLE = false`
- `KIP1_VISIBLE = false` (SGLU невидим)
- `KIP1_PRESS = 5.0` (приходит, валидный)
- `LU1_CONTROL = 1`

**Действия (часть 1: проверка каскада при закрытии):**

1. `hmi.set("MT1.LU1.SGLU1.GRZDV1.ZDV1.Status", 0)` — закрыть (если не закрыта)
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.GRZDV1.Status")` → 0
4. `hmi.get("MT1.LU1.SGLU1.State.Activity")` → false
5. `hmi.get("MT1.LU1.SGLU1.State.Visible")` → false
6. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")` → false
7. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")` — нет (SGLU_CONTROLON может быть false)
8. `hmi.get("MT1.LU1.State.CounterKIP")` — **проверить**: считает ли KIP1 (Press валидный, но Visible=false)

**Действия (часть 2: проверка при открытии):**

1. `hmi.set("MT1.LU1.SGLU1.GRZDV1.ZDV1.Status", 2)` — открыть
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.State.Activity")` → true
4. `hmi.get("MT1.LU1.SGLU1.State.Visible")` → true
5. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")` → true
6. `hmi.get("MT1.LU1.State.CounterKIP")` — KIP1 учитывается

**Ожидаемый результат:**

- Шаг 4: `SGLU1_ACTIVITY = false`
- Шаг 5: `SGLU1_VISIBLE = false` (Priority=1, ControlOn=false, Activity=false → по формуле: (false AND true) OR (false AND 1) = false)
- Шаг 6: `KIP1_VISIBLE = false` (SGLU невидим)
- Шаг 8: `LU1_COUNTERKIP` — **зафиксировать фактическое поведение**. Ожидание: KIP1 считается (т.к. Press валидный, CounterKIP считает по invalid, а не по Visible)
- Шаг 11: `SGLU1_ACTIVITY = true`
- Шаг 12: `SGLU1_VISIBLE = true` (Priority=1, ControlOn=false, Activity=true → (false AND true) = true)
- Шаг 13: `KIP1_VISIBLE = true`
- Шаг 14: `LU1_COUNTERKIP` увеличен на 1 (KIP1 учтён)

**Критический вопрос (зафиксировать):** `CounterKIP` считает по
`KIP_PRESS.invalid` или по `KIP_VISIBLE`? Если по invalid — датчик «невидимый»
(Visible=false) всё равно учитывается в `CounterKIP`. Это важно для корректности
`IndicatorLink`.

**Teardown:** `RESET()`
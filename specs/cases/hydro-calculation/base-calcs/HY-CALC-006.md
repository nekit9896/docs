---
case_conflu: HY-CALC-006
title: Постановка на контроль: отключённый датчик не участвует
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-006
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-005, HY-CALC-018, HY-CALC-041]
status: verified
---

# HY-CALC-006 — Постановка на контроль: отключённый датчик не участвует

**Требование:** R-HYDR-022
**Описание:** Отключённый датчик (`Disable = true`) не участвует в формировании
базового состояния. Его `PressStation` помечается `invalid = true`. Это нужно,
чтобы невалидное давление отключённого датчика не исказило диапазон для остальных.

**Сценарий (обоснование):**

- Датчик A: `Press = 0.0` МПа (отключён, показывает 0 — типично для обрыва сигнала)
- Датчик B: `Press = 5.0` МПа (норма)
- Если бы A участвовал: `PressStation_A = 0.0` → `RangeMax_A = 0.0 + 0.2 = 0.2` → B мгновенно дал бы аларм (5.0 >> 0.2)
- Если A исключён: `PressStation_A = invalid` → B работает штатно (RangeMax_B = 5.2)

**Предусловие:**

- `LU1_CONTROL = 0`
- `KIP_A_DISABLE = true`, `KIP_A_PRESS = 0.0`
- `KIP_B_DISABLE = false`, `KIP_B_PRESS = 5.0`
- `KIP_B_PRESSDELTARANGEMAX = 0.2`, `KIP_B_PRESSDELTARANGEMIN = 0.1`

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetControlOn", true)`
2. `WAIT(event)`
3. Проверить `KIP_A_PRESSSTATION` и `KIP_B_PRESSSTATION`

**Ожидаемый результат:**

- `KIP_A_PRESSSTATION.invalid = true` (отключённый датчик не зафиксирован)
- `KIP_B_PRESSSTATION = 5.0` (зафиксирован штатно)
- `KIP_B_PRESSRANGEMAX = 5.2`, `KIP_B_PRESSRANGEMIN = 4.9`
- Алармы по KIP_B не сгенерированы

**Teardown:** `RESET()`
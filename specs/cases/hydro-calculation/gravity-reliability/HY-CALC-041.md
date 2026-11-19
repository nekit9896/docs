---
case_conflu: HY-CALC-041
title: "Аларм достоверности: отключён, но данные валидны"
service: hydro-calculation
group: gravity-reliability
source: confluence/test-plan-hydro-calculation.md#HY-CALC-041
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-006, HY-CALC-018, HY-CALC-040]
status: verified
---

# HY-CALC-041 — Аларм достоверности: отключён, но данные валидны

**Требование:** R-HYDR-043
**Описание:** Датчик отключён (`Disable = true`), но данные всё ещё приходят и
помечены валидными (`invalid = false`). Противоречие — ошибка конфигурации или
оператор забыл остановить поток. `AlmFailOn = true`.

**Предусловие:**

- `KIP1_DISABLE = true` (отключён)
- `KIP1_PRESS = 5.0` (приходит, валидный)
- `KIP1_ALMFAILON = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", true)` — отключить
2. `WAIT(event)` — KipAlarmsAlg
3. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`
4. `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", false)` — восстановить
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_ALMFAILON = true` (Disable=true, invalid=false → противоречие)
- Шаг 6: `KIP1_ALMFAILON = false` (сброшен)

**Teardown:** `RESET()`
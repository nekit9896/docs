---
case_conflu: HY-CALC-040
title: "Аларм достоверности: пропал сигнал (invalid)"
service: hydro-calculation
group: gravity-reliability
source: confluence/test-plan-hydro-calculation.md#HY-CALC-040
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-004, HY-CALC-018, HY-CALC-041]
status: verified
---

# HY-CALC-040 — Аларм достоверности: пропал сигнал (invalid)

**Требование:** R-HYDR-043
**Описание:** Датчик выдаёт невалидные данные (`invalid = true`) при
`Disable = false` — сигнал пропал. `KipAlarmsAlg` генерирует `AlmFailOn`.
Невалидные данные не используются для расчёта напора и алармов давления.

**Предусловие:**

- `KIP1_DISABLE = false`
- `KIP1_PRESS = 5.0` (валидный)
- `KIP1_ALMFAILON = false`
- `KIP1_HEAD = 663.2` (рассчитан)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=true)` — пропал сигнал
2. `WAIT(event)` — KipAlarmsAlg
3. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`
4. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` — проверить invalid
5. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=false)` — восстановить
6. `WAIT(event)`
7. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_ALMFAILON = true` (Disable=false, invalid=true → сигнал пропал)
- Шаг 4: `KIP1_HEAD.invalid = true` (напор не рассчитывается по невалидным данным)
- Шаг 7: `KIP1_ALMFAILON = false` (сброшен при восстановлении)

**Teardown:** `RESET()`
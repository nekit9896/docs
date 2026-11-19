---
case_conflu: HY-CALC-031
title: "Снятие режима автопостановки"
service: hydro-calculation
group: stationarity
source: confluence/test-plan-hydro-calculation.md#HY-CALC-031
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-028, HY-CALC-029, HY-CALC-007]
status: verified
---

# HY-CALC-031 — Снятие режима автопостановки

**Требование:** R-HYDR-025
**Описание:** Полное отключение автопостановки. Таймер сбрасывается, флаг
снимается. Control не изменяется.

**Предусловие:**

- `LU1_AUTOCONTROLON = true`
- `LU1_CONTROLAUTOTIMELEFT = 50` (идёт отсчёт)
- `LU1_CONTROL = 0`

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetAutoControlOff", true)`
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.State.AutoControlOn")`
4. `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`
5. `hmi.get("MT1.LU1.State.Control")`

**Ожидаемый результат:**

- `LU1_AUTOCONTROLON = false`
- `LU1_CONTROLAUTOTIMELEFT = −1`
- `LU1_CONTROL = 0` (без изменений)
- `LU1_TU_SETAUTOCONTROLOFF = false` (сброшен)

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-029
title: "Отмена автопостановки"
service: hydro-calculation
group: stationarity
source: confluence/test-plan-hydro-calculation.md#HY-CALC-029
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-028, HY-CALC-030, HY-CALC-031]
status: verified
---

# HY-CALC-029 — Отмена автопостановки

**Требование:** R-HYDR-025
**Описание:** Диспетчер отменяет автопостановку во время отсчёта. TimeLeft = −2.
При следующем Station=true → −1 (не выполняется).

**Предусловие:**

- `LU1_AUTOCONTROLON = true`
- `LU1_CONTROLAUTOTIMELEFT = 120` (идёт отсчёт)
- `LU1_STATION = true`

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetAutoControlCancel", true)`
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`
4. `hmi.get("MT1.LU1.TU.SetAutoControlCancel")`

**Ожидаемый результат:**

- `LU1_CONTROLAUTOTIMELEFT = −2` (отменено)
- `LU1_TU_SETAUTOCONTROLCANCEL = false` (сброшен)
- При следующем Station=true → TimeLeft = −1 (автопостановка не выполняется)

**Teardown:** `RESET()`
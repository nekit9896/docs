---
case_conflu: HY-CALC-030
title: "Перезапуск таймера автопостановки [ИСПР] (HYDRO-234)"
service: hydro-calculation
group: stationarity
source: confluence/test-plan-hydro-calculation.md#HY-CALC-030
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-028, HY-CALC-029, HY-CALC-072]
status: verified
---

# HY-CALC-030 — Перезапуск таймера автопостановки [ИСПР]

**Требование:** R-HYDR-025 (HYDRO-234)
**Описание:** Диспетчер сбрасывает таймер — система получает дополнительное
время на стабилизацию.

**Предусловие:**

- `LU1_AUTOCONTROLON = true`
- `LU1_CONTROLAUTOTIMELEFT = 100` (осталось 100 с)
- `LU1_CONTROLAUTOTIMEOUT = 180`

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetAutoControlReset", true)`
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`

**Ожидаемый результат:**

- `LU1_CONTROLAUTOTIMELEFT = 180` (полный сброс, отсчёт заново)
- `LU1_TU_SETAUTOCONTROLRESET = false` (сброшен)

**Teardown:** `RESET()`
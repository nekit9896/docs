---
case_conflu: HY-CALC-027
title: "LU нестационарен: слишком много скачущих"
service: hydro-calculation
group: stationarity
source: confluence/test-plan-hydro-calculation.md#HY-CALC-027
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-026, HY-CALC-071, HY-CALC-072]
status: verified
---

# HY-CALC-027 — LU нестационарен: слишком много скачущих

**Требование:** R-HYDR-017
**Описание:** Нестационарных ≥ `CountKIPNoStation` → ТУ достоверно нестационарен.
Автопостановка блокируется.

**Обоснование:**

- 5 KIP: 3 нестационарны (KIP_A, B, C), 2 стационарны (D, E)
- `CountKIPNoStation = 2`
- 3 ≥ 2 → false
- Если `ControlAutoTimeLeft > 0` → сбрасывается на −1

**Предусловие:**

- `KIP_A_STATION = false`, `KIP_B_STATION = false`, `KIP_C_STATION = false`
- `KIP_D_STATION = true`, `KIP_E_STATION = true`
- `LU1_COUNTKIPNOSTATION = 2`

**Действия:**

1. Симулировать: на KIP_A/B/C `Press` прыгает ±0.6 МПа (превышает DevMaxStation = 0.5)
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.State.Station")`
4. `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")` — если автопостановка была активна

**Ожидаемый результат:**

- `LU1_STATION = false` (3 нестационарных ≥ 2)
- Если `ControlAutoTimeLeft` было > 0 → теперь `−1`

**Teardown:** `RESET()`
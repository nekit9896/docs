---
case_conflu: HY-CALC-025
title: "KIP нестационарен при невалидных данных"
service: hydro-calculation
group: stationarity
source: confluence/test-plan-hydro-calculation.md#HY-CALC-025
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-023, HY-CALC-024, HY-CALC-004]
status: verified
---

# HY-CALC-025 — KIP нестационарен при невалидных данных

**Требование:** R-HYDR-016
**Описание:** `invalid = true` → датчик автоматически нестационарен. При
восстановлении — Station=false сохраняется, нужен новый период стабильности.

**Предусловие:**

- `KIP1_STATION = true` до этого
- Данные были валидны

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=true)`
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")`
4. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=false)` — восстановить
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_STATION = false`
- Шаг 6: `KIP1_STATION = false` (не восстанавливается мгновенно — нужен новый 120-с период)

**Teardown:** `RESET()`
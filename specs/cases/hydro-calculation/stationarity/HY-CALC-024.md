---
case_conflu: HY-CALC-024
title: "KIP выходит из стационарного режима (скачок)"
service: hydro-calculation
group: stationarity
source: confluence/test-plan-hydro-calculation.md#HY-CALC-024
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-023, HY-CALC-025]
status: verified
---

# HY-CALC-024 — KIP выходит из стационарного режима (скачок)

**Требование:** R-HYDR-016
**Описание:** Давление скакнуло и превысило `DevMaxStation` → датчик
нестационарен. Система фиксирует новое эталонное давление
(`PressStationaryMode`), обнуляя счётчик времени.

**Обоснование:**

- `PressStationaryMode = 5.0`, `DevMaxStation = 0.5`
- Скачок: P = 5.7 → `|5.7 − 5.0| = 0.7 > 0.5` → выход из стационарности
- Новый `PressStationaryMode = 5.7`

**Предусловие:**

- `KIP1_STATION = true`
- `KIP1_PRESS = 5.0`, `KIP1_PRESSSTATIONARYMODE = 5.0`
- `KIP1_DEVMAXSTATION = 0.5`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.7)` — скачок
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")`
4. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressStationaryMode")`

**Ожидаемый результат:**

- `KIP1_STATION = false`
- `KIP1_PRESSSTATIONARYMODE = 5.7` (обновлено на новое значение)
- Для восстановления Station=true нужно 120 с стабильности на 5.7

**Teardown:** `RESET()`
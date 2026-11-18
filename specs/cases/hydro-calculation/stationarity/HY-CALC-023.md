---
case_conflu: HY-CALC-023
title: "KIP переходит в стационарный режим"
service: hydro-calculation
group: stationarity
source: confluence/test-plan-hydro-calculation.md#HY-CALC-023
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-024, HY-CALC-025, HY-CALC-026, HY-CALC-071]
status: verified
---

# HY-CALC-023 — KIP переходит в стационарный режим

**Требование:** R-HYDR-016, R-HYDR-017
**Описание:** Датчик считается стационарным, если:

1. `|Press − PressStationaryMode| ≤ DevMaxStation` (давление не скачет)
2. Время с последнего скачка > `TimeIntSetStation` (120 с)

Стационарность — необходимое условие для автопостановки.

**Обоснование:**

- `DevMaxStation = 0.5` МПа (из ИМ) — допустимое отклонение
- `TimeIntSetStation = 120` с (из ИМ) — минимальное время стабильности
- P = 5.0 МПа стабилен ±0.05 → отклонение 0.05 < 0.5 → условие 1 выполнено
- После 120 с стабильности → условие 2 выполнено → Station = true

**Предусловие:**

- `KIP1_PRESS = 5.0` МПа (стабилен)
- `KIP1_PRESSSTATIONARYMODE = 5.0`
- `KIP1_STATION = false` (ещё не перешёл)
- `KIP1_DEVMAXSTATION = 0.5` (из ИМ)
- `LU1_TIMEINTSETSTATION = 120` с (из ИМ)

**Действия:**

1. Поддерживать `KIP1_PRESS = 5.0 ± 0.05` в течение 130 секунд (записи каждые 10 с через hmi-backend, имитация потока СДКУ)
2. `WAIT(130c)` — 120 с стабильности + 10 с margin
3. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")`

**Ожидаемый результат:**

- `KIP1_STATION = true`
- `KIP1_PRESSSTATIONARYMODE` остаётся 5.0 (не обновляется, т.к. скачка не было)

**Примечание:** Для ускорения теста можно временно уменьшить `TimeIntSetStation`
до 15 с через Redis (если допустимо изменять ИМ в тестовом стенде). В этом случае
ожидание — 20 с.

**Teardown:** `RESET()`
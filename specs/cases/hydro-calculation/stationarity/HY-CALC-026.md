---
case_conflu: HY-CALC-026
title: "LU стационарен: все датчики стабильны"
service: hydro-calculation
group: stationarity
source: confluence/test-plan-hydro-calculation.md#HY-CALC-026
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-023, HY-CALC-027, HY-CALC-071]
status: verified
---

# HY-CALC-026 — LU стационарен: все датчики стабильны

**Требование:** R-HYDR-017
**Описание:** ТУ стационарен, если нестационарных < `CountKIPNoStation` и
стационарных ≥ `LimitKIP`. Три зоны:

| Зона | Условие | Результат |
|---|---|---|
| Достоверно стационарный | Нестационарных < CountKIPNoStation AND стационарных ≥ LimitKIP | true |
| Достоверно нестационарный | Нестационарных ≥ CountKIPNoStation | false |
| Недостаточно данных | Стационарных < LimitKIP (и нестационарных < порог) | false |

**Обоснование:**

- 5 KIP на ТУ1: все Station=true
- `CountKIPNoStation = 2` (из ИМ): допустимо до 2 нестационарных
- `LimitKIP = 2` (из ИМ): минимум 2 стационарных для уверенности
- Нестационарных = 0 < 2, стационарных = 5 ≥ 2 → true

**Предусловие:**

- Все 5 KIP: `Station = true`
- `LU1_COUNTKIPNOSTATION = 2`
- `LU1_LIMITKIP = 2`
- `LU1_CONTROL = 0`, `LU1_AUTOCONTROLON = false`

**Действия:**

1. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")` — убедиться все true
2. `WAIT(event)` — LuStationAlg
3. `hmi.get("MT1.LU1.State.Station")`

**Ожидаемый результат:**

- `LU1_STATION = true`
- Если бы `AutoControlOn = true` и `Control = 0` → `LU1_CONTROLAUTOTIMELEFT` запустился бы отсчёт

**Teardown:** `RESET()`
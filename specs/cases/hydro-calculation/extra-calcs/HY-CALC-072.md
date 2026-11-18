---
case_conflu: HY-CALC-072
title: "Автопостановка — прерывание во время отсчёта"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-072
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-028, HY-CALC-027, HY-CALC-030]
status: verified
---

# HY-CALC-072 — Автопостановка — прерывание во время отсчёта

**Требование:** R-HYDR-025
**Описание:** HY-CALC-028 проверяет полный цикл. Дополнительно: прерывание
отсчёта при потере стационарности и возобновление после восстановления.

**Логика:**

```
1. AutoControlOn=true, Station=true → TimeLeft = 180 (отсчёт начался)
2. TimeLeft: 180 → 120 (цикл 1)
3. Скачок → Station=false → TimeLeft = −1 (отсчёт прерван)
4. Стабилизация → Station=true → TimeLeft = 180 (отсчёт заново)
```

**Предусловие:**

- `LU1_CONTROL = 0`
- `LU1_AUTOCONTROLON = true`
- `LU1_STATION = true` (все KIP стабильны)
- `LU1_CONTROLAUTOTIMEOUT = 180` с

**Действия:**

1. `WAIT(60c)` — цикл 1
2. `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")` → 180
3. `WAIT(60c)` — цикл 2
4. `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")` → 120
5. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.7)` — скачок (Station → false)
6. `WAIT(event)`
7. `hmi.get("MT1.LU1.State.Station")`
8. `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`
9. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — стабилизация
10. `WAIT(130c)` — 120 с стабильности + 10 с margin
11. `hmi.get("MT1.LU1.State.Station")`
12. `WAIT(60c)` — следующий цикл
13. `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`

**Ожидаемый результат:**

- Шаг 2: `TimeLeft = 180` (отсчёт начался)
- Шаг 4: `TimeLeft = 120` (идёт отсчёт)
- Шаг 7: `Station = false` (скачок 0.7 > DevMaxStation 0.5)
- Шаг 8: `TimeLeft = −1` (отсчёт прерван)
- Шаг 11: `Station = true` (восстановлена стабильность)
- Шаг 13: `TimeLeft = 180` (отсчёт начался **заново**, не продолжается с 120)

**Примечание:** Для ускорения — временно установить `TimeIntSetStation = 15 с` и
`ControlAutoTimeOut = 30 с` через Redis. Тогда: 2 цикла по 60 с → прерывание →
20 с стабильности → 1 цикл → TimeLeft = 0 → Control = 1.

**Teardown:** `RESET()`
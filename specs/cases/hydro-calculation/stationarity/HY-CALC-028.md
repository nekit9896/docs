---
case_conflu: HY-CALC-028
title: "Автопостановка: полный цикл"
service: hydro-calculation
group: stationarity
source: confluence/test-plan-hydro-calculation.md#HY-CALC-028
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-029, HY-CALC-030, HY-CALC-031, HY-CALC-072]
status: verified
---

# HY-CALC-028 — Автопостановка: полный цикл

**Требование:** R-HYDR-025
**Описание:** Полный цикл автопостановки: включение → ожидание стационарности →
отсчёт → автоматическая постановка на контроль.

**Последовательность:**

```
1. SetAutoControlOn = true → AutoControlOn = true
2. LU_STATION = false (нестабильно) → TimeLeft = −1
3. Давления стабилизируются → LU_STATION = true
4. TimeLeft = ControlAutoTimeOut (180 с)
5. Отсчёт: 180 → 179 → ... → 0 (каждый цикл 60с, т.е. 3 цикла)
6. TimeLeft = 0 → LuControlSetAlg → LU_CONTROL = 1
```

**Обоснование:**

- `ControlAutoTimeOut = 180` с (из ИМ)
- LuAutoControlTimeLeftAlg работает по POLL(60с): каждый цикл decrements на 60
- Цикл 1: TimeLeft = 180 → 120
- Цикл 2: TimeLeft = 120 → 60
- Цикл 3: TimeLeft = 60 → 0 → срабатывание
- Итого: ~180–240 секунд от стационарности до постановки

**Предусловие:**

- `LU1_CONTROL = 0`
- `LU1_STATION = false` (сначала нестабильно)
- `LU1_AUTOCONTROLON = false`
- `LU1_CONTROLAUTOTIMEOUT = 180` с

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetAutoControlOn", true)`
2. `WAIT(event)` → проверить `AutoControlOn = true`
3. Убедиться, что все KIP стабильны → `LU1_STATION = true`
4. `WAIT(60c)` → цикл 1: TimeLeft = 180
5. `WAIT(60c)` → цикл 2: TimeLeft = 120
6. `WAIT(60c)` → цикл 3: TimeLeft = 60
7. `WAIT(60c)` → цикл 4: TimeLeft = 0 → срабатывание
8. `hmi.get("MT1.LU1.State.Control")`

**Ожидаемый результат:**

- Шаг 2: `LU1_AUTOCONTROLON = true`
- Шаг 4: `LU1_CONTROLAUTOTIMELEFT = 180` (или 120, зависит от момента)
- Шаг 8: `LU1_CONTROL = 1` (автоматическая постановка)
- `KIP1_PRESSSTATION` зафиксировано

**Примечание:** Для ускорения теста можно временно установить
`ControlAutoTimeOut = 30` с через Redis. Тогда отсчёт: 30 → 0 за 1 цикл (60с).

**Teardown:** `RESET()`
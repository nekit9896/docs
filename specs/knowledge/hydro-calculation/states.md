---
id: KB-CALC-STATE-001
title: Состояния системы (LU_CONTROL, LU_STATION, индикаторы)
service: hydro-calculation
group: states
source: confluence/repo_description_hydro-calculation#«Состояния системы», #10 (LuIndicatorControlAlg, LuIndicatorLinkAlg)
requires: [KB-CALC-MODEL-001]
related: [KB-CALC-ALGO-LU-IND-001, KB-CALC-TAGS-LU-001]
status: verified
---

# Состояния

## Control State (`LU_CONTROL`)

| Значение | Описание |
|---|---|
| 0 | Контроль выключен |
| 1 | Контроль включён |
| 2 | Переход в контроль |

## Station State (`LU_STATION`)

| Значение | Описание |
|---|---|
| true | Стационарный |
| false | Нестационарный |

## Indicator Control State (`LU_INDICATORCONTROL`, enum `IndicatorControlState`)

| Значение | State | Описание |
|---|---|---|
| 0 | ControlOn | Контроль включён |
| 1 | Norm | Нормальный режим |
| 2 | LonesomeKipAlarmed | Аларм на одиночном датчике |
| 3 | RangedKipAlarmed | Аларм на датчике с диапазоном |
| 4 | ControlAutoTimeLeft | Осталось времени до автоматического контроля |
| 5 | TransitionOn | Переход в режим контроля |

## Indicator Link State (`LU_INDICATORLINK`, enum `IndicatorLinkState`)

| Значение | State | Описание |
|---|---|---|
| 0 | Norm | Нормальный режим связи |
| 1 | AlmKipCountLink | Аларм: потеря связи с определённым числом датчиков |
| 2 | AlmKipAllLink | Аларм: потеря связи со всеми датчиками |
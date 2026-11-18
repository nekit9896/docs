---
id: KB-CALC-TAGS-LU-001
title: Теги линейного участка (LU_*)
service: hydro-calculation
group: tags
source: confluence/repo_description_hydro-calculation#11.Structure Layer (LuParameters), #10 (LuDiffQAlg, LuTracingAlg, LuUnifiedAlg)
requires: [KB-CALC-MODEL-001]
related: [KB-CALC-STATE-001, KB-CALC-ALGO-LU-CTRL-001, KB-CALC-ALGO-LU-DATA-001]
status: verified
---

# Теги LU_* (LuStructure и др.)

## Геометрия и профиль
| Тег | Описание |
|---|---|
| `LU_KM` | километровые отметки |
| `LU_HEIGHT` | высоты |
| `LU_CARRIERDEF` | несущая (профиль допустимых давлений) |
| `LU_CARRIER_DATA1`, `LU_CARRIER_DATA2` | данные несущей 1/2 (сырые срезы) |
| `LU_PMAXDEFAULT` | максимальное давление по умолчанию |
| `LU_ARMT_PIPEPRESS` | давление труб |

## Состояния и контроль
| Тег | Описание |
|---|---|
| `LU_CONTROL` | состояние контроля (0/1/2 — см. KB-CALC-STATE-001) |
| `LU_STATION` | стационарность (bool — см. KB-CALC-STATE-001) |
| `LU_CONTROLAUTOTIMELEFT` | время до автоматического контроля |
| `LU_NEWCONTROLTIME` | новое время контроля |
| `LU_SETTIMESHIFT` | флаг установки времени контроля |
| `LU_COUNTKIPNOSTATION` | порог числа нестационарных датчиков |
| `LU_LIMITKIP` | порог числа активных датчиков |
| `LU_INDICATORCONTROL` | индикатор контроля (см. KB-CALC-ALGO-LU-IND-001) |
| `LU_INDICATORLINK` | индикатор связи |

## Самотёки
| Тег | Описание |
|---|---|
| `LU_GRAVITYSEGS` | самотёчные участки |
| `LU_GRAVITYPOSSIBLE` | возможные самотёки |
| `LU_GRAVITYSEGSSCHEDULE` | плановые самотёки |
| `LU_PASSPOINTS` | перевальные точки |
| `LU_PASSPOINTSPOSSIBLE` | возможные перевальные точки |
| `LU_ALMGRAVITY` | аларм самотёка |
| `LU_ALMGRAVITYPOSSIBLE` | аларм возможного самотёка |

## Плотность
| Тег | Описание |
|---|---|
| `LU_RODISTRIB` | распределение плотности |
| `LU_RODISTRIBMANUAL` | ручное распределение плотности |
| `LU_DENSTIME` | время перерасчёта плотности |
| `LU_DENSDEF` | начальная плотность |
| `LU_DENSLIMIT` | предел изменения плотности |

## Связь и алармы
| Тег | Описание |
|---|---|
| `LU_ALMKIPALLLINK` | аларм потери связи со всеми датчиками |
| `LU_ALMKIPCOUNTLINK` | аларм потери связи с числом датчиков |
| `LU_ALMCARRIERONUSER` | аларм изменения несущей пользователем |
| `LU_ALMDEVPRESS` | аларм отклонения давления |
| `LU_ALMDEVRANGE` | аларм диапазона |
| `LU_ALMDEVHEADCARRIER` | аларм отклонения несущей |
| `LU_ALMRATELIMITPRESS` | аларм предела скорости изменения давления |

## Трассировка (LuTracingAlg)
| Тег | Описание |
|---|---|
| `LU_TRACEON` | флаг активной трассировки |
| `LU_TRACESON` / `LU_TRACESOFF` | включить/выключить трассировку |
| `LU_TRACEINTERVAL` | интервал трассировки |
| `LU_TRACETTL` | TTL трассировки |
| `LU_TRACEIGNORETTL` | игнорировать TTL |

## Унифицированные диапазоны (LuUnifiedAlg)
| Тег | Назначение |
|---|---|
| `LU_UNIFIED_PRESSDELTARANGEMAX/MIN` | униф. верхний/нижний предел давления |
| `LU_UNIFIED_QVMOMDELTARANGEMAX/MIN` | униф. пределы расхода |
| `LU_UNIFIED_PRESSDELTASCHEDULERANGEMAX/MIN` | униф. пределы плана |

## План и режимы (PumpingPlanAlg, LuStationAlg и др.)
| Тег | Описание |
|---|---|
| `LU_ARMT_PUMPPLAN` | план перекачки |
| `LU_SCHEDULEREGIMNAME` | название режима |
| `LU_PRESSMANUALLIMIT` | ручные пределы давления |

## Разница расходов (LuDiffQAlg, теги вида `.TI.*` / `.Alm.*`)
| Тег | Описание |
|---|---|
| `.TI.DiffQmom` | моментальный расход разницы |
| `.TI.DiffQavg` | средний расход разницы (за час) |
| `.TI.DiffQavgStation` | средний расход в стационарном режиме |
| `.TI.DiffQmomLimitMin/Max` | пределы моментального |
| `.TI.DiffQavgLimitMin/Max` | пределы среднего |
| `.TI.DiffQavgLimitStationMin/Max` | пределы стационарного |
| `.Alm.AlmDevQmom` | аларм моментального |
| `.Alm.AlmDevQavg` | аларм среднего |
| `.Alm.AlmDevQavgStation` | аларм стационарного |
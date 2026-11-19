---
id: KB-CALC-TAGS-KIP-001
title: Теги датчика давления (KIP_*)
service: hydro-calculation
group: tags
source: confluence/repo_description_hydro-calculation#11.Structure Layer (KipParameters)
requires: [KB-CALC-MODEL-001]
related: [KB-CALC-ALGO-KIP-001, KB-CALC-TAGS-LU-001, KB-CALC-STATE-001]
status: verified
---

# Теги KIP_* (KipStructure)

## Основные измерения
| Тег | Описание |
|---|---|
| `KIP_PRESS` | давление |
| `KIP_HEAD` | напор |
| `KIP_HEIGHT` | высота |
| `KIP_KM` | километр |

## Статусы
| Тег | Описание |
|---|---|
| `KIP_DISABLE` | отключён |
| `KIP_VISIBLE` | видим |
| `KIP_STATION` | стационарен |

## Алармы отклонения
| Тег | Описание |
|---|---|
| `KIP_ALMDEV` | аларм отклонения |
| `KIP_ALMDEVMAX` / `KIP_ALMDEVMIN` | аларм макс/мин отклонения |
| `KIP_ALMDEVMAXRANGE` / `KIP_ALMDEVMINRANGE` | аларм макс/мин диапазона |
| `KIP_ALMDEVMAXRANGEMIN` / `KIP_ALMDEVMAXRANGEMAX` | аларм макс диапазона: мин/макс |
| `KIP_ALMDEVMINRANGEMIN` / `KIP_ALMDEVMINRANGEMAX` | аларм мин диапазона: мин/макс |

## Скорость изменения давления
| Тег | Описание |
|---|---|
| `KIP_PRESSRATE` | скорость изменения давления |
| `KIP_PRESSRATETAG` | тег скорости |
| `KIP_PRESSRATETAGMIN` / `KIP_PRESSRATETAGMAX` | мин/макс скорость |
| `KIP_PRESSRATETAGALARM` | аларм скорости |

## Диапазон давления
| Тег | Описание |
|---|---|
| `KIP_PRESSRANGE` | диапазон давления |
| `KIP_PRESSRANGEMIN` / `KIP_PRESSRANGEMAX` | мин/макс диапазон |
| `KIP_PRESSRANGEALARM` | аларм диапазона |

## Разница напора/давления (попарно, включая «плановые» варианты)
| Тег | Описание |
|---|---|
| `KIP_HEADDELTA` / `KIP_PRESSDELTA` | разница напора / давления |
| `KIP_HEADDELTARANGE` / `KIP_PRESSDELTARANGE` | диапазон разницы |
| `KIP_HEADDELTARANGEMIN/MAX`, `KIP_PRESSDELTARANGEMIN/MAX` | мин/макс диапазона разницы |
| `KIP_HEADDELTASCHEDULERANGE` / `KIP_PRESSDELTASCHEDULERANGE` | диапазон разницы плана |
| `KIP_HEADDELTASCHEDULERANGEMIN/MAX`, `KIP_PRESSDELTASCHEDULERANGEMIN/MAX` | мин/макс планового диапазона |

## Плотность и план
| Тег | Описание |
|---|---|
| `KIP_RO` / `KIP_ROSCHEDULE` | плотность / плановая плотность |
| `KIP_HEADSCHEDULE` / `KIP_PRESSSCHEDULE` | плановый напор / плановое давление |
| `KIP_ARMTID` | ID арматуры |
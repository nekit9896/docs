# Группа pressure-alarms — Алармы давления (§3.4)

Сервис: hydro-calculation. Источник: `confluence/test-plan-hydro-calculation.md` §3.4.
Стенд: KB-CALC-TESTSTAND-001; обозначения и правила: KB-CALC-TESTPLAN-001.

| Кейс | Название | Требование | Статус |
|---|---|---|---|
| [HY-CALC-014](HY-CALC-014.md) | Аларм выхода давления за верхнюю границу | R-HYDR-028 | verified |
| [HY-CALC-015](HY-CALC-015.md) | Аларм выхода давления за нижнюю границу | R-HYDR-028 | verified |
| [HY-CALC-016](HY-CALC-016.md) | Давление ровно на границе диапазона: аларм не генерируется | R-HYDR-028 | verified |
| [HY-CALC-017](HY-CALC-017.md) | Аларм давления не генерируется без контроля (Control = 0) | R-HYDR-028 | verified |
| [HY-CALC-018](HY-CALC-018.md) | Аларм давления не генерируется при отключённом датчике | R-HYDR-028, R-HYDR-043 | verified |
| [HY-CALC-073](HY-CALC-073.md) | Комбинированный аларм диапазона (KipPressRangeAlg) | R-HYDR-028 | verified |
| [HY-CALC-074](HY-CALC-074.md) | Отклонение расхода (UrQVmomDeltaAlg) | R-HYDR-029 | verified |
| [HY-CALC-075](HY-CALC-075.md) | Дебаланс: реакция на 2-секундном цикле | R-HYDR-033 | verified |
| [HY-CALC-076](HY-CALC-076.md) | KIP_HEADSTATION: фиксация базового напора | R-HYDR-022 | verified |
| [HY-CALC-077](HY-CALC-077.md) | KIP_ALMGRAVITYPOSSIBLE: напор близок к высоте в конфигурации | R-HYDR-035 | verified |
| [HY-CALC-078](HY-CALC-078.md) | PLTM_ALMROINVALID: невалидная плотность | R-HYDR-043 | verified |
| [HY-CALC-079](HY-CALC-079.md) | UR_ALMQVMOMINVALID: невалидный расход | R-HYDR-043 | verified |
| [HY-CALC-080](HY-CALC-080.md) | KIP_ROSCHEDULE: плановая плотность | R-HYDR-009 | verified |

Кейсы 073–080 размещены в источнике внутри §3.4, несмотря на нумерацию 07x/08x.
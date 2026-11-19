# Группа base-calcs — Базовые расчёты: напор, несущая, контроль (§3.1)

Сервис: hydro-calculation. Источник: `confluence/test-plan-hydro-calculation.md` §3.1.
Стенд: KB-CALC-TESTSTAND-001; обозначения и правила: KB-CALC-TESTPLAN-001.

| Кейс | Название | Требование | Статус |
|---|---|---|---|
| [HY-CALC-001](HY-CALC-001.md) | Расчётный напор: номинальный режим | R-HYDR-001 | verified |
| [HY-CALC-002](HY-CALC-002.md) | Расчётный напор: ручная корректировка высоты | R-HYDR-001 | verified |
| [HY-CALC-003](HY-CALC-003.md) | Расчётный напор: аномальная плотность | R-HYDR-001 | verified |
| [HY-CALC-004](HY-CALC-004.md) | Расчётный напор: невалидное давление | R-HYDR-001 | verified |
| [HY-CALC-005](HY-CALC-005.md) | Расчёт диапазона давления при постановке на контроль | R-HYDR-022, R-HYDR-006 | verified |
| [HY-CALC-006](HY-CALC-006.md) | Постановка на контроль: отключённый датчик не участвует | R-HYDR-022 | verified |
| [HY-CALC-007](HY-CALC-007.md) | Снятие ТУ с контроля | R-HYDR-023 | verified |
| [HY-CALC-008](HY-CALC-008.md) | Режим контроля перехода (TransitionControlOn) | R-HYDR-024 | needs-review |
| [HY-CALC-009](HY-CALC-009.md) | Повторная постановка на контроль: базовое состояние не обнуляется | R-HYDR-022 | verified |
| [HY-CALC-010](HY-CALC-010.md) | Несущая давления: заводские значения (PmaxDefault) | R-HYDR-004, R-HYDR-003 | verified |
| [HY-CALC-011](HY-CALC-011.md) | Несущая давления: пользователь занижает ограничение | R-HYDR-004, R-HYDR-037 | verified |
| [HY-CALC-012](HY-CALC-012.md) | Несущая давления: пользователь снимает ограничение | R-HYDR-004, R-HYDR-037 | verified |
| [HY-CALC-013](HY-CALC-013.md) | Напор выше несущей: критический аларм AlmDevHeadCarrier | R-HYDR-031, R-HYDR-003 | verified |
| [HY-CALC-081](HY-CALC-081.md) | PressManualLimit: невалидные форматы [НИЗКИЙ ПРИОРИТЕТ] | R-HYDR-004 | needs-review |
| [HY-CALC-082](HY-CALC-082.md) | Фильтрация конфигурации: некорректные массивы | R-HYDR-014 | verified |

Кейсы 081–082 размещены в источнике внутри §3.1 (возле несущей/конфигурации),
несмотря на нумерацию 08x.
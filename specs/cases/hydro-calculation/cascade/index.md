# Группа cascade — Каскадные эффекты (§3.8)

Сервис: hydro-calculation. Источник: `confluence/test-plan-hydro-calculation.md` §3.8.
Стенд: KB-CALC-TESTSTAND-001; обозначения и правила: KB-CALC-TESTPLAN-001.

| Кейс | Название | Требование | Статус |
|---|---|---|---|
| [HY-CALC-083](HY-CALC-083.md) | Каскад: SGLU Activity=false → влияние на датчики | R-HYDR-039, R-HYDR-041 | needs-review |
| [HY-CALC-084](HY-CALC-084.md) | Каскад: Control=1, все KIP отключены | R-HYDR-038, R-HYDR-028 | verified |
| [HY-CALC-085](HY-CALC-085.md) | Каскад: SGLU_CONTROLON=false → KipPressRangeAlg vs KipAlmDevRangeMaxMinAlg | R-HYDR-028 | verified |

Открытый вопрос HY-CALC-083 (см. кейс): считает ли `CounterKIP` по
`KIP_PRESS.invalid` или по `KIP_VISIBLE` — зафиксировать при первом прогоне.
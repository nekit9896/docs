# Группа stationarity — Стационарность и автопостановка (§3.3)

Сервис: hydro-calculation. Источник: `confluence/test-plan-hydro-calculation.md` §3.3.
Стенд: KB-CALC-TESTSTAND-001; обозначения и правила: KB-CALC-TESTPLAN-001.

| Кейс | Название | Требование | Статус |
|---|---|---|---|
| [HY-CALC-023](HY-CALC-023.md) | KIP переходит в стационарный режим | R-HYDR-016, R-HYDR-017 | verified |
| [HY-CALC-024](HY-CALC-024.md) | KIP выходит из стационарного режима (скачок) | R-HYDR-016 | verified |
| [HY-CALC-025](HY-CALC-025.md) | KIP нестационарен при невалидных данных | R-HYDR-016 | verified |
| [HY-CALC-026](HY-CALC-026.md) | LU стационарен: все датчики стабильны | R-HYDR-017 | verified |
| [HY-CALC-027](HY-CALC-027.md) | LU нестационарен: слишком много скачущих | R-HYDR-017 | verified |
| [HY-CALC-028](HY-CALC-028.md) | Автопостановка: полный цикл | R-HYDR-025 | verified |
| [HY-CALC-029](HY-CALC-029.md) | Отмена автопостановки | R-HYDR-025 | verified |
| [HY-CALC-030](HY-CALC-030.md) | Перезапуск таймера автопостановки [ИСПР] (HYDRO-234) | R-HYDR-025 | verified |
| [HY-CALC-031](HY-CALC-031.md) | Снятие режима автопостановки | R-HYDR-025 | verified |

Связанный кейс: HY-CALC-072 (прерывание отсчёта, extra-calcs), HY-CALC-071
(зона «недостаточно данных», extra-calcs).
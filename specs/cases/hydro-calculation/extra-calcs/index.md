# Группа extra-calcs — Дополнительные расчёты (§3.7)

Сервис: hydro-calculation. Источник: `confluence/test-plan-hydro-calculation.md` §3.7.
Стенд: KB-CALC-TESTSTAND-001; обозначения и правила: KB-CALC-TESTPLAN-001.

| Кейс | Название | Требование | Статус |
|---|---|---|---|
| [HY-CALC-042](HY-CALC-042.md) | Скорость изменения давления: алгоритм 1 (двухточечный) | R-HYDR-005 | verified |
| [HY-CALC-043](HY-CALC-043.md) | Скорость изменения давления: алгоритм 2 (МНК) | R-HYDR-005 | verified |
| [HY-CALC-044](HY-CALC-044.md) | Фильтрация конфигурации ТУ: удаление артефактов | R-HYDR-014 | verified |
| [HY-CALC-045](HY-CALC-045.md) | Активность сегмента: группа задвижек | R-HYDR-039, R-HYDR-042 | verified |
| [HY-CALC-046](HY-CALC-046.md) | Активность сегмента: без группы задвижек | R-HYDR-039 | verified |
| [HY-CALC-047](HY-CALC-047.md) | Видимость сегмента | R-HYDR-040 | verified |
| [HY-CALC-048](HY-CALC-048.md) | Состояние группы задвижек: OR и AND | R-HYDR-042 | verified |
| [HY-CALC-049](HY-CALC-049.md) | Трассировка: включение и накопление | R-HYDR-027 | verified |
| [HY-CALC-050](HY-CALC-050.md) | Трассировка: TTL и сохранение | R-HYDR-027 | verified |
| [HY-CALC-051](HY-CALC-051.md) | Распределение плотности: ручное задание | R-HYDR-013 | verified |
| [HY-CALC-052](HY-CALC-052.md) | Распределение плотности: порог формирования партии | R-HYDR-013 | verified |
| [HY-CALC-053](HY-CALC-053.md) | Унификация дельт на все датчики | R-HYDR-026 | verified |
| [HY-CALC-054](HY-CALC-054.md) | Уставка ЦСПА: контроль вне режима контроля | R-HYDR-010, R-HYDR-036 | verified |
| [HY-CALC-055](HY-CALC-055.md) | Высота датчика: расчёт из конфигурации ТУ | R-HYDR-002 | verified |
| [HY-CALC-056](HY-CALC-056.md) | Расчёт диапазона напора (HeadRange) | R-HYDR-007, R-HYDR-032, R-HYDR-008 | verified |
| [HY-CALC-057](HY-CALC-057.md) | Диапазон напора: верхняя граница выше несущей | R-HYDR-032 | verified |
| [HY-CALC-058](HY-CALC-058.md) | Дебаланс: проверка алармов в топике alarm | R-HYDR-033 | verified |
| [HY-CALC-059](HY-CALC-059.md) | Самотеки: проверка алармов в топике alarm | R-HYDR-035 | verified |
| [HY-CALC-060](HY-CALC-060.md) | Статус ремонта: автоматическое отключение/включение | EVOSCADA-21706 | verified |
| [HY-CALC-061](HY-CALC-061.md) | Видимость датчика (KipVisibleAlg) | R-HYDR-041 | verified |
| [HY-CALC-062](HY-CALC-062.md) | Отклонение напора и давления (KipHeadDeltaPressAlg) | R-HYDR-028 | verified |
| [HY-CALC-063](HY-CALC-063.md) | План перекачки (PumpingPlanAlg) | R-HYDR-009 | needs-review |
| [HY-CALC-064](HY-CALC-064.md) | Перенос времени контроля (LuNewControlTimeAlg / FAST) | R-HYDR-046 | needs-review |
| [HY-CALC-065](HY-CALC-065.md) | Расширение: скорость давления — PressRateKiplimit > 1 | R-HYDR-034 | verified |
| [HY-CALC-066](HY-CALC-066.md) | Расширение: трассировка — TracesSave=true и TracesOff | R-HYDR-027 | verified |
| [HY-CALC-067](HY-CALC-067.md) | Расширение: автоматическое распределение плотности | R-HYDR-013 | verified |
| [HY-CALC-068](HY-CALC-068.md) | Расширение: фильтрация конфигурации — все 3 фильтра одновременно | R-HYDR-014 | verified |
| [HY-CALC-069](HY-CALC-069.md) | Расширение: самотёки — плато на конфигурации ТУ | R-HYDR-018 | verified |
| [HY-CALC-070](HY-CALC-070.md) | Расширение: дебаланс — DiffQavg и DiffQavgStation | R-HYDR-033 | verified |
| [HY-CALC-071](HY-CALC-071.md) | Расширение: стационарность LU — зона «недостаточно данных» | R-HYDR-017 | verified |
| [HY-CALC-072](HY-CALC-072.md) | Автопостановка — прерывание во время отсчёта | R-HYDR-025 | verified |
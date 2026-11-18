# Кейсы HY-CALC-* — hydro-calculation (85 кейсов)

Источник: `confluence/test-plan-hydro-calculation.md` (§3.1–3.8).
Стенд: KB-CALC-TESTSTAND-001; обозначения и правила: KB-CALC-TESTPLAN-001.
Формат кейса: `case_conflu` HY-CALC-<NNN> — неизменяем (D30).

## Группы (доменные разделы источника)

| Группа | Раздел | Диапазон | Кол-во | Статусы |
|---|---|---|---|---|
| [base-calcs](base-calcs/index.md) | §3.1 Базовые расчёты: напор, несущая, контроль | 001–013, 081–082 | 15 | 2 needs-review (008, 081) |
| [imbalance](imbalance/index.md) | §3.2 Дебаланс расходов | 019–022 | 4 | verified |
| [stationarity](stationarity/index.md) | §3.3 Стационарность и автопостановка | 023–031 | 9 | verified |
| [pressure-alarms](pressure-alarms/index.md) | §3.4 Алармы давления | 014–018, 073–080 | 13 | verified |
| [link-alarms](link-alarms/index.md) | §3.5 Алармы расхода, связи и индикаторы | 032–037 | 6 | verified |
| [gravity-reliability](gravity-reliability/index.md) | §3.6 Самотёки и достоверность | 038–041 | 4 | verified |
| [extra-calcs](extra-calcs/index.md) | §3.7 Дополнительные расчёты | 042–072 | 31 | 2 needs-review (063, 064) |
| [cascade](cascade/index.md) | §3.8 Каскадные эффекты | 083–085 | 3 | 1 needs-review (083) |

**Итого:** 85 кейсов (001–085, без пропусков); verified — 80, needs-review — 5.

## Примечания

- Нумерация не совпадает с порядком разделов: кейсы 081–082 стоят внутри §3.1,
  073–080 — внутри §3.4 (нумерация источника сохранена без изменений).
- Соответствие «кейс ↔ алгоритм репозитория» — `trace/case-module-matrix.md`.
- Системные обёртки над кейсами алармов: HY-SYS-001…026 (см.
  `../system-tests/alarm-stubs/index.md`).
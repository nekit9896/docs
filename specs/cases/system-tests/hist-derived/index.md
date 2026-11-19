# Группа hist-derived — Системные сценарии из HY-HIST (§3.2)

Сервис: system-tests. Источник: `confluence/test-plan-of-system-tests.md` §3.2.
Стенд: KB-SYS-TESTSTAND-001; обозначения и правила: KB-SYS-TESTPLAN-001.

> Обёртки над кейсами HY-HIST: полное описание — в `../hydro-history-and-model/`
> (§3 тестплана hydro-history-and-model), здесь — системная специфика: щупы
> SPOT_K2 (`model_main_{id}`), SPOT_K4 (`mod-hist-commands`), SPOT_K5
> (`mod-hist-results`) на промежуточных точках. Кейсы зависят от верификации
> псевдо-endpoint'ов mod-hist (G22, блокер P0).

| Кейс | Название | Базовый кейс | SYS | Статус |
|---|---|---|---|---|
| [HY-SYS-027](HY-SYS-027.md) | Запуск: START → hydro-calc подтверждение | HY-HIST-005 | SYS-1 | verified |
| [HY-SYS-028](HY-SYS-028.md) | historical: полный цикл CH → hydro-calc | HY-HIST-014 | SYS-1 | verified |
| [HY-SYS-029](HY-SYS-029.md) | historical: смена скорости | HY-HIST-015 | SYS-1 | verified |
| [HY-SYS-030](HY-SYS-030.md) | historical: замедление 0.25× | HY-HIST-016 | SYS-1 | verified |
| [HY-SYS-031](HY-SYS-031.md) | historical: нет данных в CH | HY-HIST-017 | SYS-1 | needs-review |
| [HY-SYS-032](HY-SYS-032.md) | historical: частичные данные | HY-HIST-018 | SYS-1 | verified |
| [HY-SYS-033](HY-SYS-033.md) | historical: пагинация CH (5000 msg) | HY-HIST-019 | SYS-1 | verified |
| [HY-SYS-034](HY-SYS-034.md) | historical: максимальная скорость | HY-HIST-020 | SYS-1 | needs-review |
| [HY-SYS-035](HY-SYS-035.md) | modelling: advance 1 час | HY-HIST-022 | SYS-1 | verified |
| [HY-SYS-036](HY-SYS-036.md) | modelling: пошаговый advance | HY-HIST-023 | SYS-1 | verified |
| [HY-SYS-037](HY-SYS-037.md) | Импорт XLSX → hydro-calc считает | HY-HIST-026 | SYS-1 | verified |
| [HY-SYS-038](HY-SYS-038.md) | Импорт ZIP_CSV → hydro-calc считает | HY-HIST-027 | SYS-1 | verified |
| [HY-SYS-039](HY-SYS-039.md) | Watermark STALLED → восстановление | HY-HIST-034 | SYS-1 | verified |
| [HY-SYS-040](HY-SYS-040.md) | SESSION_ERROR: hydro-calc не отвечает | HY-HIST-038 | SYS-1 | verified |
| [HY-SYS-041](HY-SYS-041.md) | Retry после ERROR | HY-HIST-039 | SYS-1 | needs-review |
| [HY-SYS-042](HY-SYS-042.md) | Save → Play-model → hydro-calc | HY-HIST-045 | SYS-1 | verified |
| [HY-SYS-043](HY-SYS-043.md) | Timeshift (saved) → hydro-calc | HY-HIST-047 | SYS-1 | verified |
| [HY-SYS-044](HY-SYS-044.md) | Timeshift (imported) → hydro-calc | HY-HIST-048 | SYS-1 | verified |
| [HY-SYS-045](HY-SYS-045.md) | Timeshift: невалидный источник | HY-HIST-049 | SYS-1 | verified |

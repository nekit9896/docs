# Группа new-scenarios — Новые системные сценарии (§3.3)

Сервис: system-tests. Источник: `confluence/test-plan-of-system-tests.md` §3.3.
Стенд: KB-SYS-TESTSTAND-001; обозначения и правила: KB-SYS-TESTPLAN-001.

> Полностью описанные сценарии (кроме HY-SYS-049 — в источнике только примечание,
> G27). Используют псевдо-endpoint'ы mod-hist (⚠️, G22) и REST alarm-service
> (формат уточнить — G28).

| Кейс | Название | SYS | Статус |
|---|---|---|---|
| [HY-SYS-046](HY-SYS-046.md) | E2E: historical с алармом (полный путь) | SYS-2 | needs-review |
| [HY-SYS-047](HY-SYS-047.md) | Параллельные сессии: независимость потоков | SYS-1 | verified |
| [HY-SYS-048](HY-SYS-048.md) | Аларм: полный путь в оперативном режиме | SYS-2 | needs-review |
| [HY-SYS-049](HY-SYS-049.md) | data-manager: изменение уставки → hydro-calc реагирует | — | placeholder |
| [HY-SYS-050](HY-SYS-050.md) | Race condition: pause + advance одновременно | SYS-1 | verified |
| [HY-SYS-051](HY-SYS-051.md) | Моделирование: Press меняется на каждом шаге → напор меняется | SYS-1 | verified |
| [HY-SYS-052](HY-SYS-052.md) | Timeshift: сравнение результатов с исходной сессией | SYS-1 | verified |

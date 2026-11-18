# Кейсы HY-SYS-* — системные тесты (52 кейса)

Источник: `confluence/test-plan-of-system-tests.md` (§3.1–3.3).
Стенд: KB-SYS-TESTSTAND-001; обозначения и правила: KB-SYS-TESTPLAN-001.
Формат кейса: `case_conflu` HY-SYS-<NNN> — неизменяем (D30).

## Группы (доменные разделы источника)

| Группа | Раздел | Диапазон | Кол-во | Статусы |
|---|---|---|---|---|
| [alarm-stubs](alarm-stubs/index.md) | §3.1 Алармные сценарии из HY-CALC | 001–026 | 26 | все placeholder (G28) |
| [hist-derived](hist-derived/index.md) | §3.2 Системные обёртки над HY-HIST | 027–045 | 19 | verified; 3 needs-review (031, 034, 041) |
| [new-scenarios](new-scenarios/index.md) | §3.3 Новые системные сценарии | 046–052 | 7 | 2 needs-review (046, 048), 1 placeholder (049) |

**Итого:** 52 кейса (001–052, без пропусков). Канон по G26: в источнике указано
«53», фактически — 52; HY-HIST-049 из §3.2 числится системным сценарием (HY-SYS-045).

## Примечания

- Заглушки alarm-stubs (001–026) и HY-SYS-049 будут дополнены после получения
  документации alarm-service / alarm-view-service и REST data-manager (G28, G29).
- Щупы промежуточных точек SPOT_K1–K6/SPOT_WS/SPOT_REST: KB-SYS-TESTSTAND-001.
- Соответствие «кейс ↔ модуль репозитория» — `trace/case-module-matrix.md`.
# Группа lifecycle — Управление сессиями: жизненный цикл (§3.1)

Сервис: hydro-history-and-model. Источник: `confluence/test-plan-hydro-history-and-model.md` §3.1.
Стенд: KB-HM-TESTSTAND-001; обозначения и правила: KB-HM-TESTPLAN-001; статусы: KB-HM-SESSIONS-001.

| Кейс | Название | Требование | Статус |
|---|---|---|---|
| [HY-HIST-001](HY-HIST-001.md) | Создание historical-сессии: базовый сценарий | R-HYDR-050, R-HYDR-051 | verified |
| [HY-HIST-002](HY-HIST-002.md) | Создание: валидация speedRatio | R-HYDR-050 | needs-review |
| [HY-HIST-003](HY-HIST-003.md) | Создание: startTime > targetTime | R-HYDR-050 | verified |
| [HY-HIST-004](HY-HIST-004.md) | Создание: пустой список targets | R-HYDR-050 | verified |
| [HY-HIST-005](HY-HIST-005.md) | Запуск: CREATED → OPENING → PLAYING | R-HYDR-051, R-HYDR-052 | verified |
| [HY-HIST-006](HY-HIST-006.md) | Повторный запуск (идемпотентность) | R-HYDR-051 | verified |
| [HY-HIST-007](HY-HIST-007.md) | Пауза: PLAYING → PAUSED | R-HYDR-053 | verified |
| [HY-HIST-008](HY-HIST-008.md) | Возобновление: PAUSED → PLAYING | R-HYDR-053 | verified |
| [HY-HIST-009](HY-HIST-009.md) | Остановка: PLAYING → DONE | R-HYDR-054 | verified |
| [HY-HIST-010](HY-HIST-010.md) | Закрытие: DONE → CLOSING → CLOSED | R-HYDR-055 | verified |
| [HY-HIST-011](HY-HIST-011.md) | Повторное закрытие (идемпотентность) | R-HYDR-055 | verified |
| [HY-HIST-012](HY-HIST-012.md) | Превышение максимума сессий | R-HYDR-056 | verified |
| [HY-HIST-013](HY-HIST-013.md) | TTL: автозакрытие неактивной | R-HYDR-057 | verified |

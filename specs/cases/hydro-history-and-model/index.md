# Кейсы HY-HIST-* — hydro-history-and-model (48 кейсов)

Источник: `confluence/test-plan-hydro-history-and-model.md` (§3.1–3.10).
Стенд: KB-HM-TESTSTAND-001; обозначения и правила: KB-HM-TESTPLAN-001;
статусы сессий: KB-HM-SESSIONS-001.
Формат кейса: `case_conflu` HY-HIST-<NNN> — неизменяем (D30).

## Группы (доменные разделы источника)

| Группа | Раздел | Диапазон | Кол-во |
|---|---|---|---|
| [lifecycle](lifecycle/index.md) | §3.1 Управление сессиями: жизненный цикл | 001–013 | 13 |
| [historical](historical/index.md) | §3.2 Исторические сессии (REAL_TIME/история) | 014–020 | 7 |
| [modelling](modelling/index.md) | §3.3 Моделирование (SIMULATION) | 021–025 | 5 |
| [import](import/index.md) | §3.4 Импорт данных | 026–029 | 4 |
| [export](export/index.md) | §3.5 Экспорт данных | 030–032 | 3 |
| [watermark-progress](watermark-progress/index.md) | §3.6 Watermark и прогресс | 033–036 | 4 |
| [fault-tolerance](fault-tolerance/index.md) | §3.7 Отказоустойчивость | 037–039 | 3 |
| [config-edge-cases](config-edge-cases/index.md) | §3.8 Конфигурация и граничные | 040–044 | 4 |
| [save-play](save-play/index.md) | §3.9 Сохранение и воспроизведение | 045–046 | 2 |
| [timeshift](timeshift/index.md) | §3.10 Перенос времени (FAST) | 047–049 | 3 |

**Итого:** 48 кейсов. Нумерация сплошная 001–049 **без кейса 043** — в источнике
его нет (G20); нумерация не перенумеровывается (D30).

## Примечания

- Статусы кейсов (needs-review по G19, G21, G23–G25) — в групповых index.md.
- Системные обёртки: HY-SYS-027…045 (см. `../system-tests/hist-derived/index.md`).
- Соответствие «кейс ↔ модуль репозитория» — `trace/case-module-matrix.md`.
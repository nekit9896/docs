# specs/ — карта знаний СДКУ «ЭВОСКАДА» (Гидроуклон)

Назначение: агенто-ориентированное дерево знаний о бэкенде и сценариях
тестирования (подход SDD). **Источник истины — `../confluence/`** (8 исходных
файлов; изменяются только по прямой команде владельца — D36/D37, журнал —
`../confluence/README.md`). Всё в `specs/` — производные
фрагменты со ссылками на источник.

## Конвенции

1. Front-matter каждого фрагмента/кейса: `id`, `title`, `service`, `group`,
   `source`, `requires`, `related`, `status`.
2. ID: `KB-*` — фрагменты знаний (`KB-<область>-<NNN>`); кейсы используют
   `case_conflu` (HY-CALC-*, HY-HIST-*, HY-SYS-*) — неизменяемы, не перенумеровываются.
3. Статус: `verified` (перенесено точно из источника) | `needs-review`
   (требует сверки/подтверждения разработкой) | `placeholder` (не проработано).
4. Каждый факт живёт в ОДНОМ фрагменте; остальные ссылаются по ID.
   Дублирование фактов запрещено.
5. Связи — только через ID; затронутые сущности ищутся grep-ом (см. ниже).

## Дерево

| Путь | Содержание | ID |
|---|---|---|
| `knowledge/hydro-calculation/overview.md` | Микросервис: назначение, слои, модель запуска | KB-CALC-OVERVIEW-001 |
| `knowledge/hydro-calculation/formulas-and-units.md` | Формулы (напор, интерполяция), единицы, форматтеры | KB-CALC-FORMULA-001 |
| `knowledge/hydro-calculation/object-types.md` | Типы объектов (MT/LU/KIP/GRZDV/SGLU/ZDV/UR/PLTM), иерархия | KB-CALC-MODEL-001 |
| `knowledge/hydro-calculation/tags-lu.md` | Теги ЛУ (LU_*) | KB-CALC-TAGS-LU-001 |
| `knowledge/hydro-calculation/tags-kip.md` | Теги датчиков (KIP_*) | KB-CALC-TAGS-KIP-001 |
| `knowledge/hydro-calculation/tags-ur-sglu-grzdv-zdv-pltm.md` | Теги UR/SGLU/GRZDV/ZDV/PLTM | KB-CALC-TAGS-UR-001 |
| `knowledge/hydro-calculation/algorithms-overview.md` | AlgoManager, BaseAlgorithm, реестр алгоритмов | KB-CALC-ALGO-001 |
| `knowledge/hydro-calculation/algorithms-kip.md` | Алгоритмы Kip* | KB-CALC-ALGO-KIP-001 |
| `knowledge/hydro-calculation/algorithms-lu-control-and-alarms.md` | Алгоритмы Lu*: контроль, алармы, несущая | KB-CALC-ALGO-LU-CTRL-001 |
| `knowledge/hydro-calculation/algorithms-lu-data.md` | Алгоритмы Lu*: данные, плотность, план, трассировка | KB-CALC-ALGO-LU-DATA-001 |
| `knowledge/hydro-calculation/algorithms-lu-gravity.md` | LuGravitySegsAlg: самотёчные участки | KB-CALC-ALGO-LU-GRAV-001 |
| `knowledge/hydro-calculation/algorithms-lu-indicators.md` | Индикаторы контроля и связи (LuIndicator*) | KB-CALC-ALGO-LU-IND-001 |
| `knowledge/hydro-calculation/algorithms-sglu-ur.md` | Алгоритмы Sglu*/Ur* | KB-CALC-ALGO-SGLU-UR-001 |
| `knowledge/hydro-calculation/states.md` | Состояния: LU_CONTROL, LU_STATION, индикаторы | KB-CALC-STATE-001 |
| `knowledge/hydro-calculation/integration-evo-api.md` | Evo API: теги, объекты, алармы, валидация | KB-CALC-API-001 |
| `knowledge/hydro-calculation/modelling-and-kafka.md` | Режим моделирования, Kafka | KB-CALC-MODELLING-001 |
| `knowledge/hydro-calculation/config.md` | application.yml, MtProps, PlanScannerProps | KB-CALC-CONFIG-001 |
| `knowledge/hydro-calculation/alarms-writes-validation.md` | Алармы, записи тегов, ошибки | KB-CALC-SIDEFX-001 |
| `knowledge/hydro-calculation/test-stand.md` | Тестовый стенд HY-CALC: компоненты, I/O-механизмы, топики, начальное состояние, cleanup | KB-CALC-TESTSTAND-001 |
| `knowledge/hydro-calculation/test-plan-rules.md` | Тест-план HY-CALC: обозначения сценариев, правила исполнения, чек-лист, допущения, покрытие | KB-CALC-TESTPLAN-001 |
| `knowledge/hydro-history-and-model/overview.md` | Сервис истории/моделирования: типы сессий, структура | KB-HM-OVERVIEW-001 |
| `knowledge/hydro-history-and-model/sessions-lifecycle.md` | Сессии: создание, статусы, прикладные сессии, тег-время | KB-HM-SESSIONS-001 |
| `knowledge/hydro-history-and-model/player-timeline.md` | Плеер: Timeline, tick, предподгрузка | KB-HM-PLAYER-001 |
| `knowledge/hydro-history-and-model/fault-tolerance.md` | Отказоустойчивость: recover, isHalted, слежка за сессиями | KB-HM-FAULT-001 |
| `knowledge/hydro-history-and-model/save-model-session.md` | Сохранение модельной сессии, save_sessions, статусы | KB-HM-SAVE-001 |
| `knowledge/hydro-history-and-model/session-worker.md` | SessionWorker: фазы, цикл чтения, коды ошибок | KB-HM-WORKER-001 |
| `knowledge/hydro-history-and-model/watermark.md` | Watermark-сервис: lease, epoch, recovery | KB-HM-WATERMARK-001 |
| `knowledge/hydro-history-and-model/worker-executor-commands.md` | WorkerExecutor и Kafka-команды (ServiceCommand) | KB-HM-EXEC-001 |
| `knowledge/hydro-history-and-model/data-exchange-zip.md` | Экспорт/импорт данных сессий в ZIP | KB-HM-ZIP-001 |
| `knowledge/hydro-history-and-model/cleanup-imported-sessions.md` | Очистка импортированных сессий (needs-review, G11) | KB-HM-CLEANUP-001 |
| `knowledge/hydro-history-and-model/config-history-model.md` | Параметры tn-scada.* (metadata, default/yml) | KB-HM-CONFIG-001 |
| `knowledge/hydro-history-and-model/config-application-yml.md` | application.yml — полная таблица параметров | KB-HM-CONFIG-002 |
| `knowledge/hydro-history-and-model/storage-topics-endpoints.md` | Хранилища, Kafka-топики, endpoints, тег-время | KB-HM-STORAGE-001 |
| `knowledge/hydro-history-and-model/report-service.md` | Отчёты Гидроуклон (xlsx) | KB-HM-REPORT-001 |
| `knowledge/hydro-history-and-model/test-stand.md` | Тестовый стенд HY-HIST: компоненты, топики Kafka, константы, начальное состояние, cleanup | KB-HM-TESTSTAND-001 |
| `knowledge/hydro-history-and-model/test-plan-rules.md` | Тест-план HY-HIST: обозначения, enum-коды, правила исполнения, чек-лист, допущения | KB-HM-TESTPLAN-001 |
| `knowledge/system-tests/test-stand.md` | Стенд системных тестов: уровни SYS-1/2, компоненты, топики, щупы SPOT_*, начальное состояние, cleanup | KB-SYS-TESTSTAND-001 |
| `knowledge/system-tests/test-plan-rules.md` | Тестплан системных тестов: принципы, классификация, чек-лист, правила, допущения, блокеры, план исполнения | KB-SYS-TESTPLAN-001 |
| `knowledge/hmi-backend/overview.md` | hmi-backend: назначение, модули, компоненты, API V1/V2 | KB-HMI-OVERVIEW-001 |
| `knowledge/hmi-backend/tags-protobuf.md` | Тег, типы значений, Protobuf-схемы, конвертация | KB-HMI-TAG-001 |
| `knowledge/hmi-backend/rest-values.md` | REST: текущие значения тегов (п.1–5) | KB-HMI-REST-VAL-001 |
| `knowledge/hmi-backend/rest-search-history.md` | REST: поиск/навигация (п.6–9), история ClickHouse (п.10–12) | KB-HMI-REST-QUERY-001 |
| `knowledge/hmi-backend/rest-metadata.md` | REST: метаданные (объекты), сессии Modelling | KB-HMI-REST-META-001 |
| `knowledge/hmi-backend/websocket.md` | WebSocket V1/V2: команды, кадры, обслуживание сессий | KB-HMI-WS-001 |
| `knowledge/hmi-backend/data-stream.md` | Data Stream: стримовая обработка значений/алармов/истории | KB-HMI-STREAM-001 |
| `knowledge/hmi-backend/services.md` | Службы: прогрев, аудит/алармы, диагностика, ready-состояние | KB-HMI-SVC-001 |
| `knowledge/hmi-backend/errors-auth-filters.md` | Ошибки, фильтры, авторизация (needs-review, G13) | KB-HMI-ERR-001 |
| `knowledge/hmi-backend/config.md` | Переменные конфигурации (env/yml) | KB-HMI-CONFIG-001 |
| `knowledge/hmi-backend/modelling-topic-route.md` | Modelling (сессии), Topic-Route (маршруты) | KB-HMI-MODEL-001 |
| `knowledge/platform/c4-platform.md` | C4 Container Level: акторы, контейнеры, связи платформы (needs-review, G31) | KB-PLAT-C4-001 |
| `knowledge/platform/roadmap-testing.md` | Roadmap тестирования: слои, этапы 0–3, задачи/оценки, KPI (verified; исходник объединён с `old`, D37; G32, G40) | KB-PLAT-ROADMAP-001 |
| `knowledge/platform/testops-integration.md` | Тестопс: health-check, топики Kafka, WS/HTTP-эндпоинты (verified; расхождения G33–G34 открыты) | KB-PLAT-TESTOPS-001 |
| `trace/case-module-matrix.md` | Матрица «модуль репо ↔ кейсы» | — |
| `cases/hydro-calculation/` | Кейсы HY-CALC-* (85) в 8 доменных группах + index.md на группу: base-calcs (3.1), imbalance (3.2), stationarity (3.3), pressure-alarms (3.4), link-alarms (3.5), gravity-reliability (3.6), extra-calcs (3.7), cascade (3.8) | HY-CALC-* |
| `cases/hydro-history-and-model/` | Кейсы HY-HIST-* (48) в 10 доменных группах + index.md на группу: lifecycle (3.1), historical (3.2), modelling (3.3), import (3.4), export (3.5), watermark-progress (3.6), fault-tolerance (3.7), config-edge-cases (3.8), save-play (3.9), timeshift (3.10) | HY-HIST-* |
| `cases/system-tests/` | Кейсы HY-SYS-* (52) в 3 группах + index.md на группу: alarm-stubs (3.1, 26 заглушек из HY-CALC), hist-derived (3.2, 19 из HY-HIST), new-scenarios (3.3, 7 новых) | HY-SYS-* |

## Статус перекладки источников (порядок чтения)

| # | Источник (`../confluence/`) | Статус |
|---|---|---|
| 1 | `repo_description_hydro-calculation` | ✅ переложен (18 фрагментов) |
| 2 | `repo_description_hydro-history-and-model` | ✅ переложен (14 фрагментов, G7–G12; дубликаты удалены из источника) |
| 3 | `hmi-backend-descr.md` (шлюз к main*-топикам Kafka) | ✅ переложен (11 фрагментов, G13) |
| 4 | `test-plan-hydro-calculation.md` | ✅ переложен (85 кейсов HY-CALC в 8 группах + 2 фрагмента KB-CALC-TESTSTAND/TESTPLAN; G14–G16) |
| 5 | `test-plan-hydro-history-and-model.md` | ✅ переложен (48 кейсов HY-HIST в 10 группах + 2 фрагмента KB-HM-TESTSTAND/TESTPLAN; G18–G25; кейса 043 нет в источнике) |
| 6 | `test-plan-of-system-tests.md` | ✅ переложен (52 кейса HY-SYS в 3 группах + 2 фрагмента KB-SYS-TESTSTAND/TESTPLAN; G26–G30) |
| 7 | `C4.md` | ✅ переложен (1 фрагмент KB-PLAT-C4-001, `needs-review` — по старым диаграммам; G1, G31; переработка — отложенная задача) |
| 8 | `roadmap_coverage.md` | ✅ переложен (2 фрагмента KB-PLAT-ROADMAP/TESTOPS-001, `verified`); 2026-11-18: объединён с исходным роадмапом `old` (D37) — канон чисел/нумерации `../plans/automation-roadmap.md` (мастер с пометками трассировки), дубликаты задач помечены «= old X.Y», добавки 0.27–0.39; 2026-11-18: публикационная чистка Confluence-версии (служебные пометки удалены, «Предподготовка и настройка стенда»); расхождения G32–G34, G35–G41; `old` утилизирован; сроки — D2/D27 |

## Цикл поддержки документации (impact-анализ)

При изменении любого фрагмента, кейса или условия:

1. Взять `id` (или `case_conflu`) изменённой сущности.
2. Найти все ссылающиеся сущности: grep `id` по `docs/specs/`, `docs/meta/`,
   а также по маркерам `case_conflu` в кодовых репозиториях
   (`hydro-backend-tests`, `sdku-test-tools`).
3. Выдать владельцу список по каждой сущности: **проверить / уточнить /
   синхронизировать**.
4. Автоматически обновлять ТОЛЬКО индексы (`index.md`, этот `INDEX.md`)
   и front-matter-ссылки. Содержательные правки связанных сущностей —
   только по команде владельца.

Взаимные ссылки: поля `requires` (на что опирается) и `related` (соседи).
Скрипты-генераторы графа связей — по мере надобности (сейчас — grep).
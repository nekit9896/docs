# Tasks: Автоматизированные тесты гидрорасчёта (Гидроуклон)

**Input**: Design documents from `/specs/001-hydro-autotest-suite/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: тестовые модули кейсов здесь — это продукт фичи (автотесты), а не TDD-тесты реализации. Отдельные TDD/юнит-тесты не генерируются (не запрошены). Валидация — по quickstart.md.

**Organization**: задачи сгруппированы по пользовательским историям spec.md (US1 HY-CALC, US2 HY-HIST, US3 HY-SYS, US4 отчётность); 1 задача = 1 задача роадмапа (`docs/plans/automation-roadmap.md`; оценки Ч/SP — там же).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Один проект — pytest-пакет автотестов (см. plan.md): `autotests/src/`, `autotests/tests/`, `autotests/scripts/`, `autotests/config/`
- Пути указаны относительно будущего корня репозитория автотестов (`autotests/`); до его создания исходники и артефакты живут в `docs/` и переносятся (решение пользователя)
- Кейсы каталога: `docs/specs/cases/`; трассировка кейсы↔модули: `docs/specs/trace/case-module-matrix.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: create `autotests/` with `pyproject.toml`, `src/hydro_autotests/`, `tests/`, `scripts/`, `config/env/`, `testdata/`, `reports/` (plan.md Source Code tree)
- [ ] T002 [P] Initialize Python 3.12+ project with dependencies in `autotests/pyproject.toml`: pytest; lds-autotest as a library dependency (NO code copying — research R2, roadmap 0.26)
- [ ] T003 [P] Configure linting and typing in `autotests/pyproject.toml`: ruff, mypy (roadmap 0.24, research R8)
- [ ] T004 [P] Create environment template `autotests/config/env/example.yaml`: endpoints, ports, messaging topics, reserved tags; TODO placeholders for open questions R9 (hot topic ↔ `model_main_{id}`, ClickHouse `history`, PostgreSQL `sessions`, ports 8379/8432/8443, Kafka topic names) — roadmap 0.25
- [ ] T005 [P] Create stand environment config `autotests/config/env/test-stand.yaml` from example.yaml (no secrets; secrets via env vars — research R7) — roadmap 0.25
- [ ] T006 Configure pytest in `autotests/pyproject.toml` `[tool.pytest.ini_options]`: markers `hy_calc`, `hy_hist`, `hy_sys`, `smoke`, `slow`, `stand_depends`; addopts `--strict-markers` (contracts/run-cli.md)
- [ ] T007 [P] Document naming convention «test module ↔ case» in `autotests/README.md`: `tests/<suite>/test_<CASE-ID>_<slug>.py`, case_id in module name and reports (research R3, FR-007) — roadmap 0.10
- [ ] T008 [P] Create `autotests/.gitignore` (`.venv/`, `reports/`, `__pycache__/`, local env configs)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [P] Implement SSH stand adapter (two hops: account `-a` → scada_docker; run commands, copy files) in `autotests/src/hydro_autotests/clients/ssh.py` over lds-autotest — roadmap 0.3
- [ ] T010 [P] Implement Kafka adapter (send with partition key; read with filter and timeout ≥ 30 s — constraint from roadmap 0.4) in `autotests/src/hydro_autotests/clients/kafka.py`
- [ ] T011 [P] Implement Redis adapter (read/write/delete, TTL check, group commands) in `autotests/src/hydro_autotests/clients/redis.py` — roadmap 0.5
- [ ] T012 [P] Implement HTTP adapter for hmi-backend gateway (REST, user headers) in `autotests/src/hydro_autotests/clients/http.py` — roadmap 0.6
- [ ] T013 [P] Implement WebSocket adapter (subscribe to session events, wait-for-event, progress marks, connection control) in `autotests/src/hydro_autotests/clients/ws.py` — roadmap 0.7
- [ ] T014 [P] Implement Docker adapter (start/stop/inspect containers, read logs) in `autotests/src/hydro_autotests/clients/docker.py` — roadmap 0.8
- [ ] T015 [P] Implement ClickHouse and PostgreSQL adapters (queries, data upload) in `autotests/src/hydro_autotests/clients/ch.py` and `autotests/src/hydro_autotests/clients/pg.py` — roadmap 0.9
- [ ] T016 Implement waiters layer in `autotests/src/hydro_autotests/waiters/` (event waits via WS, polling via HTTP/Redis/DB; timeout windows from case rules; retry ONLY on infra errors — research R4; infra failure verdict is `infra_error`, never `failed` — FR-004)
- [ ] T017 Implement state cleanup fixtures (restore initial stand state before run: control off, auto-put off) in `autotests/src/hydro_autotests/fixtures/cleanup.py` + `autotests/tests/conftest.py` — roadmap 0.11/0.12
- [ ] T018 Implement stand run lock (semaphore; parallel runs on one stand blocked with explicit message — FR-010, research R5) in `autotests/src/hydro_autotests/fixtures/stand_lock.py`
- [ ] T019 Implement run reporting in `autotests/src/hydro_autotests/reporting/` per `contracts/report-schema.md`: verdict enum `passed`/`failed`/`skipped`/`infra_error` (FR-004); `mismatches` required and non-empty for `failed`; `skip_reason` required for `skipped`; `infra_reason` required for `infra_error` (SC-005); every result carries `case_id` (FR-007); plus JUnit XML output — roadmap 0.23 link
- [ ] T020 [P] Implement stand state auto-check lists in `autotests/scripts/stand_checks/` (readiness/consistency checks of stand state) — roadmap 0.13–0.15
- [ ] T021 [P] Implement ClickHouse history preparation script `autotests/scripts/prepare_history.py` (fill test tag history: not less than 10 000 values per tag over 48 hours — roadmap 0.18)
- [ ] T022 [P] Implement section config load into data-manager `autotests/scripts/load_section_config.py` (config + limits: deltas, density, pressure rate, control intervals; initial state: control off, auto-put off — roadmap 0.20)
- [ ] T023 [P] Reserve test tags MT1.LU1 and MT1.LU2 for autotests in `autotests/config/env/example.yaml` and `autotests/README.md` (agreement with teams, docs) — roadmap 0.19
- [ ] T024 Implement smoke test of stand availability in `autotests/tests/test_smoke_stand.py` (marker `smoke`; expected exit codes per contracts/run-cli.md: 0 or 3)
- [ ] T025 [P] Prepare import test data set (XLSX, archive with correct structure) in `autotests/testdata/` — roadmap 0.21
- [ ] T026 [P] Prepare alarm files and delivery script `autotests/scripts/prepare_alarms.py` (deliver to stand, restart history-and-model service) — roadmap 0.22
- [ ] T027 Implement TestOps integration `autotests/scripts/testops_upload.py` (upload run reports via TestOps API, launch runs from TestOps) — roadmap 0.23
- [ ] T028 Create CI pipeline config `autotests/.gitlab-ci.yml` (or CI-system equivalent): ruff/mypy checks, nightly full run, on-demand runs; failing cases block the quality gate — roadmap 0.24, FR-013

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Регрессионная проверка расчёта гидравлики (Priority: P1) 🎯 MVP

**Goal**: автоматизировать все 85 кейсов расчёта (HY-CALC) со сопоставлением результатов эталонам (FR-001)

**Independent Test**: `pytest -m hy_calc --junitxml=reports/junit.xml --report-json=reports/run.json` даёт вердикт по каждому кейсу HY-CALC без US2/US3 (quickstart.md, шаги 3–6)

### Implementation for User Story 1

> Все задачи фазы создают тестовые модули в `autotests/tests/hy_calc/` по кейсам `docs/specs/cases/hydro-calculation/` (правила исполнения — `docs/confluence/test-plan-*.md`); именование `test_<CASE-ID>_<slug>.py` (R3).

- [ ] T029 [P] [US1] Tests for расчётный напора (roadmap 1.1) in `autotests/tests/hy_calc/`
- [ ] T030 [P] [US1] Tests for постановка и снятие участка с контроля (roadmap 1.2) in `autotests/tests/hy_calc/`
- [ ] T031 [P] [US1] Tests for повторная постановка на контроль и заводская несущая давления (roadmap 1.3) in `autotests/tests/hy_calc/`
- [ ] T032 [P] [US1] Tests for снятие ограничения несущей и критический аларм превышения (roadmap 1.4) in `autotests/tests/hy_calc/`
- [ ] T033 [P] [US1] Tests for граничные случаи конфигурации участка (roadmap 1.5) in `autotests/tests/hy_calc/`
- [ ] T034 [P] [US1] Tests for алармы выхода давления за границы (roadmap 1.6) in `autotests/tests/hy_calc/`
- [ ] T035 [P] [US1] Tests for алармы при отключённых датчиках и комбинированный аларм (roadmap 1.7) in `autotests/tests/hy_calc/`
- [ ] T036 [P] [US1] Tests for отклонение расхода и реакция дебаланса на быстром цикле (roadmap 1.8) in `autotests/tests/hy_calc/`
- [ ] T037 [P] [US1] Tests for базовый напор станции и аларм близости к высоте (roadmap 1.9) in `autotests/tests/hy_calc/`
- [ ] T038 [P] [US1] Tests for алармы невалидных данных и плановая плотность (roadmap 1.10) in `autotests/tests/hy_calc/`
- [ ] T039 [P] [US1] Tests for стационарность датчика (roadmap 1.11) in `autotests/tests/hy_calc/`
- [ ] T040 [P] [US1] Tests for стационарность участка в целом (roadmap 1.12) in `autotests/tests/hy_calc/`
- [ ] T041 [P] [US1] Tests for автопостановка на контроль: полный цикл и отмена (roadmap 1.13) in `autotests/tests/hy_calc/`
- [ ] T042 [P] [US1] Tests for таймер автопостановки: перезапуск и снятие режима (roadmap 1.14) in `autotests/tests/hy_calc/`
- [ ] T043 [P] [US1] Tests for отклонения по смежным датчикам, гидроудар и коридор расхода (roadmap 1.15) in `autotests/tests/hy_calc/`
- [ ] T044 [P] [US1] Tests for потеря связи со всеми датчиками (roadmap 1.16) in `autotests/tests/hy_calc/`
- [ ] T045 [P] [US1] Tests for недостаточное число датчиков и индикатор контроля (roadmap 1.17) in `autotests/tests/hy_calc/`
- [ ] T046 [P] [US1] Tests for дебаланс расходов: штатная работа и утечка (roadmap 1.18) in `autotests/tests/hy_calc/`
- [ ] T047 [P] [US1] Tests for дебаланс с отключённым расходомером и ручным вводом (roadmap 1.19) in `autotests/tests/hy_calc/`
- [ ] T048 [P] [US1] Tests for обнаружение самотёчного участка и прогноз риска (roadmap 1.20) in `autotests/tests/hy_calc/`

- [ ] T049 [P] [US1] Tests for алармы достоверности датчиков (roadmap 1.21) in `autotests/tests/hy_calc/`
- [ ] T050 [P] [US1] Tests for расчёт скорости изменения давления: два алгоритма (roadmap 1.22) in `autotests/tests/hy_calc/`
- [ ] T051 [P] [US1] Tests for фильтрация конфигурации участка (roadmap 1.23) in `autotests/tests/hy_calc/`
- [ ] T052 [P] [US1] Tests for активность сегмента и группа задвижек (roadmap 1.24) in `autotests/tests/hy_calc/`
- [ ] T053 [P] [US1] Tests for видимость сегмента и датчика (roadmap 1.25) in `autotests/tests/hy_calc/`
- [ ] T054 [P] [US1] Tests for трассировка расчётов (roadmap 1.26) in `autotests/tests/hy_calc/`
- [ ] T055 [P] [US1] Tests for распределение плотности (roadmap 1.27) in `autotests/tests/hy_calc/`
- [ ] T056 [P] [US1] Tests for унификация дельт и уставка ЦСПА (roadmap 1.28) in `autotests/tests/hy_calc/`
- [ ] T057 [P] [US1] Tests for высота датчика и диапазон напора (roadmap 1.29) in `autotests/tests/hy_calc/`
- [ ] T058 [P] [US1] Tests for диапазон напора выше несущей и отклонение напора (roadmap 1.30) in `autotests/tests/hy_calc/`
- [ ] T059 [P] [US1] Tests for публикация алармов дебаланса и самотёков в топик алармов (roadmap 1.31) in `autotests/tests/hy_calc/`
- [ ] T060 [P] [US1] Tests for статус ремонта и перенос времени контроля (roadmap 1.32) in `autotests/tests/hy_calc/`
- [ ] T061 [P] [US1] Tests for план перекачки (roadmap 1.33; run with 60 min wait, marker `slow`) in `autotests/tests/hy_calc/`
- [ ] T062 [P] [US1] Tests for расширенные лимиты скорости давления и трассировки (roadmap 1.34) in `autotests/tests/hy_calc/`
- [ ] T063 [P] [US1] Tests for автоматическое распределение плотности и плато самотёков (roadmap 1.35) in `autotests/tests/hy_calc/`
- [ ] T064 [P] [US1] Tests for дебаланс со средними значениями и зона «недостаточно данных» (roadmap 1.36) in `autotests/tests/hy_calc/`
- [ ] T065 [P] [US1] Tests for прерывание автопостановки во время отсчёта таймера (roadmap 1.37) in `autotests/tests/hy_calc/`
- [ ] T066 [P] [US1] Tests for каскадные эффекты: влияние отключений (roadmap 1.38) in `autotests/tests/hy_calc/`
- [ ] T067 [P] [US1] Tests for каскадные эффекты: расхождение алгоритмов при отключённом управлении (roadmap 1.39) in `autotests/tests/hy_calc/`

**Checkpoint**: US1 (MVP) complete — прогон `pytest -m hy_calc` даёт полный вердикт по 85 кейсам; валидация по quickstart.md

---

## Phase 4: User Story 2 - Проверка истории и моделирования (Priority: P2)

**Goal**: автоматизировать 48 кейсов HY-HIST (жизненный цикл сессий, режимы, плеер, импорт/экспорт, алармы, отказоустойчивость — FR-002)

**Independent Test**: `pytest -m hy_hist` даёт вердикт по каждому кейсу HY-HIST независимо от US1/US3

### Implementation for User Story 2

> Все задачи фазы создают тестовые модули в `autotests/tests/hy_hist/` по кейсам `docs/specs/cases/hydro-history-and-model/` (кейсы HY-HIST-001…049 без 043).

- [ ] T068 [P] [US2] Tests for создание и завершение сессии: happy-path (HTTP, WS-события, освобождение топиков и слотов; roadmap 2.1) in `autotests/tests/hy_hist/`
- [ ] T069 [P] [US2] Tests for управление сессией: пауза, стоп, ошибки, идемпотентность запуска (roadmap 2.2) in `autotests/tests/hy_hist/`
- [ ] T070 [P] [US2] Tests for конкурентный запуск сессий и квоты (3-я сессия при квоте 2, завершение самой старой; roadmap 2.3) in `autotests/tests/hy_hist/`
- [ ] T071 [P] [US2] Tests for режим REAL_TIME (публикация в модельный топик, без записи в историю; roadmap 2.4) in `autotests/tests/hy_hist/`

- [ ] T072 [P] [US2] Tests for режим FAST (чтение истории из ClickHouse, водяной знак; roadmap 2.5) in `autotests/tests/hy_hist/`
- [ ] T073 [P] [US2] Tests for режим SIMULATION (команды set и advance, сохранение и публикация; roadmap 2.6) in `autotests/tests/hy_hist/`
- [ ] T074 [P] [US2] Tests for инкрементальная загрузка истории (догрузка при запуске новой сессии; roadmap 2.7) in `autotests/tests/hy_hist/`
- [ ] T075 [P] [US2] Tests for контроль прогресса и отставания (speed, lag, watermark, target; roadmap 2.8) in `autotests/tests/hy_hist/`
- [ ] T076 [P] [US2] Tests for управление плеером (play/pause/seek/change_speed; roadmap 2.9) in `autotests/tests/hy_hist/`
- [ ] T077 [P] [US2] Tests for экспорт данных (выгрузка истории в файлы, корректность форматов; roadmap 2.10) in `autotests/tests/hy_hist/`
- [ ] T078 [P] [US2] Tests for импорт данных и ошибки формата (невалидный формат, дубликаты, некорректные даты, неизвестный тег; roadmap 2.11) in `autotests/tests/hy_hist/`
- [ ] T079 [P] [US2] Tests for расширенные сценарии импорта/экспорта (пакетный импорт, работа в активной сессии; roadmap 2.12) in `autotests/tests/hy_hist/`
- [ ] T080 [P] [US2] Tests for импорт с перезаписью и контроль статуса результата (roadmap 2.13) in `autotests/tests/hy_hist/`
- [ ] T081 [P] [US2] Tests for сохранение в историю ClickHouse (запись расчётных значений, чтение для пересчёта; roadmap 2.14) in `autotests/tests/hy_hist/`
- [ ] T082 [P] [US2] Tests for воспроизведение истории без библиотек (roadmap 2.15) in `autotests/tests/hy_hist/`
- [ ] T083 [P] [US2] Tests for алармы в режиме моделирования (приоритеты, подавление дублей, топик алармов сессии; roadmap 2.16) in `autotests/tests/hy_hist/`
- [ ] T084 [P] [US2] Tests for отказоустойчивость (потеря соединения, рестарт сервиса, сбой ClickHouse; roadmap 2.17) in `autotests/tests/hy_hist/`
- [ ] T085 [P] [US2] Tests for граничные значения и допустимые размеры (пустая история, большой файл, обрезка значений; roadmap 2.18) in `autotests/tests/hy_hist/`
- [ ] T086 [P] [US2] Tests for множество датчиков и тегов (roadmap 2.19; marker `slow` if needed) in `autotests/tests/hy_hist/`
- [ ] T087 [P] [US2] Tests for резервное копирование данных сессии и восстановление (roadmap 2.20) in `autotests/tests/hy_hist/`

**Checkpoint**: US2 complete — прогон `pytest -m hy_hist` даёт полный вердикт по 48 кейсам

---

## Phase 5: User Story 3 - Системные сквозные сценарии (Priority: P3)

**Goal**: автоматизировать 52 системных кейса HY-SYS (сквозные потоки через сервисы стенда, точки контроля, алармы — FR-003)

**Independent Test**: `pytest -m hy_sys` даёт вердикт по каждому кейсу HY-SYS независимо от US1/US2

### Implementation for User Story 3

> Все задачи фазы создают тестовые модули в `autotests/tests/hy_sys/` по кейсам `docs/specs/cases/system-tests/` (кейсы HY-SYS-001…052).

- [ ] T088 [P] [US3] Tests for обнаружение давления вне диапазона, аларм пропавшего сигнала, выключение контроля (roadmap 3.1) in `autotests/tests/hy_sys/`
- [ ] T089 [P] [US3] Tests for автопостановка на контроль: полный цикл и отмена (roadmap 3.2) in `autotests/tests/hy_sys/`
- [ ] T090 [P] [US3] Tests for отклонение давления по датчикам и быстрое изменение (roadmap 3.3) in `autotests/tests/hy_sys/`
- [ ] T091 [P] [US3] Tests for критическое превышение несущей (roadmap 3.4) in `autotests/tests/hy_sys/`
- [ ] T092 [P] [US3] Tests for утечка: обнаружение и снятие (roadmap 3.5) in `autotests/tests/hy_sys/`
- [ ] T093 [P] [US3] Tests for самотёки: обнаружение и алармы (roadmap 3.6) in `autotests/tests/hy_sys/`
- [ ] T094 [P] [US3] Tests for аларм по группе задвижек (roadmap 3.7) in `autotests/tests/hy_sys/`
- [ ] T095 [P] [US3] Tests for расхождение датчиков и стационарность (roadmap 3.8) in `autotests/tests/hy_sys/`
- [ ] T096 [P] [US3] Tests for исправность датчиков и пропавший сигнал (roadmap 3.9) in `autotests/tests/hy_sys/`
- [ ] T097 [P] [US3] Tests for связь и число датчиков на связи (roadmap 3.10) in `autotests/tests/hy_sys/`

- [ ] T098 [P] [US3] Tests for дебаланс: обнаружение и подавление (roadmap 3.11) in `autotests/tests/hy_sys/`
- [ ] T099 [P] [US3] Tests for статусы ремонта и контроля (roadmap 3.12) in `autotests/tests/hy_sys/`
- [ ] T100 [P] [US3] Tests for интервалы контроля (дельты давления/расхода, время контроля; roadmap 3.13) in `autotests/tests/hy_sys/`
- [ ] T101 [P] [US3] Tests for постановка на контроль вне режима (уставка ЦСПА; roadmap 3.14) in `autotests/tests/hy_sys/`
- [ ] T102 [P] [US3] Tests for снятие с контроля, в т.ч. при отключённом сегменте (roadmap 3.15) in `autotests/tests/hy_sys/`
- [ ] T103 [P] [US3] Tests for давление вне диапазона при отключённом сегменте (roadmap 3.16) in `autotests/tests/hy_sys/`
- [ ] T104 [P] [US3] Tests for аларм недостаточности данных стационарности (roadmap 3.17) in `autotests/tests/hy_sys/`
- [ ] T105 [P] [US3] Tests for реакция на утечку при автопостановке на контроль (roadmap 3.18) in `autotests/tests/hy_sys/`
- [ ] T106 [P] [US3] Tests for постановка на контроль в переходном режиме (roadmap 3.19) in `autotests/tests/hy_sys/`
- [ ] T107 [P] [US3] Tests for водяной знак REAL_TIME (roadmap 3.20) in `autotests/tests/hy_sys/`
- [ ] T108 [P] [US3] Tests for сквозная цепочка давления (имитация СДКУ → расчёт → аларм → конечная точка бэкенда; roadmap 3.21; требует документации alarm-service) in `autotests/tests/hy_sys/`
- [ ] T109 [P] [US3] Tests for сквозная цепочка расчёта напора (roadmap 3.22) in `autotests/tests/hy_sys/`
- [ ] T110 [P] [US3] Tests for сценарий постановки на контроль в связке сервисов (roadmap 3.23; требует документации alarm-service) in `autotests/tests/hy_sys/`
- [ ] T111 [P] [US3] Tests for сценарий снятия с контроля в связке сервисов (roadmap 3.24; REST API data-manager не документирован — уточнить) in `autotests/tests/hy_sys/`
- [ ] T112 [P] [US3] Tests for сценарий отклонения давления в связке сервисов (roadmap 3.25) in `autotests/tests/hy_sys/`
- [ ] T113 [P] [US3] Tests for сценарий воспроизведения истории в связке сервисов (roadmap 3.26) in `autotests/tests/hy_sys/`
- [ ] T114 [P] [US3] Tests for сквозные утечка и самотёк (roadmap 3.27) in `autotests/tests/hy_sys/`
- [ ] T115 [P] [US3] Tests for кросс-валидация: сверка одного тестового тега в расчётном топике, в БД истории и через API шлюза (roadmap 3.28; финальная проверка стенда) in `autotests/tests/hy_sys/`

**Checkpoint**: US3 complete — прогон `pytest -m hy_sys` даёт полный вердикт по 52 кейсам

---

## Phase 6: User Story 4 - Отчётность и карта покрытия (Priority: P3)

**Goal**: прозрачность программы — покрытие каталога, история вердиктов, управление эталонами (FR-011, FR-012)

**Independent Test**: отчёт и карта покрытия строятся по завершённым прогонам и каталогу и сверяются с фактическим составом проверок

### Implementation for User Story 4

- [ ] T116 [P] [US4] Implement coverage map «case ↔ test» generator `autotests/scripts/coverage_report.py`: for non-automated cases `reason` is required (FR-012); source of truth `docs/specs/cases/` + `autotests/tests/`
- [ ] T117 [P] [US4] Implement run summary and verdict history view in `autotests/src/hydro_autotests/reporting/summary.py` (status of last run per case, verdict history — FR-008, US4 scenario 1)
- [ ] T118 [US4] Implement reference (etalon) versioning in `autotests/src/hydro_autotests/references/`: `version` grows on approved change; `change_log` records what changed and why (FR-011, data-model CaseReference)
- [ ] T119 [US4] Wire quality gate to CI `autotests/.gitlab-ci.yml` per `contracts/run-cli.md` exit codes: `failed` blocks acceptance of the change (FR-013)

**Checkpoint**: US4 complete — карта покрытия и сводка доступны команде

---

## Addendum: Setup tasks (roadmap 0.27–0.39)

> Added 2026-11-18 (D37) as part of the roadmap merge: tasks 0.27–0.39 of the
> combined roadmap (`docs/plans/automation-roadmap.md`) that have no counterparts
> in the main plan. Duplicate roadmap items are collapsed into existing tasks
> 0.1–0.26 («= old X.Y» marks in `docs/plans/automation-roadmap.md`).
> Hours/SP estimates are in the roadmap. T-numbers continue after T125;
> existing T-numbers are unchanged (linked to Jira).

- [ ] T126 [P] Requirements registry for the hydroslope (ТРП/РА) with requirement→case bindings (roadmap 0.27; deferred — D19) in `docs/specs/trace/`
- [ ] T127 [P] Automation roadmap document (roadmap 0.28) — done: `docs/plans/automation-roadmap.md`
- [ ] T128 [P] Test plan for hydro-calculation (roadmap 0.29) — done: `docs/confluence/test-plan-hydro-calculation.md`
- [ ] T129 [P] Test plan for hydro-history-and-model (roadmap 0.30) — done: `docs/confluence/test-plan-hydro-history-and-model.md`
- [ ] T130 [P] Test plan for system tests (roadmap 0.31) — done: `docs/confluence/test-plan-of-system-tests.md`
- [ ] T131 [P] Test plan for E2E tests (roadmap 0.32)
- [ ] T132 [P] Study hmi-backend contracts (write/read of tags) (roadmap 0.33) — summarized in `docs/specs/knowledge/hmi-backend/`
- [ ] T133 [P] Study alarm contracts (WS/REST/Kafka/Redis) (roadmap 0.34; blocked: alarm-service docs missing — G28)
- [ ] T134 [P] Deploy TestOps containers (Kafka, Redis, PG, CH, nginx) (roadmap 0.35)
- [ ] T135 [P] Configure nginx for TestOps (port proxying, TLS if needed) (roadmap 0.36)
- [ ] T136 [P] Get stand observation access: K8s namespace, Grafana, Jaeger, logging (roadmap 0.37)
- [ ] T137 [P] Publish sdku-test-tools for reuse by test projects (wheel in Nexus, D7) (roadmap 0.38)
- [ ] T138 [P] Implement TestOps API for uploading front-end reports (HTML/JSON) (roadmap 0.39)

## Final Phase: Polish & Cross-Cutting Concerns

- [ ] T120 Run quickstart.md validation end-to-end (scenarios table — all User Stories)
- [ ] T121 Measure full catalog run duration; confirm ≤ 12 hours nightly window (SC-002); tune waits if needed
- [ ] T122 Verify reproducibility: repeat run on restored stand gives identical verdicts per case (FR-005, SC-003)
- [ ] T123 Verify report quality: 100% of failures contain `mismatches`/checkpoint info (SC-005); infra failures classified `infra_error` (FR-004)
- [ ] T124 [P] Update docs: `docs/specs/knowledge/platform/roadmap-testing.md` counters, `docs/confluence/roadmap_coverage.md`, `docs/specs/trace/case-module-matrix.md` coverage column
- [ ] T125 [P] Calibrate estimates: compare actuals vs roadmap rates 2/4/8 h after first US1 groups; target ±15% (roadmap «Точность оценок»)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–6)**: All depend on Foundational phase completion
  - Согласно роадмапу поставка последовательная: US1 (этап 1) → US2 (этап 2) → US3 (этап 3); US4 наращивается по мере прогонов
  - Формально истории независимы и могут идти параллельно при наличии ресурса
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: after Foundational; использует адаптеры SSH/HTTP/Redis/Docker/CH/PG, waiters (T009–T017), отчёт (T019)
- **User Story 2 (P2)**: after Foundational; дополнительно адаптеры WS/Kafka (T010, T013), скрипты истории/алармов (T021, T026)
- **User Story 3 (P3)**: after Foundational; использует все адаптеры и сквозные скрипты (T020–T022); задачи 3.21/3.23 требуют документации alarm-service (блокер — внешний)
- **User Story 4 (P3)**: after первых прогонов US1; T119 зависит от T028

### Within Each User Story

- Каждая задача-группа кейсов независима (отдельные файлы модулей) — [P]
- Кейс перед тестом: сверить `docs/specs/cases/` и правила исполнения из `docs/confluence/test-plan-*.md`
- Story complete = все кейсы набора имеют вердикт в отчёте (FR-001…FR-003)

### Parallel Opportunities

- Setup tasks marked [P] — parallel
- Foundational tasks marked [P] (адаптеры, скрипты) — parallel within Phase 2
- Within US1/US2/US3: все групповые задачи [P] — параллельно разными исполнителями
- Ставки кейсов роадмапа (2/4/8 ч) сохраняются; оценки — `docs/plans/automation-roadmap.md`

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (39 задач, 85 кейсов)
4. **STOP and VALIDATE**: `pytest -m hy_calc` + quickstart.md; сверка отчёта (контракт report-schema.md)
5. Готово к регрессии расчёта (MVP программы)

### Incremental Delivery

1. Setup + Foundational → foundation ready (этап 0 роадмапа)
2. US1 → валидация → MVP (этап 1: 376 ч / 188 SP)
3. US2 → валидация (этап 2: 250 ч / 125 SP)
4. US3 → валидация (этап 3: 336 ч / 168 SP)
5. US4 наращивается параллельно прогонам

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Каждая задача 1:1 соответствует задаче роадмапа (номер в скобках) — оценки Ч/SP и порядок Jira не дублируются
- Commit after each task or logical group; стоп в любой checkpoint — независимая валидация истории
- Открытые вопросы стенда (R9) закрываются в рамках задач 0.1/0.2/0.25 (T004/T005/T009–T015); до закрытия зависимые проверки — `skip` с причиной
- Избегать: смешения кейсов в одном модуле (нарушает FR-007), повторов на расхождениях (маскирует дефекты), хардкода адресов стенда







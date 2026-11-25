# Implementation Plan: Автоматизированные тесты гидрорасчёта (Гидроуклон)

**Branch**: `001-hydro-autotest-suite` | **Date**: 2026-11-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-hydro-autotest-suite/spec.md`

## Адаптация 2026-11-19

Фактическая организация работ отличается от исходного текста плана (расхождение
**G43**, `docs/meta/discrepancies-2026-11-19.md`). Ключевые дельты: библиотека
стенда — наш `sdku-test-tools` вместо `lds-autotest`; pytest-пакеты живут в
`hydro-backend-tests/` (не в `autotests/`); инфраструктурные ошибки — FAILED с
диагностикой (не `infra_error`); линтинг — black/isort/flake8; доставка —
Docker-only образ `evoscada_docker/sdku_test_tools:<semver>` (D41). Полный
маппинг путей/зависимостей/вердиктов — в `tasks.md`, раздел «Адаптация 2026-11-19»;
решения — `docs/decisions/2026-11-19-hmi-client-contract.md` (D38–D44).
Рабочий план этапов — `docs/plans/2026-11-19-hydroslope-autotest-workplan.md`.

## Summary

Автоматизировать регрессионное тестирование гидрорасчёта (185 кейсов каталога: 85 HY-CALC, 48 HY-HIST, 52 HY-SYS) на базе pytest и клиентов тестового стенда из библиотеки lds-autotest. Технический подход: единый pytest-пакет с адаптерами клиентов, фикстурами восстановления состояния, жёсткой связью «тест ↔ кейс» через идентификаторы каталога, отчётностью JUnit XML + JSON (контракт) и поэтапной поставкой HY-CALC → HY-HIST → HY-SYS. Оценки и порядок задач — `docs/plans/automation-roadmap.md` (126 задач, 1168 ч / 584 SP).

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: pytest; библиотека lds-autotest (клиенты SSH, Kafka, Redis, HTTP, WebSocket, Docker, ClickHouse, PostgreSQL); ruff/mypy для статических проверок

**Storage**: как на тестовом стенде — PostgreSQL (model/points/calc), ClickHouse (history/alarms/model), Redis; результаты прогонов — JUnit XML + JSON-файлы

**Testing**: pytest; маркеры `hy_calc`/`hy_hist`/`hy_sys`/`smoke`/`slow`/`stand_depends`; JUnit XML → TestOps

**Target Platform**: Linux (стенд и CI-агенты); локальная разработка — Linux/Windows

**Project Type**: cli / test-automation framework (pytest-пакет)

**Performance Goals**: полный регрессионный прогон каталога ≤ 12 часов (ночное окно, SC-002)

**Constraints**: один выделенный стенд — изоляция прогонов (FR-010); восстановление начального состояния перед прогоном (FR-005); окна ожидания по правилам исполнения кейсов (чтение Kafka ≥ 30 с); погрешность оценок ±30%

**Scale/Scope**: 185 кейсов каталога; программа работ — 126 задач / 1168 ч (docs/plans/automation-roadmap.md)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` — нератифицированный шаблон с плейсхолдерами: проектные принципы не заданы, нарушений быть не может. В качестве временных гейтов качества принято:

- [x] Технологии согласованы с профилем исполнителя и существующей кодовой базой (Python/pytest, lds-autotest) — research R1/R2
- [x] Все решения документированы с альтернативами (research.md)
- [x] Открытые вопросы стенда не блокируют проектирование (research R9; Assumptions spec)
- [x] Повторная проверка после Phase 1: нарушений не выявлено, Complexity Tracking не требуется

Рекомендация: ратифицировать конституцию проекта отдельным решением до начала разработки.

## Project Structure

### Documentation (this feature)

```text
specs/001-hydro-autotest-suite/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
autotests/                        # репозиторий автотестов (будет создан; артефакты пока живут в docs/)
├── pyproject.toml                # зависимости (pytest, lds-autotest), инструменты качества
├── config/
│   └── env/
│       ├── example.yaml          # шаблон окружения: адреса, порты, каналы обмена (R9 — TODO-поля)
│       └── test-stand.yaml       # значения стенда (без секретов)
├── src/hydro_autotests/
│   ├── clients/                  # адаптеры поверх lds-autotest: ssh, kafka, redis, http, ws, docker, ch, pg
│   ├── fixtures/                 # очистка состояния, подготовка истории, блокировка стенда
│   ├── waiters/                  # единый слой ожиданий: события, поллинг, таймауты
│   └── reporting/                # JSON-отчёт по contracts/report-schema.md
├── tests/
│   ├── conftest.py
│   ├── hy_calc/                  # test_HY-CALC-NNN_*.py — 85 кейсов
│   ├── hy_hist/                  # test_HY-HIST-NNN_*.py — 48 кейсов
│   └── hy_sys/                   # test_HY-SYS-NNN_*.py — 52 кейса
├── scripts/                      # подготовка стенда, история ClickHouse, загрузка отчётов в TestOps
└── reports/                      # JUnit XML и JSON отчёты (в .gitignore)
```

**Structure Decision**: единый pytest-пакет (один проект). Клиенты стенда выделяются в тонкие адаптеры поверх библиотеки lds-autotest без копирования кода (research R2, задача 0.26); тесты разложены по наборам каталога с жёсткой связью «модуль ↔ кейс» (research R3); адреса стенда живут в env-конфиге (R7). Артефакты Spec Kit остаются в `specs/001-hydro-autotest-suite/` до появления репозитория автотестов, после чего переносятся вместе с исходниками (решение пользователя).

## Complexity Tracking

> Нарушений конституции нет (конституция не ратифицирована) — таблица не заполняется.


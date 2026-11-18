---
id: KB-PLAT-TESTOPS-001
title: "Тестопс и точки интеграции: health-check, топики, WS/HTTP-эндпоинты, стенды"
service: platform
group: roadmap
source: confluence/roadmap_coverage.md
requires: [KB-PLAT-ROADMAP-001]
related: [KB-SYS-TESTSTAND-001, KB-HM-TESTSTAND-001, KB-CALC-TESTSTAND-001, KB-HMI-OVERVIEW-001]
status: verified
---

# Тестопс и точки интеграции (roadmap, этап 0/2/3)

> `verified` (2026-11-18, D37): перенесено точно из объединённого роадмапа
> (`confluence/roadmap_coverage.md`, детализация — «Детализация этапа 0»).
> Имена топиков и сервисов — из источника; расхождения с тест-планами и
> конфигами остаются открытыми — G33/G34 (сверить с разработкой до написания клиентов).

## Health-check сервисов (в setup, задача 5.1)

Перед каждым тестом — проверка, что микросервисы живы (`pytest` fixture
`session` → `pytest.skip`, если сервис упал). Эндпоинты из источника:

| Сервис | URL диагностики |
|---|---|
| hydro-calculation | `http://hydro-calculation:8080/actuator/health` |
| hydro-history-model | `http://hydro-history-model:8080/actuator/health` |
| hmi-backend | `http://hmi-backend:8080/actuator/health` |
| alarm-service | `http://alarm-service:8080/actuator/health` |
| alarm-view | `http://alarm-view:8080/actuator/health` |
| clickhouse | `http://clickhouse:8123/ping` |
| redis | `http://redis:6379` |

## Тестовые данные на общем стенде (задача 5.2–5.3)

Стенд `<STAND_HOST>` — общий (реальный адрес за плейсхолдером — D3). Другие пользователи меняют данные; тесты не чистят
всё подряд. Стратегия: **резервирование** технологических объектов/труб
(например, `MT1.LU1`, `MT1.LU2` — «тестовые», не трогают; документировать в
README). Подготовка истории: `python prepare_data.py --hours 48` → ClickHouse.

## Клиенты sdku-test-tools (задачи 3.1–3.8)

Kafka (producer/consumer), Redis (GET/SET/DEL/KEYS, TTL, pipeline), HTTP
(X-USER-* headers), SSH, WebSocket (`wait_event`, `wait_watermark`), Docker,
ClickHouse (HTTP :8123), PostgreSQL. Константы — ENV-файл с URL/кредами/
именами топиков (D13: владелец имён — `hydro-backend-tests`).

## Топики Kafka (таблицы источника, этап 2/3)

⚠️ G33: в источнике `cspa-main`; в тест-плане hydro-calculation и
KB-CALC-TESTSTAND-001 топик называется `main`. Прочие имена — сверить перед
написанием клиентов.

| Топик | Направление | Формат | От | Кому |
|---|---|---|---|---|
| `cspa-main` (⚠️ G33) | Вход + Выход | `{tag, ts, value, invalid}` | СДКУ/тест, hydro-calc | hydro-calc, hmi-backend, тест |
| `alarm` | Выход | `{tag, ts, value, text, priority, state}` | hydro-calc, alarm-service | alarm-view, тест |
| `model_main_{id}` | Вход + Выход | `{tag, ts, value, invalid}` | mod-hist, hydro-calc | hydro-calc, hmi-backend, тест |
| `model_alarm_{id}` | Выход | `{tag, ts, value, text, priority, state}` | hydro-calc, alarm-service | alarm-view, тест |
| `mod-hist-commands` | Выход | `{sessionId, command, params, ts}` | mod-hist | hydro-calc |
| `mod-hist-results` | Выход | `{sessionId, ack, ts}` | hydro-calc | mod-hist |
| `mod-hist-events` | Выход | `{sessionId, eventType, data, ts}` | mod-hist | hmi-backend |

В оперативном режиме (этап 2.8) используется `cspa-main` + `alarm`; в режиме
моделирования — `model_main_{id}` / `model_alarm_{id}`.

## WS-эндпоинты (E2E, этап 3)

| Эндпоинт | Что приходит | Для чего |
|---|---|---|
| `ws://hmi-backend:8080/hotlink` | Теги: Press, Head, Delta, Control… | Имитация «экрана» диспетчера |
| `ws://alarm-view:8080/alarm` | Алармы: text, state, priority | Имитация «экрана» алармов |
| `ws://mod-hist:8080/ws/sessions/{id}` | События сессии: STARTED, STOPPED, WATERMARK… | Состояние сессии |

## HTTP-эндпоинты (E2E, этап 3)

| Эндпоинт | Метод | Для чего |
|---|---|---|
| `http://hmi-backend:8080/api/v2/signals` | POST | Запись тегов (имитация UI) |
| `http://hmi-backend:8080/api/v2/tags/{tag}` | GET | Чтение значения тега |
| `http://mod-hist:8080/api/sessions` | POST | Создание сессии |
| `http://mod-hist:8080/api/sessions/{id}/start` | POST | Запуск |
| `http://mod-hist:8080/api/sessions/{id}/stop` | POST | Остановка |
| `http://mod-hist:8080/api/sessions/{id}` | DELETE | Закрытие |
| `http://mod-hist:8080/api/sessions/{id}/progress` | GET | Прогресс |
| `http://mod-hist:8080/api/sessions/{id}/export` | POST | Экспорт |

⚠️ G22: REST-пути mod-hist в roadmap (в т.ч. `/sessions/playback`) —
семантически те же псевдо-endpoint'ы `api.*` из тест-плана HY-HIST; реальные
контракты не подтверждены.

## Карта взаимодействия тестов и бэкенда (схема источника)

`Источники данных → Kafka: main → hydro-calculation (алгоритмы; выход —
Kafka: main / Kafka: alarm / HTTP hmi-backend) → hmi-backend (WS: hotlink) +
alarm-service (генерация алармов) → hmi-frontend / alarm-view`.

## Схемы бизнес-сценариев E2E (этап 3, IV-1…IV-4)

Источник содержит seq-диаграммы IV-1 «Постановка на контроль», IV-2 «Снятие с
контроля», IV-3 «Отклонение давления за допустимый диапазон» (проверки:
`LU.Control=1`, `PressStation` зафиксирован, `AlmDevRangeMax`, текст аларма
«превышение», `state=ACTIVE`), IV-4 «Воспроизведение истории» (сессия, топики
`model_main_{id}`, `playbackOperation (Play)`, проверка WS-данных/алармов,
`/sessions/{id}/status = RUNNING`). Это ориентиры этапа 3; кейсы E2E не заводим
(D34).
---
id: KB-SYS-TESTSTAND-001
title: Тестовый стенд системных тестов: уровни, компоненты, топики Kafka, щупы, начальное состояние, cleanup
service: system-tests
group: test-plan
source: confluence/test-plan-of-system-tests.md#1.2,#1.4,#2
requires: [KB-HM-TESTSTAND-001, KB-CALC-TESTSTAND-001]
related: [KB-HM-STORAGE-001, KB-HMI-WS-001, KB-SYS-TESTPLAN-001]
status: verified
---

# KB-SYS-TESTSTAND-001 — Тестовый стенд системных тестов

## Уровни (§1.2)

| Уровень | Описание | Кол-во (по источнику) |
|---|---|---|
| **SYS-1** | 2 микросервиса (mod-hist ↔ hydro-calc) | ~25 |
| **SYS-2** | 3 микросервиса (hydro-calc → alarm-service → hmi-backend) | ~28 |

> SYS-3 (E2E операторский) и SYS-4 (отказоустойчивость) — **в тестплан не входят**.

## Компоненты (§2.1)

| Компонент | Роль | Примечание |
|---|---|---|
| hydro-history-and-model (mod-hist / history-player) | Оркестратор сессий | |
| hydro-calculation | Расчёты | |
| hmi-backend | Шлюз (REST + WS) | Не считается микросервисом для классификации |
| alarm-service | Обработка/хранение алармов | **Док-ция уточняется** |
| alarm-view-service | Отображение алармов | **Док-ция уточняется** |
| data-manager | Конфигурация ИМ | **Док-ция уточняется** |
| Kafka | Брокер | Топики: см. ниже |
| ClickHouse | История | **Схема уточняется** |
| PostgreSQL | ИМ, сессии | **Схема уточняется** |
| Redis | Кэш, watermark | |

## Топики Kafka (§2.2)

| Топик | Producer | Consumer | Формат |
|---|---|---|---|
| `cspa-main` (только через шлюз hmi-backend) | Источники, hmi-backend | hydro-calc, hmi-backend, alarm-* | `{tag, ts, value, invalid}` |
| `model_main_{sessionId}` | mod-hist, hmi-backend | hydro-calc, mod-hist | `{tag, ts, value, invalid}` |
| `model_alarm_{sessionId}` | hydro-calc | alarm-service, alarm-view-service, mod-hist | `{tag, ts, value, text, priority, state}` |
| `mod-hist-commands` | mod-hist | hydro-calc | `{sessionId, command, params, ts}` |
| `mod-hist-results` | hydro-calc | mod-hist | `{sessionId, tag, value, ts}` |

## Щупы — точки проверки пачки данных в потоке (§1.4)

| Обозначение | Где | Что ловим |
|---|---|---|
| `SPOT_K1` | Kafka `cspa-main` (только через шлюз hmi-backend) | Входные данные (Press, Ro, Height, Control) |
| `SPOT_K2` | Kafka `model_main_{id}` | Виртуальный поток (вход + выход hydro-calc) |
| `SPOT_K3` | Kafka `model_alarm_{id}` | Алармы, сгенерированные hydro-calc |
| `SPOT_K4` | Kafka `mod-hist-commands` | Команды mod-hist → hydro-calc |
| `SPOT_K5` | Kafka `mod-hist-results` | Подтверждения hydro-calc → mod-hist |
| `SPOT_K6` | Kafka `cspa-main` (алармы, только через шлюз hmi-backend или апи alarm-view-service) | Алармы в оперативном потоке |
| `SPOT_REST` | REST alarm-view-service | Алармы, зафиксированные alarm-view-service |
| `SPOT_WS` | hmi-backend WS V2 | Алармы, видимые оператору |
| `SPOT_CH` | ClickHouse `history` | Исторические данные |
| `SPOT_REDIS` | Redis `session:*` | Состояние сессий, watermark |

## Начальное состояние (§2.3)

1. Все сервисы UP, прогревание завершено.
2. Kafka: топики существуют.
3. PostgreSQL: `sessions` — пусто.
4. Redis: `session:*` — отсутствует.
5. ClickHouse: тестовая история ≥ 24ч для MT1.LU1 (≥ 10 000 сообщений); для HY-SYS-047 дополнительно история MT1.LU2.
6. Конфигурация ТУ1 загружена в data-manager (для HY-SYS-047 — и ТУ2).
7. `api.list()` → пустой массив.
8. `LU.State.Control = 0`, все `Disable = false`.

## Cleanup после каждого сценария (§2.4)

1. Все активные сессии → stop → close.
2. Redis: `session:{id}:*` удалены.
3. PostgreSQL: записи удалены/помечены.
4. Kafka: consumer groups удалены.
5. ClickHouse: тестовые данные удалены.
6. hydro-calculation: буферы очищены.
7. hmi-backend: WS-подписки отключены.
8. `api.list({})` → пусто.
9. `redis.keys("session:*")` → пусто.

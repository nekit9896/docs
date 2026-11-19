---
id: KB-HMI-SVC-001
title: Службы: AppWarmUp, аудит/алармы, диагностика, TagInfoService, ready-состояние
service: hmi-backend
group: services
source: confluence/hmi-backend-descr.md#«Службы (Service Layer)», «Диагностика», «Monitoring / Health-Check», «Активное подключение», «Утилиты»
requires: []
related: [KB-HMI-WS-001, KB-HMI-ERR-001, KB-HMI-CONFIG-001, KB-HMI-REST-QUERY-001]
status: verified
---

# Службы (Service Layer)

## AppWarmUp (прогрев / keep-alive)

Выполняется при старте (`HmiEvoService.start()` → `appWarmUp.warmUp()`),
после завершения — `ready = true`, REST-эндпоинты разблокируются:

| Этап | Действие | Примечание |
|---|---|---|
| 1 | `kafkaProducerWarmUp()` | Периодическая отправка тестовых сообщений в hot topics (ScheduledExecutorService, интервал настраивается) |
| 2 | `websocketWarmUp()` | ReactorNetty WS client → PING, SUBSCRIBE TEST_TAG, PING |
| 3 | `tagSetWarmUp()` | POST `/tag-set` и `/tags-set` со случайным тегом |
| 4 | `tagInfoStoreWarmUp()` | `evo.tagNames(pattern)` + `evo.findTag` для списка тегов |

## AuditFacadeService

1. `POST /user_action` → Grant-Access-Audit (заголовки `X-USER-ID`, `X-USER-IP`)
2. `POST /generateAlarm` → Alarm-Service (если тег `USER_ACTION_TAGNAME` есть в кэше)

Формат алерта:
```json
{"tagName": "<USER_ACTION_TAGNAME>", "timeStamp": <epoch_s>, "value": "Audit",
 "alertClassName": "<USER_ACTION_ALERT_CLASS>",
 "text": "<message>, причина: <cause>, распоряжение: <order>"}
```

## DiagService и эндпоинты диагностики

| Метод / эндпоинт | Описание |
|---|---|
| `getHotlinkSessionsCount()` / `GET /diag/hotlink/count` | Суммарное число WS-сессий (V1 + V2) |
| `getHotlinkDiagList()` / `GET /diag/hotlink/list` | Список сессий: подписки, частота (V1 + V2) |
| `getInstanceName()` / `GET /diag/instance` | `evo-manager.app-id` |

## TagInfoService

Кэш всех тегов с **TTL 5 секунд**:

- `getTagInfoCollection()` — все теги (первый вызов — полное заполнение)
- `patternSearchTags(objectPattern, parameterPattern, types, limit)` — поиск
- `getTagInfoList(tags, muteIfMissing)` — по списку имён (missing → `TagNotFoundException` или warn)
- `getTagMetaDtoList(nameSet)` — метаданные (`TagInfoRichDTO`)
- `getValueFieldName(tag)` — имя JSON-поля значения по типу тега

## HistoryServiceLegacy

Legacy-вычитка из ClickHouse: `tagGetHistoryGroupedByTag(...)` (сгруппированная
по тегам), `tagGetHistoryFlat(...)` (плоский массив); батчи по **10 000** ключей.

## HmiEvoService и ServerReadyRestInterceptor

```
start() → ready=true → appWarmUp.warmUp()
stop()  → логирование
isReady() → ready
```

`ServerReadyRestInterceptor` блокирует REST-эндпоинты (**503**) до
`isReady() = true`. Без блокировки: `/health*`, `/actuator*`. Блокируется: все
методы/классы с `@RequireServerReady` и все `@RestController` (по умолчанию).
Аннотация `@RequireServerReady(message="...", retryAfter=5)` — кастомизация
сообщения и заголовка `Retry-After`.

## Monitoring (Spring Boot Actuator)

| Эндпоинт | Ответ |
|---|---|
| `GET /actuator/health` | `UP` / `DOWN` / `OUT_OF_SERVICE` |
| `GET /actuator/metrics` | Метрики JVM/системы |
| `GET /actuator/prometheus` | Выгрузка Prometheus |

## Утилиты

| Класс | Назначение |
|---|---|
| `JsonUtils` | Конвертация коллекций → `JsonArray` |
| `LimitedMap` | LRU-Map с ограничением размера (автосброс старейших) |
| `RequestUtils` | IP клиента, identity пользователя из заголовков (см. KB-HMI-ERR-001) |
| `TagValueUtils` | Сравнение значений, `isPlotable`, конвертация TagValue ↔ HmiMsg |
| `TickCollector` | Счётчик тиков за окно времени (статистика/мониторинг) |
| `PingPongLogger` | Lazy-логирование PING/PONG (только DEBUG) |
| `RequireServerReady` | Аннотация: блокировка до готовности |
---
id: KB-HMI-WS-001
title: WebSocket V1 (/hotlink) и V2 (/v2/hotlink): команды, кадры, обслуживание сессий
service: hmi-backend
group: api
source: confluence/hmi-backend-descr.md#«WebSocket»
requires: [KB-HMI-STREAM-001]
related: [KB-HMI-SVC-001, KB-HMI-CONFIG-001, KB-HMI-ERR-001, KB-HMI-REST-VAL-001]
status: verified
---

# WebSocket

## V1: `ws://<host>:<port>/hotlink` (текстовые строки)

| Команда | Формат | Описание |
|---|---|---|
| `SUBSCRIBE` | `SUBSCRIBE tag1,tag2` или `SUBSCRIBE tag1 tag2` | Подписка: в ответ последние значения, далее агрегация в окне **1000 мс** |
| `UNSUBSCRIBE` | `UNSUBSCRIBE tag1,tag2` | Отписка |
| `PING` | `PING` | Heartbeat → `PONG` |

- Ответ: `HmiMsg.BatchedTagValueMsg` (JSON-представление Protobuf); изменения —
  те же, агрегированные в окне 1000 мс.
- Особенности V1: трассировка отсутствует, авторизация не передаётся, только
  подписки + PING; сессии — `HotlinkWebSocketHandler` + `HotlinkWaitValueSession`
  (ожидание значений для `tag-set-and-wait`).

## V2: `ws://<host>:<port>/v2/hotlink` (JSON-фреймы `CommandDto`)

Кадр: `{"cmd": "...", "id": "req-001", "args": [...], "headers": {...}}`

| Поле | Тип | Обязательность |
|---|---|---|
| `cmd` | string | required |
| `id` | string | required (трассировка) |
| `args` | array / object / null | зависит от команды |
| `headers` | object | для команд с авторизацией (напр. `X-USER-ALLOW-PATTERNS`, `X-USER-FULLNAME`) |

Ответы: `SUB_ANSWER` (пакет значений подписки), `CALL_ANSWER` (TAG_GET, TAG_FIND,
TAG_NAMES, OBJECT_TYPES), `CALL_ERROR`, `PONG`.

### Команды

**Подписки:**

| Команда | Args | Headers | Примечание |
|---|---|---|---|
| `SUBSCRIBE` | `["tag1","tag2"]` | `X-USER-GET-ALLOW-PATTERNS` | Буферизация `sample-time` (default **50 мс**), отправка пакетом |
| `UNSUBSCRIBE` | `["tag1","tag2"]` | — | — |
| `UNSUBSCRIBE_ALL` | `null` | — | Сброс всех подписок сессии |

**Чтение/запись/поиск:**

| Команда | Args | Headers |
|---|---|---|
| `TAG_GET` | `["SO.ME.TAG1"]` | `X-USER-GET-ALLOW-PATTERNS` |
| `TAG_SET` | `[{"tag":"...","data":{"value":"123"}}]` | `X-USER-ALLOW-PATTERNS`, `X-USER-FULLNAME` |
| `TAG_FIND` | `["SO.ME.TAG1"]` | — |
| `TAG_NAMES` | `{"objectPattern":".*","parameterPattern":".*","types":["NPS"],"limit":100,"sorted":true}` | — |
| `OBJECT_TYPES` | `{"typePattern":".*","sorted":true}` | — |

**Плеер истории:**

| Команда | Args |
|---|---|
| `SWITCH` | `{"target":"HISTORY","start":...,"finish":...,"millisPerTick":1000}` или `{"target":"LIVE"}` |
| `SEEK` | `1706593000000` (timestamp, мс) |
| `SET_MILLIS_PER_TICK` | `1000` |
| `PLAY` | `null` |
| `STOP` | `null` |

**Служебные:** `PING` `{"id":"ping-001"}` → `PONG` с тем же `id`.

### Архитектура V2

```
HotlinkWebSocketHandlerV2
├── HotlinkWebSocketHandlerBase (общая логика: сессии, stale/wake)
├── HotlinkService (управление сессиями)
├── HotlinkSession / HotlinkSessionBase (состояние сессии)
├── HotlinkWaitValueSession (ожидание значений — V1)
├── HeadersHandshakeInterceptor (захват заголовков при handshake)
├── HotlinkMessageLogger (логирование сообщений)
└── HotlinkSessionV2Modelling / HotlinkWebSocketHandlerV2Modelling /
    HotlinkWebSocketHandlerV2Routed (моделирование)
```

## Обслуживание сессий (Minuteman)

Каждые **30 секунд** для V1 и V2:
1. `wakeUpStaleSessions()` — пробуждение неактивных (если прошло `clientside-wake-time-s`)
2. `killStaleSessions()` — закрытие неактивных (если прошло `clientside-stale-time-s`)
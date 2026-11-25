---
id: KB-HMI-WS-001
title: WebSocket V1 (/hotlink) и V2 (/v2/hotlink): команды, кадры, обслуживание сессий
service: hmi-backend
group: api
source: real_repo_dump/hmi-backend:L8630-L8680 (hotlink/dto/Command.java, CommandDto.java); L7445-L8083 (HotlinkSessionV2.java); L6364-L6418 (HeadersHandshakeInterceptor.java); L1427-L1476 (configuration/HotlinkWebSocketConfig.java)
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

Кадр команды (`CommandDto`): `{"cmd": "...", "id": "req-001", "args": [...], "headers": {...}}`

| Поле | Тип | Обязательность |
|---|---|---|
| `cmd` | string | required |
| `id` | string | optional (трассировка; страница `tag-monitor.html` шлёт без `id`) |
| `args` | array / object / null | зависит от команды |
| `headers` | object | для команд с авторизацией (напр. `X-USER-ALLOW-PATTERNS`, `X-USER-FULLNAME`) |

**Кадры ответов** (`AnswerDto`): `{"id": ..., "message_type": "...", "message": ...}`
(+ служебные кадры без `id`):

| message_type | Формат | Когда |
|---|---|---|
| `SUB_ANSWER` | `{"message_type":"SUB_ANSWER","message":[...]}` | Пакет значений подписки (агрегация `sample-time`) |
| `CALL_ANSWER` | `{"id":"...","message_type":"CALL_ANSWER","message":...}` | Ответ на `TAG_GET`/`TAG_FIND`/`TAG_NAMES`/`OBJECT_TYPES`/`TAG_SET` |
| `CALL_ERROR` | `{"id":"...","message_type":"CALL_ERROR","message":...}` | Ошибка синхронного вызова |
| `pong` | `{"message_type":"pong","pingId":<id или null>,"hmiToSessionTime":<ms>}` | Ответ на `PING` |
| `time` | `{"message_type":"time","stream_time_s":<s>,"current_time_s":<s>,"last_tag_data_sent_s":<s>,"stream_state":{"type":"live","id":"<uuid>"}}` | Серверные часы, интервал `clock-message-interval-s` (default 1 с) |
| `error` | `{"message_type":"error","error_message":...}` | Ошибка уровня сессии |

> `CALL_ANSWER`/`CALL_ERROR` — **message_type кадров-ответов**, не команды:
> в `Command` enum (L8635-L8651) команды `CALL_ANSWER` нет (расхождение G44).

### Handshake и авторизация (D47, G45)

Идентификация при рукопожатии — **и query-параметрами URL, и HTTP-заголовками**
одновременно: `HeadersHandshakeInterceptor` (L6364-L6418) кладёт в атрибуты
сессии `IP`, `x-user-fullname` (`RequestUtils.getAnyUserIdentity`, L11680-L11687:
заголовки `X-USER-LOGIN` → `X-USER-FULLNAME` → `x-user-fullname` → `X-USER-ID`,
фолбэк — query `x-user-fullname` с двойной декодификацией) и `queryParameterMap`.
Query-параметры `X-USER-*` мержатся с `headers` кадров (`HotlinkSessionBase`,
L7120-L7125) и действуют как умолчания для команд сессии. Образец подключения —
`tag-monitor.html` (L15045-L15055): `wss://<host>/v2/hotlink?x-user-fullname=
<double-url-encoded>&X-USER-ALLOW-PATTERNS=<json>` (+ опционально `x-user-ip`,
`X-USER-FORBIDDEN-PATTERNS`, `modelSessionId`). Пока `!hmiEvoService.isReady()` —
отказ 503.

### Команды

Полный состав `Command` enum — 14 команд (канон **D48**: клиент `sdku-test-tools`
реализует весь enum; `SWITCH {"target":"LIVE"}` — обязательный шаг инициализации
сессии, в т.ч. после реконнекта; G42 закрыт).

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
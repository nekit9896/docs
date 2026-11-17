## Общее описание

**hmi-backend** — сервис HMI в составе EVOSCADA на базе evo-manager. Обеспечивает данные для расчёта отображения элементов экранных форм (ЭФ), а также получение/отправку команд телерегулирования и телеуправления. Выступает связующим интерфейсом между клиентскими приложениями (ЭФ, тренды) и внутренними сервисами SCADA.

### Функционал

| Модуль | Описание                                                                                                             |
|--------|----------------------------------------------------------------------------------------------------------------------|
| **WebSocket V1** | Текстовые подписки на сигналы, обмен в реальном времени (окно агрегации 1000 мс)                                     |
| **WebSocket V2** | JSON-фреймы: подписки, вызовы (TAG_GET/SET/FIND/NAMES/OBJECT_TYPES), плеер истории, PING/PONG (окно агрегации 50 мс) |
| **REST** | Получение/запись значений тегов, поиск, метаданные, история                                                          |
| **Метаданные** | Чтение из кеша (TTL 5 с), создание/удаление объектов с маршрутизацией                                                |
| **Аудит/алармы** | Запись действий → Grant-Access-Audit, Alarm-Service                                                                  |
| **История** | Вычитывание из ClickHouse (REST, батчи по 10 000 ключей), плеер истории (WebSocket)                                  |
| **Data Stream** | Стримовая обработка: значения тегов, алармы, история (TimelineBucket)                                                |
| **Modelling** | Моделирование сессий, маршрутизация сообщений, mock-провайдеры                                                       |
| **Прогревание** | Warm-up Kafka producer, WebSocket, tag-set, tag-info store при старте                                                |

### Смежные компоненты

| Компонент | Роль |
|-----------|------|
| **Kafka** | Текущие данные/команды через топики; источник метаданных (взаимозаменяемо с Redis) |
| **Redis** | Кеш информационной модели, метаданные (взаимозаменяемо с Kafka) |
| **ClickHouse** | Исторические данные (JDBC) |
| **Data-Manager** | Интерфейс ИМ и сигналов (REST) |
| **Alarm-Service** | События и алармы (REST) |
| **Grant-Access-Audit** | Аудит действий оператора (REST) |
| **Schema Registry** | Confluent Schema Registry для Protobuf сериализации |

### Инструменты

- **Swagger UI:** `http(s)://<host>:<port>/swagger-ui/index.html`
- **Tag Monitor:** `http(s)://<host>:<port>/tag-monitor.html` — поиск/подписка на теги, ручная запись значений, плеер истории, выборка архивов из ClickHouse

---

## Тег

Уникальный адрес в адресном пространстве EVOSCADA. Сигналы, параметры, команды, коэффициенты — всё это значения тегов. Каждый тег имеет `value` и `attributes` (метаданные: алармы, шкалы, ЕИ, принадлежность к объекту).

### Типы значений

| Тип | Protobuf field | Plotable |
|-----|---------------|----------|
| BOOL | `boolVar` | ✅ |
| INT | `intVar` | ✅ |
| LONG | `longVar` | ✅ |
| FLOAT | `floatVar` | ✅ |
| DOUBLE | `doubleVar` | ✅ |
| STRING | `stringVar` | ❌ |
| BYTES | `bytesVar` | ❌ |
| TIME | `timeVar` | ❌ |
| DYN_BOOL | `dynBoolVar` | ❌ |
| DYN_INT | `dynIntVar` | ❌ |
| DYN_LONG | `dynLongVar` | ❌ |
| DYN_FLOAT | `dynFloatVar` | ❌ |
| DYN_DOUBLE | `dynDoubleVar` | ❌ |
| DYN_STRING | `dynStringVar` | ❌ |
| DYN_TIME | `dynTimeVar` | ❌ |
| DYN_BYTES | `dynBytesVar` | ❌ |

> **Важно:** При записи значения (`TAG_SET`) сервис валидирует соответствие типа тега и типа значения через `ProtoValidator.validate()`. Несоответствие → `ValueConversionException` (HTTP 400).

### Версии API

| Версия | Префикс | Формат значения | Статус |
|--------|---------|----------------|--------|
| **V1** | `/` | Вложенная типизация: `"value": {"stringVar": "..."}` | Устаревшая (активна для legacy-эндпоинтов) |
| **V2** | `/v2/` | Плоские JSON-примитивы: `"value": "..."` | Актуальная |

---

## Protobuf-схемы

Базовые сообщения для сериализации данных в Kafka.

### HmiMsg

```protobuf
message TagValueMsg {
  string tag = 1;
  ValueMsg value = 2;
  uint64 ts = 3;
}

message BatchedTagValueMsg {
  repeated TagValueMsg tagValueBatch = 1;
}
```

### TnMsg.ValueMsg

```protobuf
message ValueMsg {
    Key key = 1;           // опционально
    bool invalid = 2;
    int64 quality = 3;     // опционально
    repeated uint64 chainTimeStamp = 4;  // опционально

    oneof value {
        bool boolVar = 5;
        int32 intVar = 6;
        int64 longVar = 7;
        float floatVar = 8;
        double doubleVar = 9;
        string stringVar = 10;
        bytes bytesVar = 11;
        DynBoolVar dynBoolVar = 12;
        DynIntVar dynIntVar = 13;
        DynLongVar dynLongVar = 14;
        DynFloatVar dynFloatVar = 15;
        DynDoubleVar dynDoubleVar = 16;
        DynStringVar dynStringVar = 17;
        DynBytesVar dynBytesVar = 18;
        TimeVar timeVar = 19;
        DynTimeVar dynTimeVar = 20;
    };
}
```

### Dynamic / Time types

```protobuf
message DynBoolVar  { repeated bool values = 1; }
message DynIntVar   { repeated int32 values = 1; }
message DynLongVar  { repeated int64 values = 1; }
message DynFloatVar { repeated float values = 1; }
message DynDoubleVar{ repeated double values = 1; }
message DynStringVar{ repeated string values = 1; }
message DynBytesVar { repeated bytes values = 1; }
message TimeVar     { int64 millis = 1; }
message DynTimeVar  { repeated TimeVar values = 1; }
```

### Конвертация (ProtoConverter)

| Метод | Направление | Примечание |
|-------|-------------|------------|
| `toJson(MessageOrBuilder)` | Protobuf → JSON | Использует `JsonFormat.printer()`. Ошибка → `ValueConversionException` |
| `toMsg(String, Message.Builder)` | JSON → Protobuf | Использует `JsonFormat.parser().merge()`. Ошибка → `ValueConversionException` |

---

## REST: текущие значения тегов

### 1. `GET /v2/tag-get`

| Параметр | Тип | Обязательность | Примечание |
|----------|-----|----------------|------------|
| `tagName` | query | required | — |
| `X-USER-GET-ALLOW-PATTERNS` | header | optional | default `[".*"]`, JSON-массив regex |
| `X-USER-GET-FORBIDDEN-PATTERNS` | header | optional | JSON-массив regex, приоритет над allow |
| `X-USER-FULLNAME` | header | optional | — |

**Ответ:**
```json
{"tag":"MN.TU.TAGNAME..,","data":{"value":"some value","invalid":false,"ts":123456789,"ts2":123456789}}
```

> **V1** (`GET /tag-get`): вложенная типизация значения (`HmiMsg.TagValueMsg`).

### 2. `GET|POST /v2/tags-get`

- **GET:** query `tagNames` (массив строк)
- **POST:** body — JSON-массив адресов

Заголовки те же, что в п.1.

**Ответ:** массив объектов той же структуры, что в п.1.

> **V1** (`GET|POST /tags-get`): обёртка `BatchedTagValueMsg` → `{"tagValueBatch":[...]}`.

### 3. `POST /v2/tag-set`

| Заголовок | Обязательность | Примечание |
|-----------|----------------|------------|
| `X-USER-FULLNAME` | **required** | Идентификация, сохраняется в Grant-Access-Audit |
| `X-USER-IP` | optional | IP для логов аудита/алармов |
| `X-USER-ALLOW-PATTERNS` | **required** | JSON-массив regex |
| `X-USER-FORBIDDEN-PATTERNS` | optional | JSON-массив regex |

**Body:**
```json
{"tag":"MN.TU.TAGNAME","data":{"value":"new value","invalid":false,"ts":123456789}}
```

**Ответ:** `200 OK`. При `use-sync-set=true` — после подтверждения применения.

> **Валидация:** тип значения проверяется против типа тега (`ProtoValidator`). Несоответствие → `400` + `ValueConversionException`.

> **V1** (`POST /tag-set`): body — `HmiMsg.TagValueMsg`.

### 4. `POST /v2/tags-set`

Body: массив объектов `TagSetRequest`. Заголовки аудита как в п.3. Ответ `200 OK`.

> **V1** (`POST /tags-set`): body — `BatchedTagValueMsg`.

### 5. `POST /tag-set-and-wait` **(только V1)**

Запись в один тег + блокировка HTTP-ответа до появления ожидаемого значения на связанном теге. Body: `TagSetAndWaitDTO`. В V2 отсутствует (ожидание вынесено на WebSocket).

---

## REST: поиск и навигация

### 6. `GET /v2/tag-names`

Поиск тегов по паттернам с фильтрацией по типам.

| Параметр | Тип | Примечание |
|----------|-----|------------|
| `objectPattern` | query | regex для имени объекта |
| `parameterPattern` | query | regex для имени параметра |
| `types` | query (массив) | Фильтр по типам (NPS, NCS и т.д.) |
| `skipFolders` | query | Пропускать папки |
| `limit` | query | Ограничение результатов |

**Ответ:** `array of string` (имена тегов)

### 7. `GET /object-types`

Получить список типов объектов.

| Параметр | Тип | Примечание |
|----------|-----|------------|
| `pattern` | query | regex |

**Ответ:** `array of string`

### 8. `GET /object-names`

Получить список объектов.

| Параметр | Тип | Примечание |
|----------|-----|------------|
| `pattern` | query | regex |
| `type` | query (optional) | Имя object-type |

**Ответ:** `array of string`

### 9. `GET /tag-names` **(V1, legacy)**

Получить список тегов по regex.

| Параметр | Тип | Примечание |
|----------|-----|------------|
| `pattern` | query | regex |
| `type` | query (optional) | Имя object-type |

**Ответ:** `array of string`

> V1 также имеет `/tag-names-labels`, `POST /get-tags-meta` — устаревшие, без кэширования/фильтрации/лимитов.

---

## REST: история (ClickHouse)

### 10. `POST /v2/tags-get-history`

**Body:**
```json
{
  "startTime": 1706592000000,
  "endTime": 1706595600000,
  "tags": ["SO.ME.TAG1"],
  "limit": 1000,
  "offset": 0,
  "returnBounds": false
}
```

**Ответ:** объект с ключами-тегами, значения — массивы записей `{ts, ts2, quality, invalid, value}`.

> **Внутренне:** запрос делится на батчи по **10 000** ключей (ограничение ClickHouse на размер SQL: 256 KiB).

> **V1** (`POST /tags-get-history`): легаси-сервис с `timeBucketWidth` (агрегация по интервалам), V2 — прямой запрос из CH.

### 11. `POST /v2/tags-get-history-iso`

Аналог п.10, временные метки в ISO8601.

**Body:** `HistoryISORequestDTO` — структура аналогична, но `startTime`/`endTime` — строки в формате ISO8601.

**Ответ:** `RecordValueISO` — значения с ISO-датами.

### 12. `POST /tags-get-history-flat` **(V1, активен во всех версиях)**

Линейный массив архивных записей со сжатыми ключами JSON.

**Body:** аналогичен п.10 + `timeBucketWidth` (опционально).

**Ответ:** `array of HistoryRecordShortNameDTO`.

---

## REST: метаданные (кеш core-meta-data-store)

### Чтение

| # | Эндпоинт | Параметры |
|---|----------|-----------|
| 1 | `GET /v1/configurator/project` | `page`, `size` |
| 2 | `GET /v1/configurator/object-type` | `projectId`, `page`, `size` |
| 3 | `GET /v1/configurator/object` | `objectTypeId`, `projectId`, `parentId`, `sort`, `page`, `size` |
| 4 | `GET /v1/configurator/object/{parentId}/children` | `projectId` |
| 5 | `GET /v1/area_attr` | `project` |
| 6 | `GET /v1/general_attr/{object}` | path `object` |
| 7 | `GET /v2/tag-names` | `objectPattern`, `parameterPattern`, `types[]`, `skipFolders`, `limit` |

### Изменение

| # | Эндпоинт | Описание |
|---|----------|----------|
| 8 | `POST /object` | Создание объекта + автопрописывание маршрутов (topic-route) |
| 9 | `DELETE /object/{object_name}` | Каскадное удаление |

#### Детали создания объекта (`POST /object`)

Алгоритм `TagInfoEditService.createObjectWithRouting`:

1. Проверка конфигурации (Data-Manager URL задан)
2. Получение маршрутов из `TopicRouteConfig` по имени объекта и типу
3. `POST /v1/object` в Data-Manager
4. Если объект уже существует (400):
    - Проверка равенства DTO
    - Если равен — дописывание недостающих маршрутов
    - Если не равен — `BadRequestException`
5. Для каждого маршрута: `POST /v1/route_attr`
6. Проверка конфликтов маршрутов

#### Вариант с ожиданием (`createObjectWithRoutingAndWaitForApply`)

После создания ожидает появления объекта в локальном кэше (до 5 сек, интервал 500 мс).

---

## REST: сессии (Modelling)

### 13. `SessionsController`

Контроллер для управления сессиями моделирования.

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/sessions` | Регистрация сессии (`SessionToServiceDTO`) |
| DELETE | `/sessions/{sessionId}` | Удаление сессии |

> Используется в контексте модуля Modelling для маршрутизации сообщений между сервисами.

---

## WebSocket

### V1: `ws://<host>:<port>/hotlink`

**Формат:** текстовые строки.

#### Команды

| Команда | Формат | Описание |
|---------|--------|----------|
| `SUBSCRIBE` | `SUBSCRIBE tag1,tag2` или `SUBSCRIBE tag1 tag2` | Подписка. В ответ — последние значения, далее агрегация в окне **1000 мс** |
| `UNSUBSCRIBE` | `UNSUBSCRIBE tag1,tag2` | Отписка |
| `PING` | `PING` | Heartbeat → `PONG` |

#### Примеры

```
SUBSCRIBE test_1.Value test_2.Value test_3.Value
SUBSCRIBE test_1.Value,test_2.Value,test_3.Value
```

#### Формат ответа

- Подписка: `HmiMsg.BatchedTagValueMsg` (JSON-представление Protobuf)
- Изменения: те же, агрегированные в окне 1000 мс

#### Особенности V1

- Трассировка сообщений отсутствует
- Авторизация не передаётся
- Только подписки + PING
- Сессии обрабатываются `HotlinkWebSocketHandler` + `HotlinkWaitValueSession`

---

### V2: `ws://<host>:<port>/v2/hotlink`

**Формат:** JSON-фреймы (`CommandDto`).

#### Структура кадра

```json
{
  "cmd": "SUBSCRIBE",
  "id": "req-001",
  "args": ["Station.Tag1.Value"],
  "headers": {
    "X-USER-ALLOW-PATTERNS": "[\".*\"]",
    "X-USER-FULLNAME": "Иванов И.И."
  }
}
```

| Поле | Тип | Обязательность |
|------|-----|----------------|
| `cmd` | string | required |
| `id` | string | required (трассировка) |
| `args` | array / object / null | зависит от команды |
| `headers` | object | для команд с авторизацией |

#### Ответы

| Тип | Описание |
|-----|----------|
| `SUB_ANSWER` | Пакет значений подписки |
| `CALL_ANSWER` | Ответ на вызов (TAG_GET, TAG_FIND, TAG_NAMES, OBJECT_TYPES) |
| `CALL_ERROR` | Ошибка выполнения |
| `PONG` | Ответ на PING |

#### Команды

**Подписки:**

| Команда | Args | Headers | Примечание |
|---------|------|---------|------------|
| `SUBSCRIBE` | `["tag1","tag2"]` | `X-USER-GET-ALLOW-PATTERNS` | Буферизация `sample-time` (default **50 мс**), отправка пакетом |
| `UNSUBSCRIBE` | `["tag1","tag2"]` | — | — |
| `UNSUBSCRIBE_ALL` | `null` | — | Сброс всех подписок сессии |

**Чтение/запись/поиск:**

| Команда | Args | Headers |
|---------|------|---------|
| `TAG_GET` | `["SO.ME.TAG1"]` | `X-USER-GET-ALLOW-PATTERNS` |
| `TAG_SET` | `[{"tag":"...","data":{"value":"123"}}]` | `X-USER-ALLOW-PATTERNS`, `X-USER-FULLNAME` |
| `TAG_FIND` | `["SO.ME.TAG1"]` | — |
| `TAG_NAMES` | `{"objectPattern":".*","parameterPattern":".*","types":["NPS"],"limit":100,"sorted":true}` | — |
| `OBJECT_TYPES` | `{"typePattern":".*","sorted":true}` | — |

**Плеер истории:**

| Команда | Args |
|---------|------|
| `SWITCH` | `{"target":"HISTORY","start":...,"finish":...,"millisPerTick":1000}` или `{"target":"LIVE"}` |
| `SEEK` | `1706593000000` (timestamp, мс) |
| `SET_MILLIS_PER_TICK` | `1000` |
| `PLAY` | `null` |
| `STOP` | `null` |

**Служебные:**

| Команда | Args |
|---------|------|
| `PING` | `{"id":"ping-001"}` → ответ `PONG` с тем же `id` |

#### Архитектура WebSocket V2

```
HotlinkWebSocketHandlerV2
├── HotlinkWebSocketHandlerBase (общая логика: сессии, stale/wake)
├── HotlinkService (управление сессиями)
├── HotlinkSession / HotlinkSessionBase (состояние сессии)
├── HotlinkWaitValueSession (ожидание значений — V1)
├── HeadersHandshakeInterceptor (захват заголовков при handshake)
├── HotlinkMessageLogger (логирование сообщений)
└── HotlinkSessionV2Modelling / HotlinkWebSocketHandlerV2Modelling / HotlinkWebSocketHandlerV2Routed (моделирование)
```

#### Обслуживание сессий (Minuteman)

Каждые **30 секунд** для V1 и V2:
1. `wakeUpStaleSessions()` — пробуждение неактивных сессий (если прошло `clientside-wake-time-s`)
2. `killStaleSessions()` — закрытие неактивных сессий (если прошло `clientside-stale-time-s`)

---

## Data Stream

Стримовый слой обработки данных в реальном времени.

### Компоненты

| Класс | Роль |
|-------|------|
| **DataStreamManager** | Оркестратор: управляет жизненным циклом провайдеров и хендлеров |
| **DataStreamProvider** (интерфейс) | Источник стримов (Kafka, mock, model) |
| **HistoryDataStreamProvider** | Провайдер для стримов истории (плеер) |
| **TagValueStreamHandler** | Обработка входящих значений тегов: буферизация, валидация, доставка подписчикам |
| **TagAlarmStreamHandler** | Обработка алармов: ретрансляция подписчикам |
| **HistoryStreamHandler** | Обработка стримов истории для плеера |
| **TimelineBucket** | Временное окно агрегации: собирает значения за период, отправляет пакетом |

### Поток данных (V2 подписка)

```
Kafka topic → DataStreamManager → TagValueStreamHandler
                                         │
                                         ├── ProtoValidator (валидация типа)
                                         ├── TimelineBucket (буфер 50 мс)
                                         └── HotlinkSession → WebSocket V2 (SUB_ANSWER)
```

### Поток данных (плеер истории)

```
ClickHouse → HistoryDataStreamProvider → HistoryStreamHandler
                                                  │
                                                  └── HotlinkSession → WebSocket V2 (SUB_ANSWER)
```

---

## Modelling

Модуль для моделирования/маршрутизации сообщений между сервисами.

### Компоненты

| Класс | Роль |
|-------|------|
| **EvoCoreDelegated** | Делегирование вызовов в Evo (ядро) |
| **ModelEvoApiManager** | Менеджер API для моделирования |
| **SessionManager** | Управление сессиями моделирования |
| **ModellingKafkaTnMsgSender** | Отправка TnMsg в Kafka (маршрутизация) |
| **ModelDataStreamProvider** | Провайдер данных для моделирования |
| **MockDataStreamProvider** | Mock-провайдер (тестирование) |
| **HotlinkSessionV2Modelling** | Сессия V2 для моделирования |
| **HotlinkWebSocketHandlerV2Modelling** | WebSocket handler для моделирования |
| **HotlinkWebSocketHandlerV2Routed** | Маршрутизированный handler V2 |

### Назначение

Разделяет нагрузку между инстансами: каждый инстанс обслуживает свою порцию сессий. Маршрутизация по `SessionToServiceDTO`.

---

## Службы (Service Layer)

### AppWarmUp

Прогревание приложения при старте. Выполняет:

| Прогрев | Описание |
|---------|----------|
| `kafkaProducerWarmUp` | Периодическая отправка тестовых сообщений в hot topics (интервал настраивается) |
| `websocketWarmUp` | Подключение к WS, отправка PING / SUBSCRIBE TEST_TAG / PING |
| `tagSetWarmUp` | POST `/tag-set` и `/tags-set` со случайным тегом |
| `tagInfoStoreWarmUp` | `evo.tagNames(pattern)` + `evo.findTag` для списка тегов |

> Вызывается из `HmiEvoService.start()` после инициализации Spring.

### AuditFacadeService

Фасад для аудита и алертов:

1. `POST /user_action` → Grant-Access-Audit (заголовки: `X-USER-ID`, `X-USER-IP`)
2. `POST /generateAlarm` → Alarm-Service (если тег `USER_ACTION_TAGNAME` существует в кэше)

**Формат алерта:**
```json
{
  "tagName": "<USER_ACTION_TAGNAME>",
  "timeStamp": <epoch_s>,
  "value": "Audit",
  "alertClassName": "<USER_ACTION_ALERT_CLASS>",
  "text": "<message>, причина: <cause>, распоряжение: <order>"
}
```

### DiagService

Диагностика:

| Метод | Описание |
|-------|----------|
| `getHotlinkSessionsCount()` | Суммарное число WS-сессий (V1 + V2) |
| `getHotlinkDiagList()` | Список сессий: подписки, частота (V1 + V2) |
| `getInstanceName()` | `evo-manager.app-id` |

### TagInfoService

Кэш всех тегов с **TTL 5 секунд**:

- `getTagInfoCollection()` — все теги (первый вызов — полное заполнение)
- `patternSearchTags(objectPattern, parameterPattern, types, limit)` — поиск
- `getTagInfoList(tags, muteIfMissing)` — по списку имён (missing → `TagNotFoundException` или warn)
- `getTagMetaDtoList(nameSet)` — метаданные (`TagInfoRichDTO`)
- `getValueFieldName(tag)` — имя JSON-поля значения по типу тега

### HistoryServiceLegacy

Legacy-вычитка из ClickHouse:

- `tagGetHistoryGroupedByTag(...)` — сгруппированная по тегам
- `tagGetHistoryFlat(...)` — плоский массив
- **Батчи:** по 10 000 ключей на запрос (ограничение CH)

### HmiEvoService

Управление жизненным циклом:

```
start() → ready=true → appWarmUp.warmUp()
stop()  → логирование
isReady() → ready
```

### ServerReadyRestInterceptor

Блокирует REST-эндпоинты (503) до `HmiEvoService.isReady() = true`.

**Разрешено без блокировки:**
- `/health*`
- `/actuator*`

**Блокируется:**
- Все методы/классы с `@RequireServerReady`
- Все `@RestController` (по умолчанию)

> Аннотация `@RequireServerReady(message="...", retryAfter=5)` — кастомизация сообщения и `Retry-After` заголовка.

### TagInfoEditService

Создание/удаление объектов (см. раздел «Метаданные → Изменение»).

### TopicRouteConfig

Конфигурация маршрутизации (см. раздел «Topic-Route»).

### Minuteman

Периодическое обслуживание WS-сессий (каждые 30 с):

```
perform() {
  v1.wakeUpStaleSessions()
  v2.wakeUpStaleSessions()
  v1.killStaleSessions()
  v2.killStaleSessions()
}
```

---

## Обработка ошибок

### Иерархия исключений

```
ApplicationLogicException (базовое)
├── BadRequestException          → 400
├── NotFoundException            → 404
├── ForbiddenException           → 403
├── TagNotFoundException         → 404 (тег не найден)
├── TagNotAvailable              → 503 (тег временно недоступен)
├── TagSetException              → 400 (ошибка записи)
├── ValueConversionException     → 400 (несоответствие типа)
└── WebClientErrorException      → 502 (ошибка внешнего сервиса)
```

### Обработчики

| Обработчик | Роль |
|------------|------|
| `ControllerErrorsHandler` | Обработка исключений контроллеров → JSON `ErrorResponseApi` |
| `ControllerDefaultErrorsHandler` | Дефолтная обработка (fallback) |

### Формат ошибки

```json
{
  "message": "Описание ошибки",
  "tag": "SO.ME.TAG",       // для TagErrorMessage
  "timestamp": 123456789
}
```

---

## Фильтры и инфраструктура

### RequestInfoFilter

- Извлекает IP клиента (через `RequestUtils.getClientIpAddr`)
- Извлекает identity пользователя (через `RequestUtils.getAnyUserIdentity`)
- Логгирует информацию о запросе

### MultiReadHttpServletRequest

Обёртка над `HttpServletRequest` для многократного чтения body (необходимо для фильтра + контроллера).

### KafkaSender

Отправка сообщений в Kafka:
- Обычные топики
- Compact-топики (для метаданных)

---

## Диагностика

| Эндпоинт | Ответ |
|----------|-------|
| `GET /diag/instance` | `evo-manager.app-id` |
| `GET /diag/hotlink/count` | Число WS-сессий (V1 + V2) |
| `GET /diag/hotlink/list` | Список сессий: подписки, частота (V1 + V2) |

---

## Monitoring / Health-Check (Spring Boot Actuator)

| Эндпоинт | Ответ |
|----------|-------|
| `GET /actuator/health` | `UP` / `DOWN` / `OUT_OF_SERVICE` |
| `GET /actuator/metrics` | Метрики JVM/системы |
| `GET /actuator/prometheus` | Выгрузка в формате Prometheus |

> REST бизнес-эндпоинты возвращают **503** до завершения инициализации, перехватчик `ServerReadyRestInterceptor`.

---

## Авторизация (HTTP-заголовки)

Контроль на уровне бизнес-логики.

| Заголовок | Обязательность | Описание |
|-----------|----------------|----------|
| `X-USER-FULLNAME` | Required при записи | Идентификация, сохраняется в Grant-Access-Audit |
| `X-USER-ID` | Optional | ID пользователя (для аудита) |
| `X-USER-IP` | Optional | IP для логов аудита/алармов |
| `X-USER-ALLOW-PATTERNS` | **Required** при записи | JSON-массив regex, разрешающий доступ |
| `X-USER-GET-ALLOW-PATTERNS` | **Required** при чтении | JSON-массив regex, разрешающий чтение |
| `X-USER-FORBIDDEN-PATTERNS` | Optional | Чёрный список, **приоритет над allow** |
| `X-USER-GET-FORBIDDEN-PATTERNS` | Optional | Чёрный список для чтения |
| `X-USER-LOGIN` | Optional | Альтернативный заголовок identity |

> **WebSocket V2:** параметры авторизации передаются в поле `headers` внутри JSON-кадра.

> **RequestUtils** проверяет заголовки в порядке: `X-USER-LOGIN` → `X-USER-FULLNAME` → `x-user-fullname` → `X-USER-ID`. Для IP: `X-Forwarded-For` → `Proxy-Client-IP` → `WL-Proxy-Client-IP` → `HTTP_CLIENT_IP` → `HTTP_X_FORWARDED_FOR` → `request.getRemoteAddr()`.

---

## Конфигурация

### Приложение

| Переменная | Default | Описание |
|------------|---------|----------|
| `WEB_SERVER_PORT` | `8080` | TCP порт |
| `SERVER_ALLOWED_ORIGINS` | `*` | CORS |
| `WEB_CLIENT_TIMEOUT` / `NETWORK_TIMEOUT_MS` | `5000` | Таймаут HTTP-запросов к внешним сервисам (мс) |
| `CSPA_TOPICS` | — | Топик на чтение из Kafka |

### evo-manager / Kafka

| Переменная | Default | Описание |
|------------|---------|----------|
| `EVO_MANAGER_APP_ID` | — | ID сервиса (шаблон `{имя}_{номер}`) |
| `EVO_MANAGER_HOT_TOPICS` | — | Hot-топики |
| `KAFKA_APPLICATION_ID_CONFIG` | `cspa-hmi-backend-1` | Group ID потребителя |
| `BOOTSTRAP_SERVERS_CONFIG` | — | Адресы нод Kafka |
| `SCHEMA_REGISTRY_URL_CONFIG` | — | Confluent Schema Registry URL |
| `KAFKA_ENABLE_SSL` | `false` | SSL для Kafka |
| `KAFKA_KEYSTORE_LOCATION` | — | KeyStore для Kafka SSL |
| `KAFKA_KEYSTORE_PASSWORD` | — | Пароль к KeyStore |
| `KAFKA_TRUSTSTORE_LOCATION` | — | TrustStore для Kafka SSL |
| `KAFKA_TRUSTSTORE_PASSWORD` | — | Пароль к TrustStore |

### Смежные сервисы

| Переменная | Описание |
|------------|----------|
| `DATAMANAGER_ROOT_URL` / `TN_SCADA_DATA_MANAGER_URL_ROOT` | Data-Manager |
| `GAAUDIT_URL_ROOT` | Grant-Access-Audit |
| `ALARMSERVICE_URL_ROOT` | Alarm-Service |

### Redis

| Переменная | Default | Описание |
|------------|---------|----------|
| `REDIS_ADDRESS` | — | Адреса (Sentinel/Redis), через запятую с портами |
| `REDIS_CONNECTION_TYPE` | `Standalone` | `Standalone` / `Sentinel` / `Cluster` |
| `REDIS_SENTINEL_MASTER` | — | Имя master-узла (для Sentinel) |
| `REDIS_USERNAME` | — | ACL логин |
| `REDIS_PASSWORD` | — | ACL пароль |
| `REDIS_SENTINEL_USERNAME` | — | ACL логин для Sentinel |
| `REDIS_SENTINEL_PASSWORD` | — | ACL пароль для Sentinel |
| `REDIS_ENABLE_SSL` | `false` | SSL для Redis |
| `REDIS_KEYSTORE_LOCATION` | — | KeyStore для Redis SSL |
| `REDIS_KEYSTORE_PASSWORD` | — | Пароль к KeyStore |
| `REDIS_TRUSTSTORE_LOCATION` | — | TrustStore для Redis SSL |
| `REDIS_TRUSTSTORE_PASSWORD` | — | Пароль к TrustStore |
| `TAG_METADATA_TOPIC` / `TN_SCADA_METADATA_TOPIC` | `dm-meta` | Топик метаданных |

### ClickHouse

| Переменная | Описание |
|------------|----------|
| `DB_CONNECTION_STRING` | JDBC URL |
| `DB_USERNAME` | Учётка |
| `DB_PASSWORD` | Пароль |
| `DB_TYPE` | `clickhouse` |

### HMI / WebSocket

| Переменная | Default | Описание |
|------------|---------|----------|
| `tn-scada.hmi.sample-time` | `50` | Окно агрегации WS V2 (мс) |
| `tn-scada.hmi.clock-message-interval-s` | `1` | Интервал серверного времени (с), 0 — отключить |
| `tn-scada.hmi.clientside-stale-time-s` | `3600` | Тайм-аут неактивной сессии (с) |
| `tn-scada.hmi.clientside-wake-time-s` | `30` | Тайм-аут пробуждения сессии (с) |
| `CSPA_HMI_CLIENTSIDE_STALE_TIME_S` | — | Альтернативное имя (stale) |
| `CSPA_HMI_CLIENTSIDE_WAKE_TIME_S` | — | Альтернативное имя (wake) |
| `CSPA_HMI_CLOCK_MESSAGE_INTERVAL_S` | — | Альтернативное имя (clock) |
| `USER_ACTION_TAGNAME` | — | Тег журнала действий в Alarm-Service |
| `USER_ACTION_ALERT_CLASS` | `AC1` | Класс алармов |
| `tn-scada.hmi-backend.use-sync-set` | `true` | Синхронное подтверждение записи |

### Логирование / OpenTelemetry

| Переменная | Default | Описание |
|------------|---------|----------|
| `LOGGER_ROOT_LEVEL` | `INFO` | Корневой логер (библиотеки) |
| `LOGGER_LEVEL` | `INFO` | `tnt.tnscada.*` |
| `LOGGER_OUTPUT_PATTERN_CONFIG` | — | Формат логов |
| `OTEL_SDK_DISABLED` | `false` | Вкл/выкл OTel |
| `OTEL_JAVAAGENT_LOGGING` | — | Куда выводить логи OTel agent |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | URL сборщика |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | — | Протокол (gRPC / HTTP) |
| `OTEL_SERVICE_NAME` | — | Имя в трассировке |

---

## Topic-Route (переопределение маршрутов)

Соответствие проектов/типов/параметров → топики Kafka + `descentRule`. Используется при создании объектов.

### YAML

```yaml
tn-scada:
  cspa:
    topic-route:
      root:
        descentRule: rcv
        topic: cspa-main-topic
      project:
        TU1:
          root:
            descentRule: rcv
            topic: tu1-root-topic
          type:
            NPS:
              "[.Alm.AlmAll.AlmAllStop.AlarmMinLevelRzv]":
                descentRule: rcv
                topic: topic1
              "[.]":
                descentRule: rcv
                topic: topic2
```

### Переменные окружения

```
tn-scada.cspa.topic-route.root.topic=cspa-main-topic
tn-scada.cspa.topic-route.root.descentRule=rcv
tn-scada.cspa.topic-route.project.TU1.root.topic=tu1-root-topic
tn-scada.cspa.topic-route.project.TU1.root.descentRule=rcv
tn-scada.cspa.topic-route.project.TU1.type.NPS."[.Alm.AlmAll.AlmAllStop.AlarmMinLevelRzv]".topic=topic1
tn-scada.cspa.topic-route.project.TU1.type.NPS."[.Alm.AlmAll.AlmAllStop.AlarmMinLevelRzv]".descentRule=rcv
tn-scada.cspa.topic-route.project.TU1.type.NPS."[.]".topic=topic2
tn-scada.cspa.topic-route.project.TU1.type.NPS."[.]".descentRule=rcv
```

### Алгоритм `TopicRouteConfig.getRoutes(objectName, objectTypeName)`

1. Разбивает на `ProjectQualifier`
2. Если проект не определён или отсутствует в конфиге → **root route**
3. Если проект есть, но тип не определён → **project root route**
4. Если проект и тип есть → **типовые маршруты** (все параметры типа + `[.]` как fallback)

> `ROOT_PARAMETER_NAME = "."` — fallback-маршрут для параметров без явного определения.

---

## Активное подключение - типа keep alive (AppWarmUp)

Выполняется при старте (`HmiEvoService.start()` → `appWarmUp.warmUp()`):

| Этап | Действие | Примечание |
|------|----------|------------|
| 1 | `kafkaProducerWarmUp()` | Периодическая отправка в hot topics (ScheduledExecutorService) |
| 2 | `websocketWarmUp()` | ReactorNetty WS client → PING, SUBSCRIBE, PING |
| 3 | `tagSetWarmUp()` | POST `/tag-set`, `/tags-set` со случайным тегом |
| 4 | `tagInfoStoreWarmUp()` | `evo.tagNames(pattern)`, `evo.findTag` для списка |

> После завершения — `HmiEvoService.ready = true`, REST-эндпоинты разблокируются.

---

## Утилиты

| Класс | Назначение |
|-------|------------|
| `JsonUtils` | Конвертация коллекций → `JsonArray` |
| `LimitedMap` | LRU-Map с ограничением размера (автосброс старейших) |
| `RequestUtils` | IP клиента, identity пользователя из заголовков |
| `TagValueUtils` | Сравнение значений, `isPlotable`, конвертация TagValue ↔ HmiMsg |
| `TickCollector` | Счётчик тиков за окно времени (для статистики/мониторинга) |
| `PingPongLogger` | Lazy-логирование PING/PONG (только на DEBUG) |
| `RequireServerReady` | Аннотация: блокировка до готовности |

---


---
id: KB-CALC-TESTSTAND-001
title: Тестовый стенд hydro-calculation: компоненты, механизмы ввода/вывода, топики, начальное состояние, cleanup
service: hydro-calculation
group: test-plan
source: confluence/test-plan-hydro-calculation.md#2.ТЕСТОВЫЙ.СТЕНД
requires: []
related: [KB-HMI-REST-VAL-001, KB-HMI-WS-001, KB-HMI-STREAM-001, KB-HMI-OVERVIEW-001, KB-HMI-MODEL-001, KB-CALC-MODELLING-001, KB-CALC-TESTPLAN-001]
status: verified
---

# Тестовый стенд hydro-calculation (тест-план HY-CALC, §2)

Факты — из `confluence/test-plan-hydro-calculation.md` §2. Ограничения
hmi-backend пересекаются с KB-HMI-* — см. `related` (каждый факт живёт в
одном фрагменте).

## Компоненты стенда (§2.1)

| Компонент | Назначение | Примечание |
|---|---|---|
| hydro-calculation | Тестируемый сервис | Java Spring Boot, N экземпляров (1 лидер + followers) |
| hmi-backend | API записи/чтения тегов | REST **8080**; WS V2 `ws://hmi-backend:8080/v2/hotlink`. Прокси: REST/WS → Kafka hot topics → hydro-calculation → Kafka → hmi-backend → ответ |
| clickhouse | Хранение истории | 8123 |
| postgresql | ИМ (конфигурация ТУ, несущая) | 5432 |
| redis | Кэш ИМ, состояния | 6379 |
| kafka | Брокер сообщений (KRaft) | 9092 |

## Механизмы ввода/вывода (§2.2)

Все взаимодействия с hydro-calculation в тест-кейсах — через **hmi-backend**
(8080): REST/WS → Kafka `cspa-main-topic` → hydro-calculation → Kafka →
hmi-backend → ответ.

### REST (однозначные запросы)

| Операция | Метод | URL | Body/Query |
|---|---|---|---|
| Чтение 1 тега | GET | `/v2/tag-get` | `?tagName=MT1.LU1.SGLU1.KIP1.TI.Press` |
| Чтение N тегов | POST | `/v2/tags-get` | `["tag1","tag2",...]` |
| Запись 1 тега | POST | `/v2/tag-set` | `{"tag":"...","data":{"value":5.0,"invalid":false}}` |
| Запись N тегов | POST | `/v2/tags-set` | `[{"tag":"...","data":{...}},...]` |
| История из CH | POST | `/v2/tags-get-history` | `{"startTime":...,"endTime":...,"tags":["..."],"limit":1000}` |

- Обязательные заголовки (запись): `X-USER-FULLNAME: Тестировщик`,
  `X-USER-ALLOW-PATTERNS: ["MT1..*"]`
- Обязательные заголовки (чтение): `X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]`
- Формат ответа (чтение):
  `{"tag":"MT1.LU1.SGLU1.KIP1.TI.Press","data":{"value":5.0,"invalid":false,"ts":1700000000000}}`

### WebSocket (подписка на изменения, E2E-проверки)

Адрес: `ws://hmi-backend:8080/v2/hotlink`. Кадр V2:

```json
{"cmd":"SUBSCRIBE","id":"req-001","args":["MT1.LU1.SGLU1.KIP1.TI.Head"],"headers":{"X-USER-ALLOW-PATTERNS":"[\"MT1\\..*\"]","X-USER-FULLNAME":"Тестировщик"}}
```

Приём изменения:

```json
{"cmd":"SUB_ANSWER","id":"req-001","args":[{"tag":"MT1.LU1.SGLU1.KIP1.TI.Head","data":{"value":663.2,"invalid":false,"ts":1700000000000}}]}
```

Использование в сценариях:

- Быстрая проверка (поллинг): REST `GET /v2/tag-get` — проще, синхронно.
- E2E-проверка: WS `SUBSCRIBE` → ожидание `SUB_ANSWER` — подтверждает полный
  цикл (Kafka → hydro-calculation → Kafka → hmi-backend).
- Алармы: WS `SUBSCRIBE` на `MT1.LU1.Alm.*` → ожидание `SUB_ANSWER` с
  `value: true`.

**Выбор метода в сценариях:**

| Обозначение | Реализация | Когда использовать |
|---|---|---|
| `hmi.set(tag, value)` | `POST /v2/tag-set` | запись входных данных (давления, расходы, команды) |
| `hmi.set(tag, value, invalid=true)` | `POST /v2/tag-set` `"invalid":true` | симуляция невалидных данных |
| `hmi.set_batch([...])` | `POST /v2/tags-set` | одновременная запись нескольких тегов |
| `hmi.get(tag)` | `GET /v2/tag-get?tagName=...` | проверка расчётного значения (поллинг) |
| `hmi.get_batch([...])` | `POST /v2/tags-get` | проверка нескольких тегов за запрос |
| `hmi.wait_change(tag, expected)` | WS `SUBSCRIBE` + `SUB_ANSWER` | E2E: значение изменилось через полный цикл |
| `hmi.wait_alarm(pattern)` | WS `SUBSCRIBE` + `SUB_ANSWER` | E2E: аларм сгенерирован и доставлен |
| `hmi.history(tag, from, to)` | `POST /v2/tags-get-history` | проверка истории (ClickHouse) |

### Ограничения hmi-backend, влияющие на автотесты (§2.2)

1. **503 до готовности:** бизнес-эндпоинты → 503 до AppWarmUp
   (`HmiEvoService.isReady() = true`). После `actuator/health = UP` дождаться
   `GET /diag/instance` → 200 (опрос 1 с, max 30 с) → KB-HMI-SVC-001.
2. **Валидация типа:** несовпадение типа значения → HTTP 400 +
   `ValueConversionException` (`ProtoValidator`). Передавать значения строками
   (`"5.0"`, не `5.0`) → KB-HMI-TAG-001, KB-HMI-ERR-001.
3. **Агрегация WS V2 (50 мс):** значения пакетом не чаще раза в 50 мс; после
   `TAG_SET` ожидать `SUB_ANSWER` с таймаутом ≥ 200 мс → KB-HMI-WS-001.
4. **Minuteman (30 с):** wake-time 30 с, stale-time 3600 с; в сценариях
   > 2 мин отправлять `PING` каждые 15–20 с → KB-HMI-WS-001.
5. **Kafka-маршрутизация:** hmi-backend не знает о `cspa-main`/`model_main_*`
   напрямую; привязка hot topic — конфигурация `CSPA_TOPICS`/`TopicRouteConfig`.
   Если hot topic ≠ `cspa-main` — значения не дойдут до hydro-calculation
   → KB-HMI-MODEL-001.
6. **Заголовки обязательны:** без `X-USER-FULLNAME`/`X-USER-ALLOW-PATTERNS`
   при записи → 401/403; без `X-USER-GET-ALLOW-PATTERNS` при чтении → default
   `[".*"]` → KB-HMI-ERR-001 (расхождение источника — G13).

## Топики Kafka стенда (§2.3)

| Топик | Направление | Формат |
|---|---|---|
| `main` | Вход + Выход | `{tag, ts, value, invalid}` |
| `alarm` | Выход | `{tag, ts, value, text, priority, state}` |
| `model_main_{id}` | Вход + Выход (моделирование) | `{tag, ts, value, invalid}` |
| `model_alarm_{id}` | Выход (моделирование) | `{tag, ts, value, text, priority, state}` |

## Начальное состояние стенда (§2.4)

- Конфигурация ТУ загружена в data-manager (PostgreSQL + Redis): массивы
  `LU_KM`, `LU_HEIGHT`, `LU_PMAXDEFAULT` для всех ТУ.
- Все KIP, UR, PLTM, GRZDV, ZDV, SGLU существуют в ИМ.
- Все датчики `Disable = false`, `Manual = false`; `LU_CONTROL = 0` для всех
  ТУ; `LU_AUTOCONTROLON = false` для всех ТУ.
- Топик `main` наполнен текущими (штатными) значениями; топик `alarm` пуст
  (или только стартовые события).
- Конфигурационные значения (ΔMax, ΔMin, DensLimit, PressRateLimit и т.д.)
  заданы в ИМ.

> Конкретная конфигурация ТУ для автотестов ещё не выбрана. В сценариях —
> абстрактные адреса без привязки к ТДП: `MT1.LU1.SGLU1.KIP1` и т.д.

## Cleanup / `RESET()` (§2.5)

После каждого тест-кейса:

1. Изменённые теги возвращаются к значениям начального состояния.
2. Если включался Control → снимается (`SetControlOff = 1`).
3. Если включался AutoControl → отключается (`SetAutoControlOff = 1`).
4. Если задавался PressManualLimit → очищается.
5. Если включалась трассировка → выключается.
6. Алармы в топике `alarm` не очищаются (накапливаются); при проверке —
   только события, появившиеся после начала конкретного теста.
7. WS-подписки отключены (`UNSUBSCRIBE_ALL` через `ws://hmi-backend:8080/v2/hotlink`
   или закрытие WS-сокета).
8. WS-сессия закрыта (если использовалась для `SUBSCRIBE`/`TAG_SET`/`TAG_GET`).

> Cleanup не является объектом проверки. Он обеспечивает изоляцию тестов:
> каждый тест стартует с известного состояния.
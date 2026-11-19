---
id: KB-CALC-TESTPLAN-001
title: Тест-план HY-CALC: обозначения сценариев, правила исполнения, чек-лист стенда, допущения, покрытие
service: hydro-calculation
group: test-plan
source: confluence/test-plan-hydro-calculation.md#1.8,#4,#5,#6,#7
requires: [KB-CALC-TESTSTAND-001]
related: [KB-HMI-REST-VAL-001, KB-HMI-WS-001, KB-HMI-ERR-001]
status: verified
---

# Тест-план HY-CALC: обозначения и правила (§1.8, §4–7)

## Обозначения для сценариев (§1.8)

> Канон — таблица §1.8. §2.6 содержит дубль с расхождениями (хост `hmi` вместо
> `hmi-backend`, иной состав операций, другие WAIT-правила и формат заголовков) —
> см. G14 в `meta/discrepancies-2026-11-17.md`. Уникальное из §2.6 включено ниже.

| Обозначение | Реализация | Примечание |
|---|---|---|
| `hmi.set(tag, value)` | `POST http://hmi-backend:8080/v2/tag-set` | Body: `{"tag":tag,"data":{"value":"<str>","invalid":false,"ts":<ms>}}`. Headers: `X-USER-FULLNAME: Test`, `X-USER-ALLOW-PATTERNS: ["MT1..*"]` |
| `hmi.set(tag, value, invalid=true)` | `POST /v2/tag-set` | `"invalid":true` в data |
| `hmi.set_batch([...])` | `POST /v2/tags-set` | Массив объектов |
| `hmi.get(tag)` | `GET http://hmi-backend:8080/v2/tag-get?tagName=tag` | Headers: `X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]`. Ответ: `{"tag":"...","data":{"value":"<str>","invalid":<bool>,"ts":<ms>,"ts2":<ms>}}` |
| `hmi.get_batch([...])` | `POST /v2/tags-get` | Body: массив строк |
| `hmi.wait_change(tag, condition)` | WS `ws://hmi-backend:8080/v2/hotlink` → `SUBSCRIBE` → ожидание `SUB_ANSWER` | Агрегация 50 мс. Таймаут: WAIT + 10 с |
| `hmi.wait_alarm(pattern)` | WS `SUBSCRIBE` на теги matching `pattern` → ожидание `value:true` | Таймаут: WAIT + 10 с |
| `hmi.history(tag, from, to)` | `POST /v2/tags-get-history` | Ответ: массив `{ts, value, invalid}` |
| `kafka.send(topic, msg)` | Kafka Producer API напрямую | Обход hmi-backend (симуляция СДКУ) |
| `kafka.consume(topic, filter)` | Kafka Consumer API | Проверка сообщений в топике |
| `redis.get(key)` / `redis.set(key, value)` | Redis CLI / client | Чтение/запись кэша ИМ |
| `WAIT(cycle)` | Ожидание по таймеру | 60с / 2с / 1с + margin 5с |
| `WAIT(event)` | Ожидание обработки callback | + margin 5с |
| `RESET()` | Cleanup (§2.5) | `POST /v2/tags-set` с начальными значениями |
| `CONFIG_X = Y` | Значение из ИМ | Не является действием |
| `// PRIMECHANIE: ...` | Комментарий | Не является действием (из §2.6) |

> **Важно (§1.8):** В V2 значение тега — **плоский JSON-примитив** внутри
> `data.value` (строка: `"5.0"`, `"true"`). Тип валидируется сервером через
> `ProtoValidator` против типа тега. Несоответствие → HTTP 400.

**Правило ожидания (§1.8):**

- POLL(60с): `WAIT(60c)` — максимум 65 секунд
- POLL(2с): `WAIT(2c)` — максимум 7 секунд
- POLL(1с): `WAIT(1c)` — максимум 6 секунд
- EVENT: `WAIT(event)` — максимум 5 секунд (callback срабатывает практически мгновенно)
- POLL(60мин): `WAIT(60min)` — максимум 3605 секунд (ночные тесты)

**Правила (§2.6, уникальное):**

- `hmi.get` — поллинг: допустимо 3 повторных запроса с интервалом 2 с (~6 с),
  если значение не изменилось.
- `WAIT(cycle)` — «слепое» ожидание полного цикла алгоритма (POLL). После `WAIT`
  всегда `hmi.get` для проверки.
- Порядок: `hmi.set` → `WAIT` → `hmi.get` (для POLL). `hmi.set` →
  `hmi.wait_change` (для EVENT/E2E).
- Заголовки REST: `X-USER-ALLOW-PATTERNS`, `X-USER-GET-ALLOW-PATTERNS`,
  `X-USER-FULLNAME`. Заголовки WS-кадров — в поле `headers`.

## Правила исполнения (§4)

1. **Изоляция:** Каждый тест стартует с начального состояния. Teardown обязателен.
2. **Ожидание:** Всегда использовать `WAIT(cycle)` с запасом 5 с. Никогда не ждать «на глаз».
3. **Проверка:** Проверять **и** тег (hmi.get), **и** событие в топике alarm
   (kafka.consume) (если актуально для сценария).
4. **Граничные значения:** При проверке границ — всегда тестировать ровно на
   границе (без аларма) и за границей (с алармом).
5. **Исправление:** При сбое — фиксировать фактический результат, не исправлять
   ожидаемый.
6. **Номер сценария:** В репорте указывать HY-CALC-xxx.
7. **Consumer Lag:** При красном тесте дополнительно зафиксировать в Allure:
   `kafka.lag(cspa-main, group=hydro-calculation)` и (для моделирования)
   `kafka.lag(model_main_{id}, group=hydro-calculation)`. Формат:
   `kafka_lag: {topic}={lag_value} (threshold: 100 msgs)`. Если lag > 100 —
   пометить: «⚠️ Возможно проблема в большом консьюмер лаге» — отличать ошибку
   алгоритма от недоставленных данных.

## Чек-лист подготовки стенда (§5)

| # | Шаг | Апи |
|---|---|---|
| 1 | hydro-calculation развёрнут | |
| 2 | hmi-backend развёрнут, API доступен | |
| 3 | Kafka развёрнут, топики main/alarm/model_* существуют | |
| 4 | PostgreSQL: ИМ загружено (конфигурация ТУ, KIP, UR, PLTM, GRZDV, ZDV) | |
| 5 | Redis: кэш ИМ загружен | |
| 6 | ClickHouse: schema готова, тестовые данные для HY-CALC-064 | |
| 7 | Конфигурация ТУ для автотестов выбрана и загружена в data-manager | |
| 8 | Значения ИМ зафиксированы (ΔMax, ΔMin, DensLimit, PressRateLimit, LimitKIP, TimeIntSetStation, ControlAutoTimeOut) | |
| 9 | Начальное состояние подтверждено: Control=0, AutoControlOn=false, все Disable=false | |
| 10a | health | `GET /actuator/health` → `{"status":"UP"}` |
| 10b | прогревание завершено | `GET /diag/instance` → HTTP 200 (не 503) |
| 10c | WS V2 доступен | `PING` → `PONG` в течение 5 с |
| 10d | доступ к тестовым тегам | `GET /v2/tag-get` + `X-USER-GET-ALLOW-PATTERNS` → 200 |
| 10e | запись тега работает | `POST /v2/tag-set` → 200 |
| 10f | hmi-backend → Kafka | значение в `cspa-main` в течение 5 с (верифицирует допущение №1) |

## Допущения (§6)

| # | Описание | Статус |
|---|---|---|
| 1 | `POST /v2/tag-set` публикует в Kafka hot topics (`CSPA_TOPICS`/`TopicRouteConfig`); для оперативного режима hot topic должен совпадать с `cspa-main` | Допущение (верифицируется чек-листом 10f) |
| 2 | `GET /v2/tag-get` читает из DataStream (Kafka → `TagValueStreamHandler` → буфер); кэш метаданных `TagInfoService` TTL 5 с | Подтверждено документацией (KB-HMI-STREAM-001) |
| 3 | `POST /v2/tag-set` валидирует тип значения (`ProtoValidator`) → 400 при несовпадении | Подтверждено (KB-HMI-TAG-001) |
| 4 | До AppWarmUp бизнес-эндпоинты → 503; разрешены `/actuator/*`, `/health*`, `/diag/*` | Подтверждено (KB-HMI-SVC-001) |
| 5 | WS V2 агрегирует подписки в окне 50 мс (`tn-scada.hmi.sample-time`) | Подтверждено (KB-HMI-WS-001) |
| 6 | Minuteman: stale-time 3600 с, wake-time 30 с | Подтверждено (KB-HMI-WS-001) |
| 7 | `POST /v2/tags-get-history` читает из ClickHouse напрямую; для HY-CALC-058/059/064 данные должны быть уже в CH | Подтверждено (KB-HMI-MODEL-001) |
| 8 | Все значения «из ИМ» — примеры; конкретные фиксируются при подготовке стенда | Допущение |
| 9 | Тег `LU1_TU_TRANSITIONCONTROLON` — допущение; механизм перехода в Control=2 уточняется | Допущение (→ HY-CALC-008 needs-review) |
| 10 | Формат JSON плана перекачки — допущение | Допущение (→ HY-CALC-063 needs-review) |
| 11 | Приоритет в alarm (WARNING/CRITICAL/ALARM) — допущение | Допущение |
| 12 | Обновление ИМ в runtime не предполагается; конфигурация фиксируется на подготовке; динамическое изменение — рестарт или отдельный сценарий | Допущение |

## Полнота покрытия (§7)

- Алгоритмы: в репозитории 43; сценарии покрывают 42; не покрыт осознанно
  ChecklistAlg (не влияет на расчёты; возможно юнит-тестами разработчиков).
  **Покрытие: 42/43 = 97.7%**.
- Требования: всего 101, к гидрокалькуляциям — 43. Полное покрытие
  **42 / 43 = 97.7%** (R-HYDR-001–007, 009*, 010–014, 016–043).
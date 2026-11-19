---
id: KB-HM-TESTPLAN-001
title: Тест-план HY-HIST: обозначения сценариев, enum-коды, правила исполнения, чек-лист стенда, допущения
service: hydro-history-and-model
group: test-plan
source: confluence/test-plan-hydro-history-and-model.md#1.6, #1.8, #4, #5, #6
requires: [KB-HM-TESTSTAND-001]
related: [KB-HM-SESSIONS-001, KB-HM-SAVE-001, KB-HM-WATERMARK-001, KB-HMI-REST-VAL-001, KB-HMI-WS-001, KB-HMI-ERR-001]
status: verified
---

# Тест-план HY-HIST: обозначения и правила (§1.6, §1.8, §4–6)

Стенд, константы и формулы — KB-HM-TESTSTAND-001. Факты — из
`confluence/test-plan-hydro-history-and-model.md`. Ограничения hmi-backend
пересекаются с KB-HMI-* — см. `related` (каждый факт живёт в одном фрагменте).

## Обозначения для сценариев (§1.8)

**REST mod-hist (реальные endpoint'ы из реализации):**

| Обозначение | Метод | Путь | Описание |
|---|---|---|---|
| `api.createHistorical(params)` | POST | `/v2/mod-hist/sessions/historical` | Создание historical |
| `api.createModelling(params)` | POST | `/v2/mod-hist/sessions/modelling` | Создание modelling |
| `api.createTimeshift(params)` | POST | `/v2/mod-hist/sessions/time-shift` | Создание timeshift |
| `api.playModel(sessionId)` | POST | `/v2/mod-hist/sessions/play-model/{id}` | Воспроизведение сохранённой |
| `api.save(sessionId)` | POST | `/v2/mod-hist/sessions/{id}/save` | Сохранение сессии |
| `api.import_(sessionId, file)` | POST | `/v2/history-import/...` | Импорт (HistoryImportController) |
| `api.export_(sessionId, format)` | GET/POST | `/v2/report/...` | Экспорт (ReportController) |

**REST mod-hist (псевдо-ручки, не подтверждены в реализации):**

> ⚠️ **Псевдо-ручка** — endpoint существует как абстракция в тестплане — по
> аналогии с ТЗ. Реальный путь/метод может отличаться. Перед выполнением
> сценария требуется верификация по коду (см. допущения 1–7).

| Обозначение | Метод | Путь | Описание |
|---|---|---|---|
| `api.start(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/start` | Запуск сессии |
| `api.stop(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/stop` | Остановка |
| `api.pause(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/pause` | Пауза |
| `api.resume(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/resume` | Возобновление |
| `api.close(sessionId)` ⚠️ | DELETE | `/v2/mod-hist/sessions/{id}` | Закрытие |
| `api.delete(sessionId)` ⚠️ | DELETE | `/v2/mod-hist/sessions/{id}/delete` | Удаление |
| `api.get(sessionId)` ⚠️ | GET | `/v2/mod-hist/sessions/{id}` | Чтение |
| `api.list(filters)` ⚠️ | GET | `/v2/mod-hist/sessions` | Список |
| `api.advance(sessionId, seconds)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/advance` | Продвижение (modelling) |
| `api.watermark(sessionId)` ⚠️ | GET | `/v2/mod-hist/sessions/{id}/watermark` | Watermark |
| `api.progress(sessionId)` ⚠️ | GET | `/v2/mod-hist/sessions/{id}/progress` | Прогресс |
| `api.setSpeed(sessionId, ratio)` ⚠️ | PUT | `/v2/mod-hist/sessions/{id}/speed` | Смена скорости |
| `api.retry(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/retry` | Повтор после ERROR |

**hmi-backend (установка/чтение значений):**

| Абстракция | Реальный endpoint | Метод | Body / Query | Заголовки |
|---|---|---|---|---|
| `hmi.set(tag, value, invalid?)` | `/v2/tag-set` | POST | `{"tag":"MT1.LU1.SGLU1.KIP1.TI.Press","data":{"value":"7.0","invalid":false,"ts":1705300000000}}` | `X-USER-FULLNAME: Test`, `X-USER-ALLOW-PATTERNS: ["MT1..*"]`, `Content-Type: application/json` |
| `hmi.setBatch(tags[])` | `/v2/tags-set` | POST | `[{"tag":"...","data":{"value":"...","invalid":false,"ts":...}}, ...]` | те же |
| `hmi.get(tag)` | `/v2/tag-get` | GET | Query: `tagName=...` | `X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]` (default `[".*"]`) |
| `hmi.getBatch(tags[])` | `/v2/tags-get` | GET/POST | Query: `tagNames=t1&tagNames=t2` или body `["t1","t2"]` | те же |

Формат ответа `hmi.get`: `{"tag":"...","data":{"value":"7.0","invalid":false,
"ts":...,"ts2":...}}`. В V2 `value` — плоский JSON-примитив внутри `data.value`;
тип валидируется `ProtoValidator` — несоответствие → HTTP 400 +
`ValueConversionException`. В автотестах числовые значения писать строками
(`"7.0"`, не `7.0`).

**WebSocket V2** (`ws://hmi-backend:8080/v2/hotlink`): команды `SUBSCRIBE`,
`UNSUBSCRIBE`, `UNSUBSCRIBE_ALL`, `TAG_GET`, `TAG_SET`, `PING`; ответы
`SUB_ANSWER` (агрегация в окне **50 мс**), `CALL_ANSWER`, `CALL_ERROR`, `PONG`.
Заголовки передаются в поле `headers` JSON-кадра (строки JSON-массивов):
`X-USER-ALLOW-PATTERNS`, `X-USER-FULLNAME` (для `TAG_SET`).

**Kafka / Redis / CH / PG:**

| Обозначение | Описание |
|---|---|
| `kafka.send(topic, msg)` | Прямая отправка в Kafka |
| `kafka.consume(topic, filter, timeout)` | Ожидание сообщения |
| `redis.get(key)` / `redis.set(key, value)` | Чтение/запись Redis |
| `ch.query(sql)` | SQL-запрос к ClickHouse :8123 |
| `pg.query(sql)` | SQL-запрос к PostgreSQL :5432 |

**Общие:**

| Обозначение | Описание |
|---|---|
| `WAIT(n)` | Слепое ожидание n секунд |
| `WAIT(event, timeout)` | Ожидание события с таймаутом |
| `RESET()` | Cleanup (KB-HM-TESTSTAND-001, §2.4) |
| `CONFIG_X = Y` | Значение, заданное в конфигурации |

**Правила ожидания:** REST — таймаут 30 с; WS — 60 с; Kafka — max(interval, 30)
с; `api.get` — допустимо 3 повторных запроса с интервалом 2 с.

**Заголовки (все REST):**

| Заголовок | Для чего | Обязательность |
|---|---|---|
| `X-USER-FULLNAME` | Идентификация (аудит) | **Required** при `tag-set` |
| `X-USER-ALLOW-PATTERNS` | Разрешение на запись | **Required** при `tag-set` |
| `X-USER-GET-ALLOW-PATTERNS` | Разрешение на чтение | Optional (default `[".*"]`) |
| `X-USER-FORBIDDEN-PATTERNS` | Чёрный список (запись) | Optional, **приоритет над allow** |
| `X-USER-GET-FORBIDDEN-PATTERNS` | Чёрный список (чтение) | Optional |
| `X-USER-IP` | IP для аудита | Optional |

**Ограничения hmi-backend, влияющие на автотесты:**

1. **503 до готовности:** бизнес-эндпоинты → 503 до завершения AppWarmUp; после
   `actuator/health = UP` дождаться `GET /diag/instance` → 200 (опрос 1 с, max 30 с).
2. **Валидация типа:** несовпадение типа значения → HTTP 400.
3. **Агрегация WS V2 (50 мс):** после `TAG_SET` ожидать `SUB_ANSWER` с таймаутом ≥ 200 мс.
4. **Minuteman (30 с):** WS без активности будится каждые 30 с (`wake-time`),
   закрывается через 3600 с (`stale-time`); в сценариях > 2 мин слать `PING` каждые 15–20 с.
5. **Kafka-маршрутизация:** hmi-backend не знает о `model_main_{sessionId}`;
   привязка hot topic к топику сессии — ответственность конфигурации
   (допущение 17). Если hot topic ≠ `model_main_{sessionId}` — значения не дойдут.

## Справочник enum-кодов (§1.6)

Коды — из тест-плана (используются в API-ответах и WS-событиях кейсов HY-HIST).
Имена статусов из repo_description (5 состояний) расходятся с 13-состоятельной
моделью тест-плана — см. G18 в `meta/discrepancies-2026-11-17.md`.

**ProcessingMode:** 0 `historical`, 1 `modelling`, 2 `timeshift`.

**SessionStatus (13 состояний):**

| Код | Статус | Переходы |
|---|---|---|
| 0 | `CREATED` | → OPENING (start), → CLOSING (close без запуска) |
| 1 | `OPENING` | → PLAYING (успех), → ERROR (сбой) |
| 2 | `PAUSED` | → PLAYING (resume), → CLOSING (close) |
| 3 | `PLAYING` | → PAUSED, → DONE (auto-stop), → SAVING, → CLOSING, → ERROR |
| 4 | `SAVING` | → SAVED, → ERROR, → CANCELLING |
| 5 | `SAVED` | → CLOSING, → DELETED |
| 6 | `IMPORTING` | → IMPORTED (успех), → ERROR (сбой) |
| 7 | `IMPORTED` | → OPENING (start), → CLOSING |
| 8 | `DONE` | → CLOSING, → SAVING, → DELETED |
| 9 | `DELETED` | терминальное |
| 10 | `CLOSING` | → CLOSED, → ERROR |
| 11 | `CLOSED` | → DELETED (cleanup) |
| 12 | `ERROR` | → PLAYING (retry), → CLOSING, → CLOSED |

**SaveSessionStatus:** 0 `CREATED`, 1 `SAVING`, 2 `SAVED`, 3 `CANCELLING`,
4 `CANCELLED`, 5 `ERROR`.
**HistoryImportStatus:** 0 `CREATED`, 1 `RUNNING`, 2 `DONE`, 3 `ERROR`, 4 `DELETED`.
**ImportFormat:** 0 `XLSX`, 1 `ZIP_CSV`.
**PlayerMode:** 0 `Play`, 1 `Stop`, 2 `SetSpeed`, 3 `Seek`.
**SourceMode:** 0 `saved`, 1 `imported`, 2 `history`.
**WatermarkState:** 0 `INIT`, 1 `MOVING`, 2 `STALLED`, 3 `COMPLETE`.

**SessionEventType (WebSocket):** 0 `SESSION_CREATED`, 1 `SESSION_OPENED`,
2 `SESSION_PAUSED`, 3 `SESSION_RESUMED`, 4 `SESSION_DONE`, 5 `SESSION_CLOSED`,
6 `SESSION_ERROR`, 7 `WATERMARK_UPDATED`, 8 `WATERMARK_STALLED`,
9 `WATERMARK_COMPLETE`, 10 `DATA_IMPORT_COMPLETE`, 11 `DATA_EXPORT_COMPLETE`,
12 `BUFFER_OVERFLOW`, 13 `SPEED_CHANGE`, 14 `SESSION_SAVED`, 15 `SESSION_SAVING`,
16 `SESSION_DELETED`.

## Правила исполнения (§4)

1. **Изоляция:** каждый тест стартует с начального состояния (2.3). Teardown
   обязателен. После каждого теста: `api.list({})` ⚠️ → пустой массив,
   `redis.keys("session:*")` → пусто.
2. **Ожидание:** `WAIT(n)` с запасом 5 с. WS: timeout = ожидаемое время + 10 с.
   Kafka: timeout = max(interval, 30) с.
3. **Множественная проверка:** каждый критичный результат — минимум из 2
   источников (REST+WS, REST+Redis, REST+PG, Kafka+Redis/REST) — для локализации.
4. **Промежуточные состояния:** для длинных каскадов проверять каждое: команда в
   `mod-hist-commands`, результат в `mod-hist-results`, статус в Redis, запись в
   PG, событие WS.
5. **Граничные значения:** 3 точки — ровно на границе (допустимо), за границей на
   1 (недопустимо), за границей значительно (недопустимо).
6. **Исправление:** при сбое фиксировать **фактический** результат, не исправлять
   ожидаемый; различия документировать (шаг, источник, ожидалось vs получено).
7. **Номер сценария:** в отчёте `HY-HIST-xxx`.
8. **Идемпотентность:** повторный запуск того же сценария — тот же результат.
9. **Время:** для тестов > 2 мин использовать сокращённые параметры, помечая
   «Для ускорения: X временно = Y (механизм: ...)».
10. **Локализация:** в неоднозначных местах указывать «Если X — значит баг в Y».

## Чек-лист подготовки стенда (§5)

| # | Проверка | Как | Ожидаемый результат |
|---|---|---|---|
| 1 | mod-hist развёрнут, UP | `GET /actuator/health` | `{"status":"UP"}` |
| 2 | hydro-calculation развёрнут, UP | health check (порт уточнить) | `{"status":"UP"}` |
| 3 | Kafka: топики существуют | `kafka-topics --list --bootstrap-server kafka:9092` | `cspa-main`, `mod-hist-commands`, `mod-hist-results` в списке |
| 4 | PostgreSQL: таблицы существуют | `pg.query(... pg_tables ...)` | `sessions`, `session_results` (2 строки) |
| 5 | Redis: доступен, ключи отсутствуют | `redis.keys("session:*")` | Пустой массив |
| 6 | ClickHouse: тестовая история загружена | `ch.query("SELECT count(*) FROM history WHERE tag LIKE 'MT1.LU1.%' ...")` | ≥ 10 000 |
| 7a | hmi-backend: health | `GET /actuator/health` | `{"status":"UP"}` |
| 7b | hmi-backend: прогревание завершено | `GET /diag/instance` | HTTP 200, `evo-manager.app-id` (не 503) |
| 7c | hmi-backend: WS V2 доступен | WS `{"cmd":"PING","id":"test"}` | `PONG` с `id:"test"` за 5 с |
| 7d | hmi-backend: доступ к тестовым тегам | `GET /v2/tag-get?tagName=MT1.LU1.SGLU1.KIP1.TI.Press` + `X-USER-GET-ALLOW-PATTERNS` | HTTP 200, в теле `tag` и `data` |
| 8 | Конфигурация ТУ1 загружена в data-manager | `pg.query(... tu_config ...)` или `redis.get("tu:MT1.LU1:config")` | ≠ 0 / ≠ null |
| 9 | Файлы импорта готовы (XLSX, ZIP_CSV) | Файлы в рабочей директории | `import_test.xlsx`, `import_test.zip` существуют |
| 10 | Начальное состояние подтверждено | `api.list({})` ⚠️ + `GET /actuator/health` | Пустой массив + UP |
| 11 | Kafka ACL настроен | `kafka.acls --list --topic model_main_* ...` | Allow для produce/consume |
| 12 | Hydro-calc подписан на mod-hist-commands | `kafka-consumer-groups --describe --group hydro-calc-*` | Group существует, lag = 0 |
| 13 | Возможность менять `Cleanup.intervalMs` | Уточнить: Redis/config/env/actuator | Механизм задокументирован |
| 14 | Возможность менять `sessionTTL` | Уточнить: Redis/config/env | Механизм задокументирован |
| 15 | Возможность менять `bufferSize` | Уточнить: Redis/config/env | Механизм задокументирован |

## Допущения (§6)

| # | Допущение | Статус | Примечание |
|---|---|---|---|
| 1 | `api.start` ⚠️ для CREATED-сессии: `POST /v2/mod-hist/sessions/{id}/start` | **Псевдо** | Возможно: `play-model` для saved, отдельный endpoint для новых |
| 2 | `api.stop` ⚠️: `POST /v2/mod-hist/sessions/{id}/stop` | **Псевдо** | — |
| 3 | `api.pause` ⚠️ / `api.resume` ⚠️ | **Псевдо** | — |
| 4 | `api.close` ⚠️: `DELETE /v2/mod-hist/sessions/{id}` | **Псевдо** | — |
| 5 | `api.advance` ⚠️: `POST /v2/mod-hist/sessions/{id}/advance` | **Псевдо** | Возможно: WS-команда или player-controller |
| 6 | `api.setSpeed` ⚠️: `PUT /v2/mod-hist/sessions/{id}/speed` | **Псевдо** | Возможно: WS-команда (PlayerMode = SetSpeed) |
| 7 | `api.retry` ⚠️: `POST /v2/mod-hist/sessions/{id}/retry` | **Псевдо** | Возможно: повторный `start` для ERROR-сессии |
| 8 | Повторный `api.start` для PLAYING-сессии возвращает HTTP 200 (не 409) | **Допущение** | Требует верификации |
| 9 | При отсутствии данных в CH сессия переходит в ERROR (12), не DONE (8) | **Допущение** | Требует верификации |
| 10 | `advance(-60)` отклоняется с 400 | **Допущение** | Требует верификации |
| 11 | WS не буферизует события при отключении клиента | **Допущение** | Проверяется в HY-HIST-042 |
| 12 | При закрытии сессии Redis-ключи удаляются (не помечаются) | **Допущение** | Альтернатива: ключ остаётся со status=11 до TTL (24 ч) |
| 13 | Экспорт пустого диапазона возвращает 200 с пустым CSV | **Допущение** | Альтернатива: 404 |
| 14 | Поле `dataGaps` в ответе `api.get` при частичных данных | **Допущение** | Может не существовать |
| 15 | `closeReason = "TTL_EXCEEDED"` — формат поля | **Допущение** | Может быть enum, код или отсутствовать |
| 16 | Cleanup удаляет сессии старше 1 дня (X = 1) | **Допущение** | Точное значение из конфигурации |
| 17 | `hmi.set` публикует в Kafka hot topics (`CSPA_TOPICS` / `TopicRouteConfig`); для mod-hist hot topic должен совпадать с `model_main_{sessionId}` | Подтверждено документацией | Механизм привязки — **уточнить**; hmi-backend не знает о `model_main_*` |
| 18 | `hmi.get` читает из DataStream (Kafka consumer → буфер), не из Redis; кэш метаданных `TagInfoService` (TTL **5 с**) | **Допущение** | Redis — для кэша ИМ/метаданных |
| 19 | При `POST /v2/tag-set` тип значения валидируется (`ProtoValidator`) → 400 + `ValueConversionException` | **Подтверждено документацией** | `"abc"` в DOUBLE-тег → ожидаем 400 |
| 20 | До завершения AppWarmUp бизнес-эндпоинты → **503** (`ServerReadyRestInterceptor`); разрешены `/actuator/*`, `/health*`, `/diag/*` | **Подтверждено документацией** | После `actuator/health = UP` дождаться `diag/instance = 200` |
| 21 | WS V2 агрегирует подписки в окне **50 мс** (`tn-scada.hmi.sample-time`) | **Подтверждено документацией** | После `TAG_SET` ожидание `SUB_ANSWER` — до 100 мс |
| 22 | WS V2 `Minuteman`: `clientside-wake-time-s` **30 с**, `clientside-stale-time-s` **3600 с** | **Подтверждено документацией** | `PING` каждые 10–20 с в длительных сценариях |
| 23 | Событие SESSION_OPENED (type=1) приходит при OPENING→PLAYING | **Допущение** | Может приходить при CREATED→OPENING |
| 24 | Watermark при запуске historical = startTime (не null) | **Допущение** | Может быть null до первого сообщения |
| 25 | timeshift использует `sourceMode` (saved/imported/history) для выбора источника | **Допущение** | Из Блока A, не подтверждено сценариями |
| 26 | Сессия SAVED может быть запущена только через `play-model` (не `start`) | **Допущение** | Из Блока B (PlayModelController) |

Покрытие: 26 допущений; 20 кейсов используют ⚠️-псевдо-ручки — верификация
endpoint'ов по коду обязательна перед прогоном (см. G22 в
`meta/discrepancies-2026-11-17.md`).





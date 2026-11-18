---
id: KB-SYS-TESTPLAN-001
title: Тестплан системных тестов: принципы, классификация, правила, чек-лист, допущения, блокеры, план исполнения
service: system-tests
group: test-plan
source: confluence/test-plan-of-system-tests.md#1,#4,#5,#6,#7,#8,#9,#11
requires: [KB-SYS-TESTSTAND-001]
related: [KB-HM-TESTPLAN-001, KB-CALC-TESTPLAN-001, KB-HMI-WS-001, KB-HMI-ERR-001]
status: verified
---

# KB-SYS-TESTPLAN-001 — Тестплан системных тестов: правила

## Общие сведения (§1)

| Параметр | Значение |
|---|---|
| Объект | Гидроуклон как система (взаимодействие микросервисов) |
| Уровень | SYS-1 (двухсервисный), SYS-2 (трёхсервисный с алармами) |
| Кол-во сценариев | **52** по факту таблиц §3.1–3.3 и §4/§11 (в §1 и сводке Части 1 указана 53 — см. G26) |
| Из них: перенесённые из HY-CALC (алармные, заглушки) | 26 |
| Из них: перенесённые из HY-HIST | 19 |
| Из них: новые | 7 (HY-SYS-049 не описан — см. G27) |
| Стенд | Тестовый стенд ЭВОСКАДА (все сервисы) — KB-SYS-TESTSTAND-001 |

## Принципы (§1.1)

1. **hmi-backend — шлюз.** Его использование для установки/чтения данных не делает сценарий системным.
2. **Системный = 2+ микросервисов.** mod-hist + hydro-calc, hydro-calc + alarm-service, mod-hist + data-manager.
3. **Алармы через `hmi.wait_alarm`** = системный (hydro-calc → REST alarm-service → hmi-backend WS + alarm-view-service).
4. **Прямое чтение Kafka** (`kafka.consume`) = наблюдение, не делает сценарий системным.
5. **Каждый сценарий самодостаточен.** Нет зависимостей между сценариями. Сложные предусловия — выполняются внутри сценария.
6. **Мульти-сервисная верификация.** Результат проверяется в каждом сервисе цепочки.
7. **Щупы в Kafka.** В каждом сценарии, где данные проходят через Kafka — `kafka.consume` на промежуточные точки для локализации.

## Правила верификации (§1.3)

| Правило | Пояснение |
|---|---|
| Мульти-сервисная проверка | Результат в каждом сервисе цепочки |
| Порядок событий | `ts_A < ts_B` для последовательных операций |
| Согласованность | Значение в Kafka = значению в CH = значению через hmi.get (пример) |
| «Щупы» | `kafka.consume` на промежуточных точках для быстрой локализации |

## Классификация сценариев (Часть 1, §4)

Какие кейсы смежных тестпланов отнесены к системным (обоснование — 2+ микросервиса):

**Из HY-CALC → системные (алармные): 26 кейсов** — HY-CALC-014–018, 032–041, 073–080, 083–085
(цепочка `hmi.wait_alarm` → hydro-calc → REST alarm-service → hmi-backend WS;
остальные разделы HY-CALC — интеграционные: hydro-calc + шлюз без второго микросервиса).
В источнике указано «27» — фактически в диапазонах 26 (G26).

**Из HY-HIST → системные: 19 кейсов** — HY-HIST-005 (START → Kafka → hydro-calc),
014–020 (CH → mod-hist → Kafka → hydro-calc), 022–023 (advance → Kafka → hydro-calc),
026–027 (импорт → mod-hist → Kafka → hydro-calc), 034 (STALLED), 038 (SESSION_ERROR),
039 (Retry), 045 (Save → Play-model → hydro-calc), 047–048 (Timeshift → Kafka → hydro-calc),
049 (Timeshift: невалидный источник). Примечание: в классификации Части 1 HY-HIST-049
отнесён к интеграционным, а в §3.2 включён как системный (G26).

**Сводка (§4):** заглушки из HY-CALC — 26; перенесённые из HY-HIST — 19;
новые системные — 7; **всего — 52** (в §1/Части 1 — 53, G26).

## Чек-лист подготовки стенда (§5, 27 пунктов)

1. mod-hist UP — `GET /actuator/health` → `{"status":"UP"}`.
2. hydro-calculation UP — health check → `{"status":"UP"}`.
3. alarm-service UP — health check (порт уточнить) → `{"status":"UP"}`.
4. alarm-view-service UP — health check (порт уточнить) → `{"status":"UP"}`.
5. hmi-backend UP + прогрет — `GET /actuator/health` → `GET /diag/instance` → UP + HTTP 200 (не 503).
6. hmi-backend WS V2 — `ws://hmi-backend:8080/v2/hotlink`, PING → PONG в течение 5с.
7. Kafka: топики существуют — `kafka-topics --list` → `cspa-main`, `mod-hist-commands`, `mod-hist-results` в списке.
8. Kafka: `model_main_*` создаются динамически — создать сессию → топик `model_main_{id}` появился.
9. Kafka: `model_alarm_*` создаются динамически — запустить сессию с алармом → топик появился.
10. PostgreSQL: таблицы существуют — `SELECT tablename FROM pg_tables WHERE tablename IN ('sessions','session_results')` → ≥ 2 строки.
11. Redis: доступен — `redis.ping` → PONG.
12. Redis: ключи `session:*` отсутствуют — `redis.keys("session:*")` → пустой массив.
13. ClickHouse: доступность — `SELECT 1` → 1.
14. ClickHouse: тестовая история — `SELECT count(*) FROM history WHERE tag LIKE 'MT1.LU1.%' AND ts >= now() - INTERVAL 24 HOUR` → ≥ 10 000.
15. ClickHouse: история MT1.LU2 — ≥ 10 000 (для HY-SYS-047).
16. Конфигурация ТУ1 — `hmi.get("MT1.LU1.State.AlmHigh")` → ≠ null (уставка загружена).
17. Конфигурация ТУ2 — `hmi.get("MT1.LU2.State.AlmHigh")` → ≠ null (для HY-SYS-047).
18. Файлы импорта готовы — `import_test.xlsx`, `import_test.zip` существуют.
19. Начальное состояние — `api.list({})` + `redis.keys("session:*")` → пусто + пусто.
20. Kafka ACL: mod-hist → `model_main_*` — Allow produce/consume.
21. Kafka ACL: hydro-calc → `model_main_*` — Allow consume (вход) + produce (выход).
22. Kafka ACL: hydro-calc → `model_alarm_*` — Allow produce.
23. Kafka ACL: alarm-service → `model_alarm_*` — Allow consume.
24. hmi-backend: доступ к тестовым тегам — `GET /v2/tag-get?tagName=MT1.LU1.SGLU1.KIP1.TI.Press` + `X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]` → HTTP 200.
25. hmi-backend: запись в теги — `POST /v2/tag-set` (Press=5.0) + заголовки → HTTP 200.
26. alarm-service: API доступен — `GET [alarm-service]/api/health` (формат уточнить) → HTTP 200.
27. alarm-view-service: API доступен — `GET [alarm-view-service]/api/health` (формат уточнить) → HTTP 200.

## Правила исполнения (§6, 11 правил)

1. **Изоляция** — каждый сценарий стартует с начального состояния (KB-SYS-TESTSTAND-001). Teardown обязателен. После: `api.list({})` → пусто, `redis.keys("session:*")` → пусто.
2. **Ожидание** — `WAIT(n)` с запасом 5с. WS: timeout = ожидаемое + 10с. Kafka: max(interval, 30)с.
3. **Мульти-сервисная проверка** — результат проверяется в каждом сервисе цепочки. Минимум 2 источника для критичного результата.
4. **Щупы в Kafka** — в каждом сценарии, где данные проходят через Kafka, `kafka.consume` на промежуточных точках (SPOT_K1…K6).
5. **Промежуточные состояния** — для длинных каскадов проверяем каждое: Kafka (команда), Redis (статус), PG (запись), WS (событие); каждый раз фиксируется consumer lag проверяемого топика.
6. **Граничные значения** — 3 точки: ровно на границе, за границей на 1, за границей значительно.
7. **Фиксация фактического результата** — при сбое фиксировать фактический результат, не исправлять ожидаемый.
8. **Локализация** — в каждом сценарии: «Если X не сработало → проверить Y в Z» (критерии провала).
9. **Нет зависимостей между сценариями** — каждый сценарий самодостаточен; сложные предусловия выполняются внутри сценария.
10. **Кросс-сервисная согласованность** — значение в Kafka = значению в CH = значению через hmi.get = значению в alarm-service.
11. **Порядок событий** — для последовательных операций `ts_A < ts_B`. Если нарушено — баг в тайминге.

## Допущения (§7, 18 допущений)

| # | Допущение | Статус | Влияние |
|---|---|---|---|
| 1 | REST API alarm-service: путь, формат запроса/ответа | **Нет док-ции** | Блокирует все 26 заглушек (HY-SYS-001…026) + HY-SYS-046, 048 |
| 2 | REST API alarm-view-service: путь, формат | **Нет док-ции** | Аналогично |
| 3 | Kafka-топики alarm-service: из каких читает (model_alarm_* или cspa-main или оба) | **Нет док-ции** | Определяет, в каком топике ставить щуп SPOT_K3/K6 |
| 4 | Kafka-топики alarm-service: в какие пишет (output) | **Нет док-ции** | Для проверки «аларм дошёл до UI» |
| 5 | REST API data-manager: путь, формат для смены уставки | **Нет док-ции** | HY-SYS-049: используем hmi-backend как шлюз (допущение) |
| 6 | hmi.set публикует в hot topic, который = model_main_{sessionId} | **Доказано док-цией hmi-backend**, механизм привязки **уточнить** | Если hot topic ≠ model_main_{id} — данные не дойдут до hydro-calc |
| 7 | hmi.get читает из DataStream (Kafka consumer → буфер), не из Redis | **Доказано док-цией** | Для щупов: hmi.get — не «мгновенное» чтение, есть задержка до 50мс (агрегация) |
| 8 | `hmi.wait_alarm` — WS V2 SUBSCRIBE на тег аларма + ожидание SUB_ANSWER | **Из тестплана hydro-calculation** | Механизм: SUBSCRIBE → TAG_SET (или Kafka) → SUB_ANSWER с value=true |
| 9 | Hydro-calculation вызывает REST API alarm-service (не Kafka) для отправки аларма | **Из C4** | |
| 10 | Конфигурация ТУ (уставки, Disable, Control) хранится в data-manager и приходит в hydro-calc через кеш Redis | **Из C4** | Для HY-SYS-049: смена уставки → Kafka → hydro-calc подхватывает |
| 11 | ClickHouse: таблица `history`, поля: tag, value, invalid, ts | **Нет схемы** | Используем как есть, уточним позже |
| 12 | PostgreSQL: таблица `sessions`, поля: id, status, watermark, processing_mode, created_at, started_at, closed_at | **Нет схемы** | Используем как есть |
| 13 | Saved-сессии хранятся в ClickHouse (таблица `saved_session_data`) | **Из тестплана hydro-history-and-model** | HY-SYS-052: сравнение с исходной |
| 14 | `api.start/stop/pause/resume/close/advance/setSpeed/retry` — псевдо-endpoint'ы | **Из тестплана hydro-history-and-model** | Верифицировать по коду перед исполнением (G22) |
| 15 | Max speedRatio = 60000 (60×) по UI, возможно 100000 в коде | **Из UI** | HY-SYS-034: используем 60000 (G21) |
| 16 | WS не буферизует события при отключении | **Доказано** | При переподключении — только новые события |
| 17 | Minuteman: WS-сессия без PING > 30с → hmi-backend будит/закрывает | **Доказано** | В длительных сценариях: PING каждые 15–20с |
| 18 | hmi-backend: 503 до AppWarmUp | **Доказано** | Чек-лист: после health=UP ждать diag/instance=200 |

## Блокирующие вопросы до начала исполнения (§8)

| # | Вопрос | Блокирует | Приоритет |
|---|---|---|---|
| 1 | REST API alarm-service (путь, метод, body, response) | 26 заглушек + HY-SYS-046, 048 | **P0** |
| 2 | REST API alarm-view-service (путь, метод, body, response) | 26 заглушек | **P0** |
| 3 | Какие Kafka-топики читает/пишет alarm-service | Щупы SPOT_K3/K6 | **P0** |
| 4 | Верификация псевдо-endpoint'ов mod-hist (13 шт.) | HY-SYS-027…045 | **P0** |
| 5 | REST API data-manager (если существует отдельный) | HY-SYS-049 | **P1** |
| 6 | Механизм привязки hot topic hmi-backend к model_main_{sessionId} | Все сценарии с hmi.set → model_main | **P0** |
| 7 | Schema ClickHouse `history` | Подготовка тестовых данных | **P1** |
| 8 | Schema PostgreSQL `sessions` | Кросс-проверки | **P2** |

## План исполнения (§9, §11)

**Фаза 1: Разблокировка (P0):** (1) получить док-цию alarm-service / alarm-view-service →
разблокировка 26 заглушек; (2) верификация псевдо-endpoint'ов mod-hist по коду →
разблокировка 19 перенесённых; (3) уточнить Kafka-топики alarm-service → корректные
щупы; (4) уточнить привязку hot topic → model_main_{id} → корректная маршрутизация.

**Фаза 2: Smoke (~30 мин):** HY-SYS-048, 050, 027, 045, 035, 047.

**Фаза 3: Core (~2 часа):** HY-SYS-028, 029, 046, 049, 051, 037, 038, 042, 052
+ 26 заглушек (по 45с).

**Фаза 4: Extended (~1.5 часа):** HY-SYS-039, 040, 041, 043, 044, 030, 031, 032,
033, 034, 036.

**Итого (§11):** всего сценариев 52 (по §1 — 53, G26); «готовы к исполнению» 26
(19 перенесённых + 7 новых; фактически полностью описаны 25 — HY-SYS-049 без тела,
G27); заглушки (ждут док-цию alarm-service) — 26; блокирующие вопросы P0 — 4
(по §8 их 5, если считать вопрос 6); общее время прогона ~4–5 часов.




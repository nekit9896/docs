# Решения по клиенту hmi-backend и доставке sdku-test-tools (2026-11-19)

Статус: принято. Источник: интервью (grilling) с владельцем проекта, раунды Q1–Q26.
Область: `sdku-test-tools`, `hydro-backend-tests`, `docs` (проект `evoscada`).
Продолжение журнала `2026-11-17-sdku-tests-org.md`; в коде `sdku-test-tools`
цитируется как «решение D-2026-11-19».

## Принятые решения

| # | Решение |
|---|---|
| D38 | **REST-канон клиента hmi-backend** — семейство `tag-*` версии V2: `POST /v2/tag-set`, `POST /v2/tags-set`, `GET /v2/tag-get?tagName=`, `POST /v2/tags-get`, `POST /v2/tags-get-history`. Формулировка «`/v2/hmi/*`» отброшена как необоснованная: не подтверждается KB-HMI-REST-VAL-001 / KB-HMI-REST-QUERY-001. Единый источник контракта — `docs/specs/knowledge/hmi-backend/`. |
| D39 | **WS-протокол клиента — только подписки**: `SUBSCRIBE` / `UNSUBSCRIBE` / `UNSUBSCRIBE_ALL` / `PING` и поток `SUB_ANSWER` (`/v2/hotlink`, кадры `CommandDto`). Синхронные `TAG_GET`/`TAG_SET`/`TAG_FIND`/`CALL_ANSWER` сервер V2 поддерживает, но клиент их не использует: чтение/запись — через REST (D38). Расхождение «сервер умеет — клиент не реализует» зафиксировано тикетом **G42** (`docs/meta/discrepancies-2026-11-19.md`) — решение о закрытии/реализации за владельцем. |
| D40 | **Заголовки идентификации оператора (`X-USER-*`)**: запись — `X-USER-FULLNAME` и `X-USER-ALLOW-PATTERNS` обязательны; чтение/подписки — `X-USER-GET-ALLOW-PATTERNS` (дефолт `[".*"]`); `X-USER-FORBIDDEN-PATTERNS`/`X-USER-GET-FORBIDDEN-PATTERNS` опциональны (приоритет над allow); `ORGUNIT`/`ORGPATH`/`POSITION`/`IP` опциональны. Имена переменных окружения — `HMI_USER_*`, владелец — `hydro-backend-tests/.env.example` (D13). |
| D41 | **Доставка Docker-only (пересматривает D7 и D8)**: публикации wheel/PyPI НЕТ. Из наших репозиториев пакуется только образ **`evoscada_docker/sdku_test_tools:<semver>`** (Dockerfile и `scripts/build_and_push.sh` в `sdku-test-tools`, сборка CI-пайплайном тулзов); pip-зависимости ставятся из корпоративного Nexus (pip-прокси), креды — из GitLab CI variables. Репозиторий автотестов НЕ пакуется: тесты гоняются в этом образе над чекаутом (job берёт образ как `image:`). Локально — `pip install -e ../sdku-test-tools`. `hydro-backend-tests/Dockerfile` удалён как утративший смысл (восстанавливается из git). |
| D42 | **Политика ошибок и ретраев**: инфраструктурные ошибки НЕ маскируются — тест падает (FAILED, не skip) с полной диагностикой в Allure/логах. `retry_call` — ≥3 попытки с экспоненциальным backoff, только для `InfraError(retryable=True)`; `sleep` — инъецируемый параметр (тестируемость). Таймауты чтения для неидемпотентных методов (POST) не повторяются (запрос мог быть применён); `5xx` повторяется (запрос не обслужен); `4xx` — штатный ответ API → `HmiApiError`, не повторяется (негативные проверки). Ошибки API/протокола не ретраятся никогда. |
| D43 | **WS-соединение живёт в фоновом потоке со своим event loop** (по образцу `training/clients/ws_connection_manager.py`): блокирующие ожидания тестов не останавливают пинги (иначе сервер закрывает сессию по Minuteman/`killStaleSessions`). Supervisor поддерживает соединение, реконнектится и возобновляет подписки; отсечение устаревших значений — механизмом watermark/seq в `WsMessageDispatcher`. |
| D44 | **Значения сравниваются в нормализованном строковом представлении API V2** (`normalize_value`: булевы — `true`/`false`, прочее — `str`): представления значений в V2 строковые, приведение типов Python даёт ложные расхождения (`True != "true"`). |

## Связанные изменения

- `hydro-backend-tests/.env.example` дополнен блоком `HMI_USER_*` (D40).
- README обоих репозиториев приведены к Docker-only модели (D41).
- Заготовки `.gitlab-ci.yml` обоих репозиториев созданы **закомментированными**:
  триггеры пайпов остаются несогласованными (D9/D20).
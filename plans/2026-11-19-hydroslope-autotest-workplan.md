# Рабочий план: автотесты Гидроуклона — 2026-11-19

Статус: в работе. Владелец плана — исполнитель, вердикты — за владельцем проекта.
Канон контрактов и решений: `docs/decisions/2026-11-19-hmi-client-contract.md`
(D38–D44), `docs/decisions/2026-11-17-sdku-tests-org.md`. Оценки задач —
`docs/plans/automation-roadmap.md`; speckit-задачи — `docs/specs/001-hydro-autotest-suite/tasks.md`
(маппинг путей — вставки «Адаптация 2026-11-19», расхождение G43).

## Текущее состояние

- **Каркас `sdku-test-tools` готов** (92 юнит-теста, без сети; black/isort/flake8 чистые):
  - `clients/`: `HttpClient` (retry/диагностика), `HmiClient` (REST V2 tag-семейство: set/set_batch/get/get_batch/history), `HotlinkClient` (WS-подписки: subscribe/unsubscribe/unsubscribe_all/ping/wait_value/wait_alarm);
  - `managers/`: `WsConnectionManager` (фоновый loop, пинги, реконнект, resubscribe), `WsMessageDispatcher` (watermark/seq, wait_for);
  - `utils/`: errors, retry (инъекция sleep), env, logging (structlog), records, ws_codec (CommandDto), user_headers (X-USER-*), allure_support.
- **Инфраструктура доставки**: `Dockerfile` + `scripts/build_and_push.sh` (образ `evoscada_docker/sdku_test_tools:<semver>`), черновики `.gitlab-ci.yml` обоих репо (закомментированы, триггеры не согласованы — D20), README приведены к Docker-only (D41).
- **Документация**: журнал решений D38–D44, G42/G43 в `docs/meta/`, `.env.example` дополнен `HMI_USER_*`.

## Этапы

### 1. Каркас sdku-test-tools — ✅ ГОТОВО
utils + HttpClient/HmiClient/HotlinkClient + WS-менеджеры + юнит-тесты + Docker/CI-заготовки.

### 2. Сценарный слой hydro-backend-tests — ⏳ В РАБОТЕ
- [ ] Фикстуры стенда (session/function): `hmi` (HmiClient), `hotlink` (HotlinkClient), env-конфиг из `.env` (D13).
- [ ] Правила кейсов из тест-плана (§ «Правила исполнения»): фиксированные окна ожидания, маркеры `@pytest.mark.case_conflu(...)`, восстановление состояния (RESET участка).
- [ ] Модели домена (датаклассы расчётных моделей) и конфиги датасетов.

### 3. Пилот HY-CALC-001 — ⏳ СЛЕДУЮЩИЙ
Первый сквозной кейс: подготовка → действие → ожидание → сверка с эталоном.
Цель: проверить выбранный контракт (D38/D39) и тайминги ожиданий на реальном стенде,
закрыть вопросы стенда из open-questions (теги, порты, значения).

### 4. Раскатка HY-CALC (85 кейсов) — 📋 ПЛАН
По пакетам функциональности (§ тест-плана) с трассировкой в `docs/specs/trace/case-module-matrix.md`.

### 5. HY-HIST (48) + системные (52) + отчётность — 📋 ПЛАН
После стабилизации HY-CALC; отчётность JUnit/JSON — контракт уточняется (G43).

## Открытые вопросы к владельцу

1. **G42**: закрыть синхронные WS-команды как не нужные или заказать реализацию?
2. **G43**: полное переписывание speckit-задач под фактические пути или достаточно маппинга?
3. Триггеры GitLab CI (D20) и версия образа тулзов для прогонов.
4. Контракт отчётности (вердикты `passed/failed/skipped`, структура `mismatches`) — подтверждение после пилота.
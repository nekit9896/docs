# Источник истины по hmi-backend: дамп кода и WS-канон клиента (2026-11-25)

Статус: принято. Источник: интервью (grilling) с владельцем проекта, раунды Q1–Q18.
Область: `docs`, `sdku-test-tools`. Продолжение журнала `2026-11-19-hmi-client-contract.md`
(D38–D44); в коде `sdku-test-tools` цитируется как «решение D-2026-11-25».

## Контекст

В `docs/real_repo_dump/hmi-backend` добавлен полный дамп кода репозитория
hmi-backend (778 КБ, 16 665 строк, 151 файл: Java/Spring-бэкенд, `API.md`,
`client/index.html`, `tag-monitor*.html`). Попытка подключения `sdku-test-tools`
по WSS к стенду проваливалась: `WS_URL` был задан как `wss://<STAND>` без пути,
сервер на `/` редиректит на `/tag-monitor.html` (`RootController`), и
вебсокет-библиотека падала на `scheme isn't ws or wss`.

## Принятые решения

| # | Решение |
|---|---|
| D45 | **Дамп кода полностью заменяет `confluence/hmi-backend-descr.md`** как источник фактов по hmi-backend. Файл удалён физически (восстанавливается из git); `source`-ссылки 11 фрагментов KB-HMI-* перепривязаны к дампу в формате `real_repo_dump/hmi-backend:L####-L#### (путь/файла)`. Индекс навигации — `real_repo_dump/hmi-backend-INDEX.md` (скелет — генерируется из дампа скриптом, описания — вручную). Сопутствующие правки: `confluence/README.md`, `.clinerules/00-docs-map.mdc`, `specs/INDEX.md`, `README.md`. |
| D46 | **Приоритет источников**: код (дамп) — истина по фактически реализованному контракту (протокол, эндпоинты, поведение); confluence-описания и устные описания — исторические/намерения. Расхождения фиксируются в `meta/discrepancies-*` с номером G; содержательных правок по догадкам не делаем. |
| D47 | **WS-конфигурация клиента и транспорт X-USER**: `WS_URL` — **базовый** URL стенда (`wss://<STAND>` или `https://<STAND>`), клиент сам строит `/v2/hotlink?<X-USER params>`; передача полного URL — явный override. Идентификация при рукопожатии — **и query-параметрами, и HTTP-заголовками** одновременно: `x-user-fullname` в query — двойное URL-кодирование (как страница `tag-monitor.html`: `encodeURIComponent` + `URLSearchParams`; сервер декодирует дважды — `getParameter` + `URLDecoder.decode`), прочие X-USER-параметры — однократное кодирование; в HTTP-заголовках значения — однократно URL-кодированными (сервер применяет `URLDecoder.decode` к значению заголовка). |
| D48 | **Полный WS-канон клиента** = весь `Command` enum сервера (`SUBSCRIBE`, `UNSUBSCRIBE`, `UNSUBSCRIBE_ALL`, `SWITCH`, `PLAY`, `STOP`, `SEEK`, `SET_MILLIS_PER_TICK`, `PING`, `TAG_GET`, `TAG_SET`, `TAG_FIND`, `TAG_NAMES`, `OBJECT_TYPES`). `SWITCH {"target":"LIVE"}` — обязательный шаг инициализации сессии (в т.ч. после реконнекта). D39 пересмотрен: синхронные WS-команды клиент реализует (закрывает G42 как «реализовано»); REST-канон D38 остаётся основным для чтения/записи в тестах. V1-эндпоинт `/hotlink` и режим моделирования (`modelSessionId` → `HotlinkWebSocketHandlerV2Routed`) — только документируются, в клиент не включаются. |

## Связанные изменения

- Журнал расхождений `meta/discrepancies-2026-11-25.md` (G44+); G42 — статус
  «закрыт: реализовано (D48)» в `meta/discrepancies-2026-11-19.md`.
- Порядок работ: решения → документация (индекс дампа + реверификация
  KB-HMI-*) → WS-клиент во «полном виде» с юнит-тестами.
- Валидация клиента: юнит-тесты `sdku-test-tools/tests/` + обновлённый
  `scripts/smoke_ws_client.py`; живой прогон по стенду — владелец.

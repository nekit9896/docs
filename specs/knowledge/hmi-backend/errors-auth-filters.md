---
id: KB-HMI-ERR-001
title: Обработка ошибок, фильтры, авторизация HTTP-заголовками
service: hmi-backend
group: api
source: real_repo_dump/hmi-backend:L5863-L6205 (errors/*); L5927-L6032 (errors/ControllerErrorsHandler.java); L6206-L6363 (filter/*); L11652-L11693 (utils/RequestUtils.java)
requires: []
related: [KB-HMI-REST-VAL-001, KB-HMI-WS-001, KB-HMI-SVC-001]
status: needs-review
---

# Ошибки, фильтры, авторизация

## Иерархия исключений и маппинг в HTTP

Все исключения наследуются от `RuntimeException` **напрямую** (общего базового
класса нет). Маппинг — `ControllerErrorsHandler` (L5927-L6032, приоритет
HIGHEST) + `ControllerDefaultErrorsHandler` (L5895-L5926, fallback):

| Исключение | HTTP | Примечание |
|---|---|---|
| `ApplicationLogicException` | **520** | Бизнес-логика (нештатный код) |
| `BadRequestException` | 400 | Некорректный запрос |
| `TagNotFoundException` | 404 | Тег не найден |
| `ValueConversionException` | 400 | Несоответствие типа значения |
| `InvalidProtocolBufferException` | 400 | Ошибка Protobuf-парсинга |
| `ForbiddenException` | 403 | Нарушение X-USER-паттернов |
| `NotFoundException` | **500** | (так маппится в коде, не 404) |
| `TagSetException` | **500** | (так маппится в коде, не 400) |
| `TagNotAvailable` | 500 (fallback) | Отдельного handler нет |
| `WebClientErrorException` | 500 (fallback) | Отдельного handler нет |
| `SQLException`, `IllegalStateException`, прочие | 500 | — |

Обработчики: `ControllerErrorsHandler` (исключения контроллеров → JSON
`ErrorMessage`), `ControllerDefaultErrorsHandler` (fallback).

Формат ошибки (`ErrorMessage`, L6044-L6050):
```json
{"errorCode": "tnt.tnscada.hmi.errors.TagNotFoundException", "message": "Tag not found: SO.ME.TAG"}
```
Для ошибок по тегам в `POST /v2/tags-set` — `TagErrorMessage` (record,
L6099-L6106): `{"tagName": ..., "errorCode": ..., "message": ...}`.

## Фильтры и инфраструктура

- `RequestInfoFilter` — извлекает IP клиента (`RequestUtils.getClientIpAddr`),
  identity пользователя (`RequestUtils.getAnyUserIdentity`), логгирует запрос.
- `MultiReadHttpServletRequest` — обёртка для многократного чтения body
  (нужна фильтру + контроллеру).
- `KafkaSender` — отправка в обычные топики и compact-топики (метаданные).

## Авторизация `X-USER-*` (HTTP-заголовки и query-параметры, контроль на уровне бизнес-логики)

| Заголовок | Обязательность | Описание |
|---|---|---|
| `X-USER-FULLNAME` | Required при записи | Идентификация, сохраняется в Grant-Access-Audit |
| `X-USER-ID` | Optional | ID пользователя (для аудита) |
| `X-USER-IP` | Optional | IP для логов аудита/алармов |
| `X-USER-ALLOW-PATTERNS` | **Required** при записи | JSON-массив regex, разрешающий доступ |
| `X-USER-GET-ALLOW-PATTERNS` | **Required** при чтении | JSON-массив regex, разрешающий чтение |
| `X-USER-FORBIDDEN-PATTERNS` | Optional | Чёрный список, **приоритет над allow** |
| `X-USER-GET-FORBIDDEN-PATTERNS` | Optional | Чёрный список для чтения |
| `X-USER-LOGIN` | Optional | Альтернативный заголовок identity |

> **WebSocket V2 (D47, G45):** при рукопожатии параметры авторизации передаются
> **query-параметрами URL и/или HTTP-заголовками** (сервер: `getAnyUserIdentity`
> → заголовки, фолбэк — query `x-user-fullname` с двойной декодификацией); в
> кадрах — поле `headers` `CommandDto` (для `X-USER-GET-ALLOW-PATTERNS` подписок);
> query-параметры URL мержатся с `headers` кадров как умолчания сессии.
> **REST:** на уровне контроллеров `X-USER-FULLNAME` объявлен `required=false`
> (L2988); обязательность при записи обеспечивается бизнес-логикой/аудитом.

Порядок проверки `RequestUtils`: `X-USER-LOGIN` → `X-USER-FULLNAME` →
`x-user-fullname` → `X-USER-ID`. Для IP: `X-Forwarded-For` → `Proxy-Client-IP` →
`WL-Proxy-Client-IP` → `HTTP_CLIENT_IP` → `HTTP_X_FORWARDED_FOR` →
`request.getRemoteAddr()`.

> ⚠️ **G13 (needs-review):** в REST-описании `GET /v2/tag-get` заголовок
> `X-USER-GET-ALLOW-PATTERNS` — *optional* (default `[".*"]`), а в этой таблице —
> *Required при чтении*. Требуется уточнение фактической обязательности.
---
id: KB-HMI-ERR-001
title: Обработка ошибок, фильтры, авторизация HTTP-заголовками
service: hmi-backend
group: api
source: confluence/hmi-backend-descr.md#«Обработка ошибок», «Фильтры и инфраструктура», «Авторизация (HTTP-заголовки)»
requires: []
related: [KB-HMI-REST-VAL-001, KB-HMI-WS-001, KB-HMI-SVC-001]
status: needs-review
---

# Ошибки, фильтры, авторизация

## Иерархия исключений

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

Обработчики: `ControllerErrorsHandler` (исключения контроллеров → JSON
`ErrorResponseApi`), `ControllerDefaultErrorsHandler` (fallback).

Формат ошибки:
```json
{"message": "Описание ошибки", "tag": "SO.ME.TAG", "timestamp": 123456789}
```
(`tag` — для TagErrorMessage.)

## Фильтры и инфраструктура

- `RequestInfoFilter` — извлекает IP клиента (`RequestUtils.getClientIpAddr`),
  identity пользователя (`RequestUtils.getAnyUserIdentity`), логгирует запрос.
- `MultiReadHttpServletRequest` — обёртка для многократного чтения body
  (нужна фильтру + контроллеру).
- `KafkaSender` — отправка в обычные топики и compact-топики (метаданные).

## Авторизация (HTTP-заголовки, контроль на уровне бизнес-логики)

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

> **WebSocket V2:** параметры авторизации передаются в поле `headers` JSON-кадра.

Порядок проверки `RequestUtils`: `X-USER-LOGIN` → `X-USER-FULLNAME` →
`x-user-fullname` → `X-USER-ID`. Для IP: `X-Forwarded-For` → `Proxy-Client-IP` →
`WL-Proxy-Client-IP` → `HTTP_CLIENT_IP` → `HTTP_X_FORWARDED_FOR` →
`request.getRemoteAddr()`.

> ⚠️ **G13 (needs-review):** в REST-описании `GET /v2/tag-get` заголовок
> `X-USER-GET-ALLOW-PATTERNS` — *optional* (default `[".*"]`), а в этой таблице —
> *Required при чтении*. Требуется уточнение фактической обязательности.
---
id: KB-HMI-REST-VAL-001
title: REST — текущие значения тегов (п.1–5: tag-get, tag-set, tag-set-and-wait)
service: hmi-backend
group: api
source: confluence/hmi-backend-descr.md#«REST: текущие значения тегов» (п.1–5)
requires: [KB-HMI-TAG-001]
related: [KB-HMI-ERR-001, KB-HMI-CONFIG-001, KB-HMI-REST-QUERY-001]
status: verified
---

# REST: текущие значения тегов

## 1. `GET /v2/tag-get`

| Параметр | Тип | Обязательность | Примечание |
|---|---|---|---|
| `tagName` | query | required | — |
| `X-USER-GET-ALLOW-PATTERNS` | header | optional | default `[".*"]`, JSON-массив regex |
| `X-USER-GET-FORBIDDEN-PATTERNS` | header | optional | JSON-массив regex, приоритет над allow |
| `X-USER-FULLNAME` | header | optional | — |

**Ответ:** `{"tag":"MN.TU.TAGNAME..,","data":{"value":"some value","invalid":false,"ts":123456789,"ts2":123456789}}`

> **V1** (`GET /tag-get`): вложенная типизация значения (`HmiMsg.TagValueMsg`).

## 2. `GET|POST /v2/tags-get`

- **GET:** query `tagNames` (массив строк); **POST:** body — JSON-массив адресов.
- Заголовки как в п.1. **Ответ:** массив объектов структуры п.1.
- **V1** (`GET|POST /tags-get`): обёртка `BatchedTagValueMsg` → `{"tagValueBatch":[...]}`.

## 3. `POST /v2/tag-set`

| Заголовок | Обязательность | Примечание |
|---|---|---|
| `X-USER-FULLNAME` | **required** | Идентификация, сохраняется в Grant-Access-Audit |
| `X-USER-IP` | optional | IP для логов аудита/алармов |
| `X-USER-ALLOW-PATTERNS` | **required** | JSON-массив regex |
| `X-USER-FORBIDDEN-PATTERNS` | optional | JSON-массив regex |

**Body:** `{"tag":"MN.TU.TAGNAME","data":{"value":"new value","invalid":false,"ts":123456789}}`
**Ответ:** `200 OK`. При `use-sync-set=true` — после подтверждения применения.

> Валидация типа значения против типа тега (`ProtoValidator`) → `400` +
> `ValueConversionException`. **V1** (`POST /tag-set`): body — `HmiMsg.TagValueMsg`.

## 4. `POST /v2/tags-set`

Body — массив объектов `TagSetRequest`. Заголовки аудита как в п.3. Ответ `200 OK`.
**V1** (`POST /tags-set`): body — `BatchedTagValueMsg`.

## 5. `POST /tag-set-and-wait` **(только V1)**

Запись в один тег + блокировка HTTP-ответа до появления ожидаемого значения на
связанном теге. Body: `TagSetAndWaitDTO`. В V2 отсутствует — ожидание вынесено
на WebSocket (см. KB-HMI-WS-001).
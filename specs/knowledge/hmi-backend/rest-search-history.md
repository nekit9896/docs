---
id: KB-HMI-REST-QUERY-001
title: REST — поиск/навигация (п.6–9) и история ClickHouse (п.10–12)
service: hmi-backend
group: api
source: confluence/hmi-backend-descr.md#«REST: поиск и навигация» (п.6–9), «REST: история (ClickHouse)» (п.10–12)
requires: []
related: [KB-HMI-REST-VAL-001, KB-HMI-SVC-001, KB-HMI-CONFIG-001]
status: verified
---

# REST: поиск, навигация, история

## Поиск и навигация

### 6. `GET /v2/tag-names`
Поиск тегов по паттернам с фильтрацией по типам.

| Параметр | Тип | Примечание |
|---|---|---|
| `objectPattern` | query | regex для имени объекта |
| `parameterPattern` | query | regex для имени параметра |
| `types` | query (массив) | Фильтр по типам (NPS, NCS и т.д.) |
| `skipFolders` | query | Пропускать папки |
| `limit` | query | Ограничение результатов |

**Ответ:** `array of string` (имена тегов).

### 7. `GET /object-types` — список типов объектов. Параметр `pattern` (regex). Ответ: `array of string`.
### 8. `GET /object-names` — список объектов. Параметры: `pattern` (regex), `type` (optional, имя object-type). Ответ: `array of string`.
### 9. `GET /tag-names` **(V1, legacy)** — список тегов по regex. Параметры: `pattern`, `type` (optional). Ответ: `array of string`.

> V1 также имеет `/tag-names-labels`, `POST /get-tags-meta` — устаревшие, без
> кэширования/фильтрации/лимитов.

## История (ClickHouse)

### 10. `POST /v2/tags-get-history`
**Body:**
```json
{"startTime": 1706592000000, "endTime": 1706595600000, "tags": ["SO.ME.TAG1"],
 "limit": 1000, "offset": 0, "returnBounds": false}
```
**Ответ:** объект с ключами-тегами, значения — массивы записей
`{ts, ts2, quality, invalid, value}`.

> Внутренне запрос делится на батчи по **10 000** ключей (ограничение ClickHouse
> на размер SQL: 256 KiB). **V1** (`POST /tags-get-history`): легаси-сервис с
> `timeBucketWidth` (агрегация по интервалам), V2 — прямой запрос из CH.

### 11. `POST /v2/tags-get-history-iso`
Аналог п.10, метки времени ISO8601. **Body:** `HistoryISORequestDTO`
(`startTime`/`endTime` — строки ISO8601). **Ответ:** `RecordValueISO`.

### 12. `POST /tags-get-history-flat` **(V1, активен во всех версиях)**
Линейный массив архивных записей со сжатыми ключами JSON. **Body:** аналог п.10 +
`timeBucketWidth` (опционально). **Ответ:** `array of HistoryRecordShortNameDTO`.

Сервисная логика: `HistoryServiceLegacy` (`tagGetHistoryGroupedByTag`,
`tagGetHistoryFlat`) — см. KB-HMI-SVC-001.
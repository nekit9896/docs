---
case_conflu: HY-HIST-032
title: Экспорт в JSON (структурированный)
service: hydro-history-and-model
group: export
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-032
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-030, HY-HIST-031]
status: verified
---

# HY-HIST-032 — Экспорт в JSON (структурированный)

**Требование:** R-HYDR-068
**Описание:** Экспорт в JSON — для программной обработки. В отличие от CSV
(плоский), JSON группирует данные по тегам и содержит метаданные (sessionId,
период, единицы измерения).

**Формат JSON:**

```json
{
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "processingMode": 0,
  "period": {"start": "2026-11-09T08:00:00Z", "end": "2026-11-09T08:02:00Z"},
  "exportedAt": "2026-11-09T12:00:00Z",
  "tags": [
    {
      "tag": "MT1.LU1.SGLU1.KIP1.TI.Head",
      "unit": "m",
      "count": 120,
      "data": [
        {"ts": "2026-11-09T08:00:00Z", "value": 663.2, "invalid": false},
        {"ts": "2026-11-09T08:00:01Z", "value": 663.3, "invalid": false}
      ]
    },
    {
      "tag": "MT1.LU1.SGLU1.KIP1.TI.PressDelta",
      "unit": "kgf/cm2",
      "count": 120,
      "data": ["..."]
    }
  ]
}
```

**Предусловие:** Сессия historical завершена (status = 8), есть данные.

**Действия:**

1. `api.export_(id, format="json", startTime="2026-11-09T08:00:00Z", endTime="2026-11-09T08:02:00Z")` ⚠️ —
   JSON за 2 минуты; система группирует данные по тегам, добавляет метаданные
2. Проверить: HTTP 200, `Content-Type: application/json`
3. Парсить JSON:
   - `sessionId` = тестовый UUID
   - `processingMode` = 0 (historical)
   - `period.start` = 08:00:00, `period.end` = 08:02:00
   - `tags` — массив, длина ≥ 1
   - Для каждого тега: `data` — массив, `count` = длина `data`
4. Проверить: для тега `Head` значение `data[0].value ≈ 663.2` (согласуется с
   CSV из HY-HIST-030)

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 2 | HTTP 200, application/json | Корректный формат |
| 3 | Валидный JSON, структура соответствует | Метаданные + данные |
| 4 | `Head[0].value ≈ 663.2` | Согласованность с CSV |

**Teardown:** `api.close(id)` ⚠️ → `RESET()`

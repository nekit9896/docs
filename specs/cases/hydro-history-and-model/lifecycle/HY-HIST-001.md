---
case_conflu: HY-HIST-001
title: Создание historical-сессии: базовый сценарий
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-001
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SESSIONS-001]
related: [HY-HIST-002, HY-HIST-003, HY-HIST-004, HY-HIST-005]
status: verified
---

# HY-HIST-001 — Создание historical-сессии: базовый сценарий

**Требование:** R-HYDR-050, R-HYDR-051
**Описание:** Оператор создаёт сессию historical для перерасчёта истории за
период 08:00–12:00 со скоростью 2× (speedRatio=2000). Система проверяет
валидность параметров, аллоцирует ресурсы, возвращает sessionId. Сессия в
состоянии CREATED (0).

**Обоснование:**

- `processingMode = 0` (historical) — основной режим перерасчёта
- `startTime = 08:00`, `targetTime = 12:00` — 4-часовой диапазон
- `speedRatio = 2000` (2×) — скорость: 4 ч / 2 = 2 ч реального
- `targets = ["MT1.LU1"]` — один ТУ

**Предусловие:**

- Стенд в начальном состоянии (KB-HM-TESTSTAND-001, §2.3)
- В ClickHouse данные за 08:00–12:00 для MT1.LU1
- Конфигурация ТУ1 загружена
- Нет активных сессий

**Действия:**

1. `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T12:00:00Z","speedRatio":2000,"targets":["MT1.LU1"]})`
2. Проверить ответ: `sessionId` не пуст, `status = 0` (CREATED), `processingMode = 0`
3. `api.get(sessionId)` ⚠️ — убедиться, что сессия сохранена
4. `api.list({status: 0})` ⚠️ — сессия в списке

**Ожидаемый результат:**

- Шаг 1: HTTP 201, тело:

```json
{
  "sessionId": "<uuid>",
  "processingMode": 0,
  "status": 0,
  "startTime": "2026-11-09T08:00:00Z",
  "targetTime": "2026-11-09T12:00:00Z",
  "speedRatio": 2000,
  "targets": ["MT1.LU1"],
  "watermark": null,
  "progress": 0.0
}
```

- Шаг 3: все поля из шага 1, `startedAt = null`, `status = 0`
- Шаг 4: одна сессия с данным sessionId
- PostgreSQL: строка в `sessions`, `status = 0`

**Teardown:** `api.close(sessionId)` ⚠️ → `WAIT(5)` → `RESET()`

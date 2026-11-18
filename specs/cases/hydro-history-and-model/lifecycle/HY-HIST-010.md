---
case_conflu: HY-HIST-010
title: Закрытие: DONE → CLOSING → CLOSED
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-010
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SESSIONS-001]
related: [HY-HIST-009, HY-HIST-011, HY-HIST-041]
status: verified
---

# HY-HIST-010 — Закрытие: DONE → CLOSING → CLOSED

**Требование:** R-HYDR-055
**Описание:** Закрытие остановленной сессии. Освобождение ресурсов.

**Предусловие:** Сессия DONE (status=8).

**Действия:**

1. `ws.subscribe(sessionId)`
2. `api.close(sessionId)` ⚠️
3. `ws.wait_event(sessionId, 5, timeout=15)` — SESSION_CLOSED (type=5)
4. `api.get(sessionId)` ⚠️
5. `api.start(sessionId)` ⚠️ — попытка запуска
6. `api.stop(sessionId)` ⚠️ — попытка остановки

**Ожидаемый результат:**

- Шаг 3: `type=5` (SESSION_CLOSED)
- Шаг 4: `status = 11` (CLOSED), `closedAt` заполнен
- Шаг 5: HTTP 409 `{"error":"Session is closed"}`
- Шаг 6: HTTP 409
- PostgreSQL: `status = 11`, `closed_at` заполнен

**Teardown:** `RESET()`

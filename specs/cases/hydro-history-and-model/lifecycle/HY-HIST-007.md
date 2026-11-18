---
case_conflu: HY-HIST-007
title: Пауза: PLAYING → PAUSED
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-007
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SESSIONS-001, KB-HM-WATERMARK-001]
related: [HY-HIST-008, HY-HIST-009, HY-HIST-013]
status: verified
---

# HY-HIST-007 — Пауза: PLAYING → PAUSED

**Требование:** R-HYDR-053
**Описание:** Приостановка. Watermark фиксируется, не сбрасывается.

**Предусловие:** Сессия PLAYING, `watermark ≈ 09:30:00`.

**Действия:**

1. `ws.subscribe(sessionId)`
2. `api.pause(sessionId)` ⚠️
3. `ws.wait_event(sessionId, 2, timeout=10)` — SESSION_PAUSED (type=2)
4. `api.get(sessionId)` ⚠️
5. `api.watermark(sessionId)` ⚠️ → `wm_pause`
6. `WAIT(10)`
7. `api.watermark(sessionId)` ⚠️ → `wm_after`

**Ожидаемый результат:**

- Шаг 3: `type=2`
- Шаг 4: `status = 2` (PAUSED)
- Шаг 5: `wm_pause = "2026-11-09T09:30:00Z"` (зафиксировано)
- Шаг 7: `wm_after = wm_pause` (не изменилось за 10 с)

**Teardown:** `api.resume(sessionId)` ⚠️ → `api.stop` ⚠️ → `api.close` ⚠️ → `RESET()`

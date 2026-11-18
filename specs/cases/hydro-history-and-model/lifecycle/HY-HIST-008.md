---
case_conflu: HY-HIST-008
title: Возобновление: PAUSED → PLAYING
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-008
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SESSIONS-001, KB-HM-WATERMARK-001]
related: [HY-HIST-007, HY-HIST-009]
status: verified
---

# HY-HIST-008 — Возобновление: PAUSED → PLAYING

**Требование:** R-HYDR-053
**Описание:** Продолжение с того же watermark.

**Предусловие:** Сессия PAUSED, `watermark = 09:30:00`.

**Действия:**

1. `ws.subscribe(sessionId)`
2. `api.resume(sessionId)` ⚠️
3. `ws.wait_event(sessionId, 3, timeout=10)` — SESSION_RESUMED (type=3)
4. `api.get(sessionId)` ⚠️
5. `api.watermark(sessionId)` ⚠️ → `wm_resume`
6. `WAIT(5)`
7. `api.watermark(sessionId)` ⚠️ → `wm_moved`

**Ожидаемый результат:**

- Шаг 3: `type=3`
- Шаг 4: `status = 3` (PLAYING)
- Шаг 5: `wm_resume = "2026-11-09T09:30:00Z"` (не сбросился)
- Шаг 7: `wm_moved > wm_resume` (двигается)

**Teardown:** `api.stop` ⚠️ → `api.close` ⚠️ → `RESET()`

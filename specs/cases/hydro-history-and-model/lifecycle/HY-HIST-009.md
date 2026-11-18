---
case_conflu: HY-HIST-009
title: Остановка: PLAYING → DONE
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-009
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SESSIONS-001]
related: [HY-HIST-007, HY-HIST-008, HY-HIST-010, HY-HIST-045]
status: verified
---

# HY-HIST-009 — Остановка: PLAYING → DONE

**Требование:** R-HYDR-054
**Описание:** Остановка. Watermark фиксируется. Ресурсы ещё не удалены (сессия
не закрыта).

**Обоснование:**

- DONE ≠ CLOSED: после DONE можно экспортировать, сохранить, а потом закрыть
- Watermark = момент, до которого обработаны данные

**Предусловие:** Сессия PLAYING, `watermark = 10:15:00`.

**Действия:**

1. `ws.subscribe(sessionId)`
2. `api.stop(sessionId)` ⚠️
3. `ws.wait_event(sessionId, 4, timeout=15)` — SESSION_DONE (type=4)
4. `api.get(sessionId)` ⚠️
5. `api.watermark(sessionId)` ⚠️ → `wm_final`
6. `api.list({status: 8})` ⚠️
7. `WAIT(10)`
8. `api.watermark(sessionId)` ⚠️ → `wm_check`

**Ожидаемый результат:**

- Шаг 3: `type=4` (SESSION_DONE)
- Шаг 4: `status = 8` (DONE), `stoppedAt` заполнен
- Шаг 5: `wm_final = "2026-11-09T10:15:00Z"`
- Шаг 6: сессия в списке со status=8
- Шаг 8: `wm_check = wm_final` (не изменился)

**Teardown:** `api.close(sessionId)` ⚠️ → `WAIT(5)` → `RESET()`

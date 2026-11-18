---
case_conflu: HY-HIST-046
title: Отмена сохранения: SAVING → CANCELLING → CANCELLED
service: hydro-history-and-model
group: save-play
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-046
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SAVE-001]
related: [HY-HIST-045]
status: needs-review
---

# HY-HIST-046 — Отмена сохранения: SAVING → CANCELLING → CANCELLED

**Требование:** R-HYDR-073
**Описание:** Во время сохранения (SAVING) оператор отменяет. Система: прерывает
запись в CH, меняет статус SAVING(4) → CANCELLING → CANCELLED. Сессия
возвращается в предыдущее состояние (PLAYING) или остаётся в промежуточном.

**Предусловие:**

- Сессия historical запущена (status = 3, PLAYING)
- `watermark = "2026-11-09T10:00:00Z"` (большой объём данных для сохранения)

**Действия:**

1. `ws.subscribe(id)`
2. `api.save(id)` ⚠️ — сохранение началось: 3→4 (SAVING), запись в CH
3. `ws.wait_event(id, 15, timeout=10)` — SESSION_SAVING
4. `WAIT(3)` — сохранение идёт (часть данных уже записана, но не всё)
5. `api.get(id)` ⚠️ — `status = 4` (SAVING)
6. Отмена сохранения: `POST /v2/mod-hist/sessions/{id}/save/cancel` ⚠️
   _(псевдо — точный endpoint уточнить)_ — система прерывает запись в CH,
   удаляет частично записанные данные (или помечает невалидными), меняет статус
   4→CANCELLED (или 4→3, если CANCELLING — промежуточное)
7. `WAIT(5)` — завершение отмены, очистка CH
8. `api.get(id)` ⚠️ — финальный статус. Допустимые варианты: (а) `status = 3`
   (PLAYING) — сессия вернулась в работу; (б) `status = 5` (SAVED) с флагом
   `cancelled = true`
9. `ch.query("SELECT count(*) FROM saved_session_data WHERE session_id = '<id>'")` —
   частично записанные данные **удалены** или **помечены невалидными**:
   0 записей (или все с `valid = false`)
10. `api.watermark(id)` ⚠️ — watermark не сбросился: ≈ 10:00 (или чуть больше,
    если сессия вернулась в PLAYING)

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 8 | `status = 3` (PLAYING) **ИЛИ** `status = 5` (SAVED, cancelled) | Сессия не «зависла» в SAVING |
| 9 | 0 записей в CH (или все invalid) | Частичные данные не остались |
| 10 | `watermark ≈ 10:00` | Watermark не сломан |

**Примечание:**

- Если отмена сохранения не реализована (нет endpoint) — сценарий помечается
  «не применимо»; единственный путь — дождаться завершения сохранения. Требует
  решения разработки — см. G24 в meta/discrepancies
- Если CANCELLING (3 по SaveSessionStatus) — промежуточное между SAVING и
  CANCELLED; проверяем, что система не «зависает» в CANCELLING

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

---
case_conflu: HY-HIST-006
title: Повторный запуск (идемпотентность)
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-006
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SESSIONS-001]
related: [HY-HIST-005, HY-HIST-011]
status: verified
---

# HY-HIST-006 — Повторный запуск (идемпотентность)

**Требование:** R-HYDR-051
**Описание:** Двойной клик «Запустить». Второй запрос не создаёт дубль.

**Предусловие:** Сессия PLAYING (status=3).

**Действия:**

1. `api.start(sessionId)` ⚠️ — повторный
2. Проверить ответ
3. `api.get(sessionId)` ⚠️
4. `kafka.consume("mod-hist-commands", {"sessionId": sessionId, "command":"START"}, timeout=5)` — проверить, что START только один

**Ожидаемый результат:**

- Шаг 1: HTTP 200 `{"message":"Session already playing"}` **ИЛИ** HTTP 409
  _(допущение 8: 200)_
- Шаг 3: `status = 3`, `startedAt` не изменился
- Шаг 4: в Kafka за всё время — только ОДНО START

**Teardown:** `api.stop` ⚠️ → `api.close` ⚠️ → `RESET()`

---
case_conflu: HY-HIST-011
title: Повторное закрытие (идемпотентность)
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-011
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SESSIONS-001]
related: [HY-HIST-010, HY-HIST-006, HY-HIST-041]
status: verified
---

# HY-HIST-011 — Повторное закрытие (идемпотентность)

**Требование:** R-HYDR-055
**Описание:** Повторный `close` закрытой сессии не должен ронять систему.

**Предусловие:** Сессия CLOSED (status=11).

**Действия:**

1. `api.close(sessionId)` ⚠️
2. Проверить ответ

**Ожидаемый результат:**

- HTTP 409 _(допущение)_
- Система не упала

**Teardown:** `RESET()`

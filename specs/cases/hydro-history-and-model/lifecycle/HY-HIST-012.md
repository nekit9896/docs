---
case_conflu: HY-HIST-012
title: Превышение максимума сессий
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-012
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-001, HY-HIST-013]
status: verified
---

# HY-HIST-012 — Превышение максимума сессий

**Требование:** R-HYDR-056
**Описание:** `maxSessions = 10` (KB-HM-TESTSTAND-001, §1.3). 11-я сессия
отклоняется.

**Предусловие:** Стенд в начальном состоянии.

**Действия:**

1. Создать и запустить 10 сессий: `api.createHistorical(...)` + `api.start(...)` ⚠️ × 10
2. `api.list({status: 3})` ⚠️ → 10 сессий PLAYING
3. `api.createHistorical(...)` — 11-я
4. Проверить ответ

**Ожидаемый результат:**

- Шаг 2: 10 сессий
- Шаг 3: HTTP 429 `{"error":"Maximum number of sessions (10) reached"}`
- 11-я не создана

**Teardown:** `api.stop` ⚠️ + `api.close` ⚠️ × 10 → `RESET()`

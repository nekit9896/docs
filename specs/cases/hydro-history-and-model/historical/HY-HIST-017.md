---
case_conflu: HY-HIST-017
title: historical: нет данных в ClickHouse
service: hydro-history-and-model
group: historical
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-017
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-018, HY-HIST-014]
status: needs-review
---

# HY-HIST-017 — historical: нет данных в ClickHouse

**Требование:** R-HYDR-060, R-HYDR-062
**Описание:** В CH нет данных за указанный период. Система обрабатывает это
успешно без последствий.

**Предусловие:** В CH **нет** данных за 20:00–21:00.

**Действия:**

1. `api.createHistorical({"startTime":"2026-11-09T20:00:00Z","targetTime":"2026-11-09T21:00:00Z","speedRatio":5000,"targets":["MT1.LU1"]})`
2. `api.start(id)` ⚠️
3. `ws.wait_event(id, 6, timeout=30)` — SESSION_ERROR (type=6) **ИЛИ** 8
4. `WAIT(30)`
5. `api.get(id)` ⚠️

**Ожидаемый результат:** УТОЧНИТЬ

- **Вариант A**: `type=6`, `data.error = "No data in ClickHouse"`, `status = 12` (ERROR)
- **Вариант B**: `status = 8` (DONE), сессия завершена без обработки

_(Допущение 9: Вариант A; требуется решение разработки — см. G23 в
meta/discrepancies)_
**Teardown:** `api.close(id)` ⚠️ → `RESET()`

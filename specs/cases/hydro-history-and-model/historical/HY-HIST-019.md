---
case_conflu: HY-HIST-019
title: historical: большой объём (пагинация CH)
service: hydro-history-and-model
group: historical
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-019
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-014, HY-HIST-037]
status: verified
---

# HY-HIST-019 — historical: большой объём (пагинация CH)

**Требование:** R-HYDR-063
**Описание:** 5000 сообщений → 5 страниц по 1000 (`pageSize`, KB-HM-TESTSTAND-001).
Все загружаются без потери.

**Предусловие:** В CH: 5000 сообщений за 08:00–08:01.

**Действия:**

1. `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:01:00Z","speedRatio":10000,"targets":["MT1.LU1"]})`
2. `api.start(id)` ⚠️
3. `WAIT(20)` — 20 с × 10× = 200 с > 60 (весь диапазон)
4. `ws.wait_event(id, 9, timeout=30)`
5. Подсчёт: `kafka.consume("model_main_" + id, timeout=10)` × N **ИЛИ**
   `ch.query("SELECT count(*) ...")`
6. Сравнить: = 5000 (± 1%)

**Ожидаемый результат:**

- Шаг 4: завершена
- Шаги 5–6: 5000 сообщений, нет дыр

**Teardown:** `api.close(id)` ⚠️ → `RESET()`

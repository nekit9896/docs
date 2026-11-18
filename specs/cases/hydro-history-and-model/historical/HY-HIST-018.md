---
case_conflu: HY-HIST-018
title: historical: частичные данные (прерывание)
service: hydro-history-and-model
group: historical
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-018
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-017, HY-HIST-014]
status: verified
---

# HY-HIST-018 — historical: частичные данные (прерывание)

**Требование:** R-HYDR-062
**Описание:** Данные за 08:00–08:05, нет за 08:05–08:10. Обработка имеющихся, без
падения.

**Предусловие:** В CH: 08:00–08:05 (300 сообщений), нет 08:05–08:10.

**Действия:**

1. `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:10:00Z","speedRatio":10000,"targets":["MT1.LU1"]})`
2. `api.start(id)` ⚠️
3. `WAIT(60)` — 60 с × 10× = 600 с = весь диапазон
4. `ws.wait_event(id, 9, timeout=60)` — WATERMARK_COMPLETE
5. `api.get(id)` ⚠️
6. `api.watermark(id)` ⚠️

**Ожидаемый результат:**

- Шаг 4: WATERMARK_COMPLETE (сессия завершена)
- Шаг 5: `status = 8` (DONE)
- В `model_main_{id}`: сообщения только за 08:00–08:05
- _(Допущение 14: поле `dataGaps` в ответе `api.get`)_

**Teardown:** `api.close(id)` ⚠️ → `RESET()`

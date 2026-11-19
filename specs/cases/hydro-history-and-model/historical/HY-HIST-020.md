---
case_conflu: HY-HIST-020
title: "historical: максимальная скорость 60× (по UI) (скорее всего максимальная 100х)"
service: hydro-history-and-model
group: historical
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-020
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-WATERMARK-001]
related: [HY-HIST-015, HY-HIST-002, HY-HIST-037]
status: needs-review
---

# HY-HIST-020 — historical: максимальная скорость 60× (по UI)

**Требование:** R-HYDR-061
**Описание:** `speedRatio = 60000` (60×). 10 мин / 60× = 10 с реального. Проверка
без переполнения буфера.

> Заголовок источника содержит пометку «(скорее всего максимальная 100х)» —
> расхождение 60× (UI/конфиг `FastMode.maxSpeedFactor`) vs 100× (предположение
> автора) vs 100 000 в коде; см. G21 в meta/discrepancies. Значение 60000
> оставлено каноном до уточнения.

**Предусловие:** В CH: 10 000 сообщений за 10 мин.

**Действия:**

1. `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:10:00Z","speedRatio":60000,"targets":["MT1.LU1"]})`
2. `api.start(id)` ⚠️
3. `WAIT(20)` — 20 с × 60× = 1200 с > 600 (весь диапазон)
4. `ws.wait_event(id, 9, timeout=30)`
5. `api.get(id)` ⚠️
6. `api.progress(id)` ⚠️

**Ожидаемый результат:**

- Шаг 4: завершена (реальное время: 600/60 = 10 с + задержка)
- Шаг 5: `status = 8` (DONE)
- Шаг 6: `progress = 100%`
- `messagesDropped = 0`
- В `model_main_{id}`: все 10 000 сообщений

**Teardown:** `api.close(id)` ⚠️ → `RESET()`

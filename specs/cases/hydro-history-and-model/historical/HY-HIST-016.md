---
case_conflu: HY-HIST-016
title: historical: скорость 0.25× (замедление)
service: hydro-history-and-model
group: historical
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-016
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-WATERMARK-001]
related: [HY-HIST-014, HY-HIST-015, HY-HIST-002]
status: verified
---

# HY-HIST-016 — historical: скорость 0.25× (замедление)

**Требование:** R-HYDR-060
**Описание:** Минимальная скорость 0.25× (speedRatio=250). Виртуальное время идёт
медленнее реального. Диапазон 4 мин → реальное: 4 мин / 0.25 = 16 мин. Проверяем
первые 30 с.

**Обоснование:**

- 0.25× — минимальная допустимая скорость
- 30 с реального × 0.25 = 7.5 с виртуального
- Проверка, что watermark движется **медленнее** реального времени

**Предусловие:** В CH данные за 08:00–08:04.

**Действия:**

1. `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:04:00Z","speedRatio":250,"targets":["MT1.LU1"]})`
2. `api.start(id)` ⚠️
3. `ws.wait_event(id, 1, timeout=30)`
4. `WAIT(30)` — 30 с реального
5. `api.watermark(id)` ⚠️
6. `api.progress(id)` ⚠️

**Ожидаемый результат:**

- Шаг 5: `watermark ≈ "2026-11-09T08:00:07Z"` (30 × 0.25 = 7.5 с виртуального)
- Шаг 6: `progress ≈ 3.1%` (7.5/240 × 100)
- Watermark двигается медленнее реального времени

**Примечание:** Полный цикл займёт 16 мин — для автотеста достаточно 30 с.
**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

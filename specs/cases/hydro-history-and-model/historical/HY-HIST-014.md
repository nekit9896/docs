---
case_conflu: HY-HIST-014
title: historical: базовый цикл обработки
service: hydro-history-and-model
group: historical
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-014
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-WATERMARK-001]
related: [HY-HIST-018, HY-HIST-035, HY-HIST-015]
status: verified
---

# HY-HIST-014 — historical: базовый цикл обработки

**Требование:** R-HYDR-058
**Описание:** Полный цикл historical: создание → запуск → обработка →
автоматическое завершение (DONE). Диапазон 10 мин, скорость 10×
(speedRatio=10000) → реальное время ≈ 60 с.

**Обоснование:**

- 10 мин / 10× = 60 с реального — приемлемо для автотеста
- speedRatio = 10000 — допустимое значение UI

**Предусловие:**

- В CH данные за 08:00–08:10 для MT1.LU1
- Конфигурация ТУ1 загружена

**Действия:**

1. `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:10:00Z","speedRatio":10000,"targets":["MT1.LU1"]})`
2. `api.start(id)` ⚠️
3. `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED
4. `WAIT(30)` — 30 с × 10× = 300 с виртуального (5 мин из 10)
5. `api.watermark(id)` ⚠️
6. `api.progress(id)` ⚠️
7. `WAIT(35)` — ещё 35 с × 10× = 350 с (всего 650 > 600 = target)
8. `ws.wait_event(id, 9, timeout=60)` — WATERMARK_COMPLETE (type=9)
9. `api.get(id)` ⚠️
10. `api.watermark(id)` ⚠️

**Ожидаемый результат:**

- Шаг 5: `watermark ≈ "2026-11-09T08:05:00Z"` (300 с = 5 мин)
- Шаг 6: `progress ≈ 50%` (300/600 × 100)
- Шаг 8: `type=9` (WATERMARK_COMPLETE)
- Шаг 9: `status = 8` (DONE) — автоматически
- Шаг 10: `watermark = "2026-11-09T08:10:00Z"` (= targetTime), `state = 3` (COMPLETE)

**Реальное время сценария:** ≈ 2 мин (30+35 с + задержки).
**Teardown:** `api.close(id)` ⚠️ → `WAIT(5)` → `RESET()`

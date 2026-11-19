---
case_conflu: HY-HIST-015
title: historical: изменение скорости во время работы
service: hydro-history-and-model
group: historical
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-015
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-WATERMARK-001]
related: [HY-HIST-014, HY-HIST-002, HY-HIST-020]
status: verified
---

# HY-HIST-015 — historical: изменение скорости во время работы

**Требование:** R-HYDR-061
**Описание:** Увеличение скорости с 2× на 10× во время работы. Watermark не
сбрасывается. Событие SPEED_CHANGE.

**Предусловие:**

- Сессия historical: `start = 08:00`, `target = 08:10` (600 с), `speedRatio = 2000` (2×)
- `watermark = 08:03:00` (180 с, progress = 30%)
- Осталось: 420 с виртуального / 2× = 210 с реального

**Действия:**

1. `ws.subscribe(id)`
2. `api.setSpeed(id, 10000)` ⚠️ (2× → 10×)
3. `ws.wait_event(id, 13, timeout=10)` — SPEED_CHANGE (type=13)
4. `api.get(id)` ⚠️
5. `api.watermark(id)` ⚠️ → `wm_before`
6. `WAIT(45)` — 45 с × 10× = 450 с виртуального > 420 (остаток)
7. `ws.wait_event(id, 9, timeout=30)` — WATERMARK_COMPLETE
8. `api.get(id)` ⚠️

**Ожидаемый результат:**

- Шаг 3: `type=13`, `data.oldSpeed = 2000`, `data.newSpeed = 10000`
- Шаг 4: `speedRatio = 10000`
- Шаг 5: `wm_before = "2026-11-09T08:03:00Z"` (не сбросился)
- Шаг 7: сессия завершена
- Шаг 8: `status = 8` (DONE)
- Реальное время от смены до завершения: ≈ 45 с (420/10 = 42 с + задержка)

**Teardown:** `api.close(id)` ⚠️ → `RESET()`

---
case_conflu: HY-HIST-034
title: Watermark: STALLED → MOVING (восстановление)
service: hydro-history-and-model
group: watermark-progress
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-034
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-WATERMARK-001, KB-HM-FAULT-001]
related: [HY-HIST-033, HY-HIST-038, HY-HIST-039]
status: verified
---

# HY-HIST-034 — Watermark: STALLED → MOVING (восстановление)

**Требование:** R-HYDR-059
**Описание:** Watermark застрял (STALLED) из-за временного сбоя (hydro-calculation
не публикует результаты). После восстановления — снова движется (MOVING).
Проверяем полный цикл: MOVING → STALLED → MOVING + соответствующие WS-события.

**Предусловие:**

- Сессия historical запущена, `watermarkState = 1` (MOVING)
- `lagThreshold` временно = 10 с _(уточнить механизм изменения)_

**Действия:**

1. `ws.subscribe(id)` — будем ловить WATERMARK_STALLED и WATERMARK_UPDATED
2. Эмулировать сбой: остановить hydro-calculation (`kill` или отключить Kafka
   consumer для `model_main_{id}`) — watermark не обновляется
3. `WAIT(20)` — 10 с lagThreshold + 10 с margin
4. `ws.wait_event(id, 8, timeout=30)` — WATERMARK_STALLED (type=8); в `data.lag` —
   величина отставания
5. `api.watermark(id)` ⚠️ — `state = 2` (STALLED), `lag > 10`
6. Восстановить hydro-calculation (запустить обратно)
7. `WAIT(15)` — hydro-calc обработал накопленное → mod-hist обновил watermark
8. `api.watermark(id)` ⚠️ — `state = 1` (MOVING), `lag = 0` (догнал)
9. `ws.wait_event(id, 7, timeout=30)` — WATERMARK_UPDATED (type=7)

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 4 | `type=8` (STALLED), `data.lag > 10` | Watermark застрял |
| 5 | `state = 2`, `lag > 10` | Подтверждено через REST |
| 8 | `state = 1` (MOVING), `lag = 0` | Восстановлен |
| 9 | `type=7` (WATERMARK_UPDATED) | Событие возобновления |

**Примечание:** Если lagThreshold нельзя изменить в тесте — используем 120 с
(стандарт) и ждём 130 с. Для автотеста долго, но корректно.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

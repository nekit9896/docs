---
case_conflu: HY-HIST-021
title: modelling: базовый цикл (ручной ввод)
service: hydro-history-and-model
group: modelling
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-021
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-CALC-FORMULA-001]
related: [HY-HIST-023, HY-HIST-025, HY-HIST-022]
status: verified
---

# HY-HIST-021 — modelling: базовый цикл (ручной ввод)

**Требование:** R-HYDR-064
**Описание:** Оператор задаёт Press=7.0 через hmi.set. Hydro-calculation
рассчитывает Head. Оператор двигает время advance.

**Обоснование:**

- «Что если Press = 7.0» → Head = (7.0/850)×101970 + 63.5 = 903.3 м
  (формула: KB-CALC-FORMULA-001)
- Нет привязки к реальному времени

**Предусловие:**

- Конфигурация ТУ1 загружена
- `[KIP].TI.Ro = 850`, `[KIP].Height = 63.5`

**Действия:**

1. `api.createModelling({"targets":["MT1.LU1"]})`
2. `api.start(id)` ⚠️
3. `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED
4. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 7.0)` ⚠️
5. `WAIT(5)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️
7. `api.advance(id, 60)` ⚠️
8. `api.watermark(id)` ⚠️

**Ожидаемый результат:**

- Шаг 6: `Head ≈ 903.3 м` (рассчитано hydro-calculation):
  `(7.0 / 850) × 101970 + 63.5 = 839.8 + 63.5 = 903.3`
- Шаг 8: `watermark` увеличен на 60 с относительно шага 4

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

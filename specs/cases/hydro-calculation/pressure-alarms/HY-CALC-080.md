---
case_conflu: HY-CALC-080
title: "KIP_ROSCHEDULE: плановая плотность"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-080
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-063, HY-CALC-067, HY-CALC-051]
status: verified
---

# HY-CALC-080 — KIP_ROSCHEDULE: плановая плотность

**Требование:** R-HYDR-009
**Описание:** В контексте плана перекачки система рассчитывает плановую плотность
для каждого KIP. `KIP_ROSCHEDULE` используется для прогноза напора в плановом
режиме.

**Предусловие:**

- `LU1_TI.ARMTPumpPlan` содержит JSON плана с плотностью
- Текущий режим: «Нормальный», `RoSchedule = 850`
- `KIP1_ROSCHEDULE` — пуст или устаревшее

**Действия:**

1. `WAIT(60c)` — скан планера
2. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.RoSchedule")`
3. Сменить режим на «Ночной» (где `RoSchedule = 860`)
4. `WAIT(60c)`
5. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.RoSchedule")`

**Ожидаемый результат:**

- Шаг 2: `KIP1_ROSCHEDULE = 850` кг/м³
- Шаг 5: `KIP1_ROSCHEDULE = 860` кг/м³

**Teardown:** `RESET()`
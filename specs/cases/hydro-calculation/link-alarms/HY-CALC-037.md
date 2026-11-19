---
case_conflu: HY-CALC-037
title: "Индикатор контроля: все значения (0–5)"
service: hydro-calculation
group: link-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-037
requires: [KB-CALC-ALGO-LU-IND-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-032, HY-CALC-035, HY-CALC-036, HY-CALC-008]
status: verified
---

# HY-CALC-037 — Индикатор контроля: все значения (0–5)

**Требование:** R-HYDR-021 (HYDRO-91)
**Описание:** Индикатор контроля — одно число (0–5), однозначно описывающее
ситуацию. Проверяем все 6 значений последовательно.

**Таблица:**

| Значение | Имя | Цвет | Условие |
|---|---|---|---|
| 0 | ControlOn | Зелёный | Control = 0 |
| 1 | Norm | Зелёный | Control = 1, всё штатно |
| 2 | LonesomeKipAlarmed | Жёлтый | Control = 1, AlmDevMax/Min = true, AlmPressDev = false |
| 3 | RangedKipAlarmed | Красный | Control = 1, AlmPressDev = true |
| 4 | ControlAutoTimeLeft | Оранжевый | ControlAutoTimeLeft > 0 |
| 5 | TransitionOn | Красный | Control = 2 |

**Приоритет (высший → низший):** 5 > 4 > 3 > 2 > 1 > 0

**Предусловие:**

- ТУ1 с 3 KIP, конфигурация загружена

**Действия (последовательная проверка всех 6 состояний):**

| Шаг | Действие | Ожидаемый IndicatorControl |
|---|---|---|
| 1 | `Control = 0`, `AutoControlOn = false`, `TimeLeft = −1` | **0** |
| 2 | `AutoControlOn = true`, `Station = true`, `Control = 0` → TimeLeft = 180 | **4** |
| 3 | `SetAutoControlOff` → TimeLeft = −1. `Control = 1`, KIP2 Press = 5.35 (AlmPressDev = true) | **3** |
| 4 | KIP2 Press = 5.0 (AlmPressDev = false), KIP1 Press = 5.3 (AlmDevMax = true) | **2** |
| 5 | KIP1 Press = 5.0 (всё штатно) | **1** |
| 6 | `SetControlOff` → Control = 0. `TransitionControlOn = true` → Control = 2 | **5** |

**Ожидаемый результат:**

- Каждый шаг даёт соответствующее значение `LU1_INDICATORCONTROL`
- Приоритет соблюдается: если одновременно Control=2 и TimeLeft>0 → 5 (не 4)

**Teardown:** `RESET()`
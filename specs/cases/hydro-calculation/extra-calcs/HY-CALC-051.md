---
case_conflu: HY-CALC-051
title: "Распределение плотности: ручное задание"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-051
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-052, HY-CALC-067, HY-CALC-080]
status: verified
---

# HY-CALC-051 — Распределение плотности: ручное задание

**Требование:** R-HYDR-013 (HYDRO-224)
**Описание:** Оператор задаёт карту плотности вручную. Если `RoDistribManual`
непуст — используется вместо автоматического расчёта.

**Формат:**

```
"км_от,км_до,ρ;км_от,км_до,ρ;..."
Пример: "0,50,845;50,100,860;100,150,850"
```

**Предусловие:**

- `LU1_RODISTRIBMANUAL` — пуст
- `LU1_RODISTRIB` — рассчитан автоматически
- `PLTM1_RO = 850`, `UR1_QVMOM = 120`

**Действия:**

1. `hmi.set("MT1.LU1.TI.RoDistribManual", "0,50,845;50,100,860;100,150,850")`
2. `WAIT(1c)` — LuRoDistribAlg (каждую секунду)
3. `hmi.get("MT1.LU1.TI.RoDistrib")`
4. `hmi.set("MT1.LU1.TI.RoDistribManual", "")` — очистить
5. `WAIT(1c)`
6. `hmi.get("MT1.LU1.TI.RoDistrib")`

**Ожидаемый результат:**

- Шаг 3: `LU1_RODISTRIB` соответствует ручному заданию: км 0–50 = 845, км 50–100 = 860, км 100–150 = 850
- Шаг 6: `LU1_RODISTRIB` возвращён к автоматическому расчёту (по PLTM/UR)

**Teardown:** `RESET()`
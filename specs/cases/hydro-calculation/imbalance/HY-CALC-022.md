---
case_conflu: HY-CALC-022
title: "Дебаланс: ручной ввод расхода (QVmomManual)"
service: hydro-calculation
group: imbalance
source: confluence/test-plan-hydro-calculation.md#HY-CALC-022
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-019, HY-CALC-021, HY-CALC-070]
status: verified
---

# HY-CALC-022 — Дебаланс: ручной ввод расхода (QVmomManual)

**Требование:** R-HYDR-012, R-HYDR-033
**Описание:** Если расходомер даёт сбой, оператор задаёт значение вручную через
`QVmomManual`. Система использует его вместо потокового `QVmom` при `Manual = true`.

**Формула:**

```
QVmom_расчёт = QVmomManual (если Manual = true)
QVmom_расчёт = QVmom (если Manual = false)
```

**Обоснование:**

- Реальный `QVmom = 120.0` (занижает, СИКГ неисправен)
- Оператор вводит `QVmomManual = 122.5` (правильное значение по расчёту)
- При Manual=1: в расчёт уходит 122.5, а не 120.0

**Предусловие:**

- `UR1` (выходной): `Disable = false`, `Manual = false`, `QVmom = 120.0`
- `UR2` (входной): `Disable = false`, `Manual = false`, `QVmom = 122.0`
- `LU1_CONTROL = 1`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.UR1.State.Manual", true)` — включить ручной режим
2. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmomManual", 122.5)`
3. `WAIT(60c)`
4. `hmi.get("MT1.LU1.TI.DiffQmom")`
5. `hmi.set("MT1.LU1.SGLU1.UR1.State.Manual", false)` — выключить
6. `WAIT(60c)`
7. `hmi.get("MT1.LU1.TI.DiffQmom")`

**Ожидаемый результат:**

- Шаг 4: `LU1_DIFFQMOM = 122.0 − 122.5 = −0.5` м³/ч (использован QVmomManual)
- Шаг 7: `LU1_DIFFQMOM = 122.0 − 120.0 = 2.0` м³/ч (использован QVmom, Manual=false)

**Teardown:** `RESET()`
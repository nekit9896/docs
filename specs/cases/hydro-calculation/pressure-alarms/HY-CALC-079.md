---
case_conflu: HY-CALC-079
title: "UR_ALMQVMOMINVALID: невалидный расход"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-079
requires: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-021, HY-CALC-074, HY-CALC-078]
status: verified
---

# HY-CALC-079 — UR_ALMQVMOMINVALID: невалидный расход

**Требование:** R-HYDR-043
**Описание:** Если `UR_QVMOM.invalid = true` при `UR_DISABLE = false` → флаг
`AlmQVmomInvalid`. Невалидный расход исключается из расчёта дебаланса.

**Предусловие:**

- `UR1_DISABLE = false`
- `UR1_QVMOM = 120.0` (валидный)
- `UR1_ALMQVMOMINVALID = false`
- `LU1_CONTROL = 1`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0, invalid=true)`
2. `WAIT(2c)`
3. `hmi.get("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomInvalid")`
4. `hmi.get("MT1.LU1.TI.DiffQmom")` — должен стать invalid (нет выходного расхода)
5. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0, invalid=false)`
6. `WAIT(2c)`
7. `hmi.get("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomInvalid")`
8. `hmi.get("MT1.LU1.TI.DiffQmom")` — восстановлен

**Ожидаемый результат:**

- Шаг 3: `UR1_ALMQVMOMINVALID = true`
- Шаг 4: `LU1_DIFFQMOM.invalid = true` (нет данных)
- Шаг 7: `UR1_ALMQVMOMINVALID = false`
- Шаг 8: `LU1_DIFFQMOM` восстановлен (0.5)

**Teardown:** `RESET()`
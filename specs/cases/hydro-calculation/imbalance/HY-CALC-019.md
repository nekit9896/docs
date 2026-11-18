---
case_conflu: HY-CALC-019
title: "Дебаланс расходов: штатная работа"
service: hydro-calculation
group: imbalance
source: confluence/test-plan-hydro-calculation.md#HY-CALC-019
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-020, HY-CALC-021, HY-CALC-022, HY-CALC-075]
status: verified
---

# HY-CALC-019 — Дебаланс расходов: штатная работа

**Требование:** R-HYDR-012, R-HYDR-033
**Описание:** На ТУ без утечки расходы на входе и выходе совпадают (с точностью
до погрешности СИКГ). Система считает мгновенный дебаланс `DiffQmom`. Если в
пределах лимита — штатно.

**Формула:**

```
DiffQmom = QVmom_входной − QVmom_выходной
```

**Обоснование:**

- Входной UR (на максимальном км ТУ1, т.е. км 200): `QVmom = 120.5` м³/ч
- Выходной UR (на минимальном км ТУ1, т.е. км 0): `QVmom = 120.0` м³/ч
- `DiffQmom = 120.5 − 120.0 = 0.5` м³/ч
- Лимит: `DiffQmomLimitMax = 1.5`, `DiffQmomLimitMin = −1.5` (из ИМ, типовые значения для данного диаметра)
- 0.5 ∈ [−1.5, +1.5] → в пределах

**Важно:** «Входной» — UR с максимальным км (куда течёт жидкость), «выходной» —
UR с минимальным км (откуда). Это определяется автоматически по `UR_KM`.

**Предусловие:**

- `LU1_CONTROL = 1`
- `UR1` (км 0, выходной): `Disable = false`, `Manual = false`, `QVmom = 120.0`
- `UR2` (км 200, входной): `Disable = false`, `Manual = false`, `QVmom = 120.5`
- `LU1_DIFFQMOMLIMITMAX = 1.5` (из ИМ)
- `LU1_DIFFQMOMLIMITMIN = −1.5` (из ИМ)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 120.5)` — входной
2. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0)` — выходной
3. `WAIT(60c)` — LuDiffQAlg по циклу
4. `hmi.get("MT1.LU1.TI.DiffQmom")`
5. `hmi.get("MT1.LU1.Alm.AlmDevQmom")`

**Ожидаемый результат:**

- `LU1_DIFFQMOM = 0.5` м³/ч
- `LU1_ALMDEVQMOM = false` (0.5 < 1.5)

**Teardown:** `RESET()`
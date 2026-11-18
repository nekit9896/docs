---
case_conflu: HY-CALC-021
title: "Дебаланс: исключение отключённого расходомера"
service: hydro-calculation
group: imbalance
source: confluence/test-plan-hydro-calculation.md#HY-CALC-021
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-019, HY-CALC-022, HY-CALC-041]
status: verified
---

# HY-CALC-021 — Дебаланс: исключение отключённого расходомера

**Требование:** R-HYDR-012, R-HYDR-033
**Описание:** Если один из краевых расходомеров отключён — система исключает его
из расчёта. Иначе дебаланс был бы завышен из-за отсутствия данных (0 вместо
реального расхода), и система дала бы ложную тревогу.

**Обоснование:**

- Входной UR отключён (`Disable = true`), показывает 0
- Если бы не исключение: `DiffQmom = 0 − 120.0 = −120.0` → ложный аларм
- С исключением: `DiffQmom` не рассчитывается (invalid) или рассчитывается по доступным данным → аларма нет

**Предусловие:**

- `LU1_CONTROL = 1`
- `UR1` (км 0, выходной): `Disable = false`, `QVmom = 120.0`
- `UR2` (км 200, входной): `Disable = false`, `QVmom = 120.5`
- `LU1_ALMDEVQMOM = false` (штатно)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU2.UR2.State.Disable", true)` — отключить входной
2. `WAIT(60c)`
3. `hmi.get("MT1.LU1.TI.DiffQmom")`
4. `hmi.get("MT1.LU1.Alm.AlmDevQmom")`
5. `hmi.set("MT1.LU1.SGLU2.UR2.State.Disable", false)` — восстановить
6. `WAIT(60c)`
7. `hmi.get("MT1.LU1.TI.DiffQmom")`

**Ожидаемый результат:**

- Шаг 3: `LU1_DIFFQMOM.invalid = true` (или 0, зависит от реализации) — расчёт исключён
- Шаг 4: `LU1_ALMDEVQMOM = false` (нет ложного аларма)
- Шаг 7: `LU1_DIFFQMOM = 0.5` м³/ч (расчёт возобновлён)

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-075
title: "Дебаланс: реакция на 2-секундном цикле"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-075
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-019, HY-CALC-020, HY-CALC-070]
status: verified
---

# HY-CALC-075 — Дебаланс: реакция на 2-секундном цикле

**Требование:** R-HYDR-033
**Описание:** `LuDiffQAlg` имеет два цикла: POLL(60с) для `DiffQavg` и POLL(2с)
для `DiffQmom`. Проверяем что мгновенный дебаланс реагирует быстрее 60с.

**Предусловие:**

- `LU1_CONTROL = 1`
- `UR1` (выходной, км 0): `QVmom = 120.0`
- `UR2` (входной, км 200): `QVmom = 120.5`
- `LU1_DIFFQMOM = 0.5` (штатно)
- `LU1_DIFFQMOMLIMITMAX = 1.5`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 125.0)` — резкий рост
2. `WAIT(2c)` — максимум 7с (2с цикл + margin)
3. `hmi.get("MT1.LU1.TI.DiffQmom")`
4. `hmi.get("MT1.LU1.Alm.AlmDevQmom")`
5. `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 120.5)` — вернуть
6. `WAIT(2c)`
7. `hmi.get("MT1.LU1.TI.DiffQmom")`
8. `hmi.get("MT1.LU1.Alm.AlmDevQmom")`

**Ожидаемый результат:**

- Шаг 3: `LU1_DIFFQMOM = 5.0` м³/ч (125.0 − 120.0)
- Шаг 4: `LU1_ALMDEVQMOM = true` (5.0 > 1.5)
- Шаг 7: `LU1_DIFFQMOM = 0.5` м³/ч
- Шаг 8: `LU1_ALMDEVQMOM = false`

**Примечание:** Если `DiffQmom` обновляется только на 60с цикле (а не на 2с) —
это несоответствие заявленному POLL(2с). Тест зафиксирует фактическое поведение.

**Teardown:** `RESET()`
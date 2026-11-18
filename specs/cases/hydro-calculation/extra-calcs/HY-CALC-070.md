---
case_conflu: HY-CALC-070
title: "Расширение: дебаланс — DiffQavg и DiffQavgStation"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-070
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-019, HY-CALC-020, HY-CALC-058, HY-CALC-075]
status: verified
---

# HY-CALC-070 — Расширение: дебаланс — DiffQavg и DiffQavgStation

**Требование:** R-HYDR-033
**Описание:** HY-CALC-019/020 проверяют только мгновенный `DiffQmom`.
Дополнительно: средний за час (`DiffQavg`) и стационарный (`DiffQavgStation`).

**Логика:**

```
DiffQavg = скользящее среднее DiffQmom за последний час (3600 с)
DiffQavgStation = DiffQavg при Station = true (зафиксированное значение)

Алармы:
- AlmDevQavg: |DiffQavg| > LimitMax
- AlmDevQavgStation: |DiffQavgStation| > LimitMax (при Station=true)
```

**Обоснование:**

- Мгновенный: DiffQmom = 2.0 (аларм)
- Средний за час: если 55 мин было 0.5, а 5 мин было 15.0:
  - DiffQavg = (55×0.5 + 5×15.0) / 60 = (27.5 + 75) / 60 = 1.71
  - 1.71 > 1.5 → аларм по среднему
- Стационарный: если Station=true → DiffQavgStation фиксируется

**Предусловие:**

- `LU1_CONTROL = 1`
- `LU1_DIFFQMOMLIMITMAX = 1.5`
- `LU1_STATION = true`
- Установившийся DiffQmom = 0.5 (штатно, >1 ч)
- `LU1_DIFFQAVG = 0.5`, `LU1_ALMDEVQAVG = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 130.0)` — резкий рост (DiffQmom = 10)
2. `WAIT(60c)` — DiffQmom = 10, но DiffQavg ещё ~0.5 (только 1 мин из 60)
3. `hmi.get("MT1.LU1.TI.DiffQmom")` → 10.0
4. `hmi.get("MT1.LU1.TI.DiffQavg")` → ~0.65 (немного выросло)
5. `hmi.get("MT1.LU1.Alm.AlmDevQmom")` → true (мгновенный аларм)
6. `hmi.get("MT1.LU1.Alm.AlmDevQavg")` → false (средний ещё в норме)
7. `WAIT(3600c)` — час прошёл, DiffQavg = 10.0
8. `hmi.get("MT1.LU1.TI.DiffQavg")` → 10.0
9. `hmi.get("MT1.LU1.Alm.AlmDevQavg")` → true (средний аларм)

**Ожидаемый результат:**

- Шаг 5: `LU1_ALMDEVQMOM = true` (мгновенный: 10 > 1.5)
- Шаг 6: `LU1_ALMDEVQAVG = false` (средний: 0.65 < 1.5)
- Шаг 9: `LU1_ALMDEVQAVG = true` (средний: 10.0 > 1.5)

**Примечание:** Тест с ожиданием 1 часа — ночной. Для ускорения: временно
уменьшить окно усреднения в ИМ (если возможно) или проверять только логику через
Redis (записать DiffQavg напрямую и проверить аларм).

**Teardown:** `RESET()`
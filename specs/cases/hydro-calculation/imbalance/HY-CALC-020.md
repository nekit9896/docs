---
case_conflu: HY-CALC-020
title: "Дебаланс расходов: превышение лимита (утечка)"
service: hydro-calculation
group: imbalance
source: confluence/test-plan-hydro-calculation.md#HY-CALC-020
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-019, HY-CALC-058, HY-CALC-070]
status: verified
---

# HY-CALC-020 — Дебаланс расходов: превышение лимита (утечка)

**Требование:** R-HYDR-012, R-HYDR-033
**Описание:** Дебаланс вышел за допустимые пределы — индикатор утечки или
неисправности СИКГ. Аларм сбрасывается автоматически при возврате в норму.

**Обоснование:**

- Входной: 122.0, выходной: 120.0 → `DiffQmom = 2.0` м³/ч
- Лимит: 1.5 м³/ч
- 2.0 > 1.5 → аларм
- Возврат: входной 120.3 → `DiffQmom = 0.3` → в пределах → сброс

**Предусловие:**

- Как в HY-CALC-019, `LU1_CONTROL = 1`
- `LU1_DIFFQMOMLIMITMAX = 1.5`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 122.0)` — входной (вырос)
2. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0)` — выходной (норма)
3. `WAIT(60c)`
4. `hmi.get("MT1.LU1.TI.DiffQmom")` → проверить значение
5. `hmi.get("MT1.LU1.Alm.AlmDevQmom")` → проверить аларм
6. `hmi.wait_alarm("MT1.LU1.Alm.AlmDevQmom")` — подтвердить доставку
7. `hmi.history("MT1.LU1.Alm.AlmDevQmom", from=ts_start, to=ts_now)` — проверить текст
8. `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 120.3)` — вернуть в норму
9. `WAIT(60c)`
10. `hmi.get("MT1.LU1.TI.DiffQmom")`
11. `hmi.get("MT1.LU1.Alm.AlmDevQmom")`

**Ожидаемый результат:**

- Шаг 4: `LU1_DIFFQMOM = 2.0` м³/ч
- Шаг 5: `LU1_ALMDEVQMOM = true`
- Шаг 6: `hmi.history` возвращает запись: value=true, text содержит «дебаланс расходов превышает допустимый: 2.0 м³/ч при лимите ±1.5 м³/ч»
- Шаг 9: `LU1_DIFFQMOM = 0.3` м³/ч
- Шаг 10: `LU1_ALMDEVQMOM = false` (сброшен)

**Teardown:** `RESET()`
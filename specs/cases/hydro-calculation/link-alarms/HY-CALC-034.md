---
case_conflu: HY-CALC-034
title: "Аларм расхода: выход за границы коридора"
service: hydro-calculation
group: link-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-034
requires: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-074, HY-CALC-079]
status: verified
---

# HY-CALC-034 — Аларм расхода: выход за границы коридора

**Требование:** R-HYDR-029
**Описание:** Расходомер проверяет: не отклоняется ли расход от базового значения
более чем на дельту. В отличие от дебаланса — здесь сравнивается один расходомер
со своим базовым значением.

**Формула:**

```
Если QVmom > QVmomStation + QVmomDeltaRangeMax → AlmQVmomRangeMax = true
Если QVmom < QVmomStation + QVmomDeltaRangeMin → AlmQVmomRangeMin = true
```

**Обоснование:**

- `QVmomStation = 120.0` м³/ч (зафиксировано при Control=1)
- `QVmomDeltaRangeMax = 5.0` м³/ч (из ИМ) → верхняя граница = 125.0
- `QVmomDeltaRangeMin = −5.0` м³/ч (из ИМ) → нижняя граница = 115.0
- Тестируем: QVmom = 127.0 > 125.0 → аларм Max
- Возврат: QVmom = 124.0 < 125.0 → сброс

**Предусловие:**

- `LU1_CONTROL = 1`
- `SGLU1_CONTROLON = true`
- `UR1_DISABLE = false`
- `UR1_QVMOMSTATION = 120.0`
- `UR1_QVMOMDELTARANGEMAX = 5.0` (из ИМ)
- `UR1_QVMOMDELTARANGEMIN = −5.0` (из ИМ)
- `UR1_QVMOM = 120.0` (норма)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 127.0)` — выше границы
2. `WAIT(event)` — UrAlmDevRangeMaxMinAlg
3. `hmi.get("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomRangeMax")`
4. `hmi.wait_alarm("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomRangeMax")` — подтвердить доставку
5. `hmi.history("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomRangeMax", from=ts_start, to=ts_now)` — проверить текст
6. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 124.0)` — вернуть
7. `WAIT(event)`
8. `hmi.get("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomRangeMax")`

**Ожидаемый результат:**

- Шаг 3: `UR1_ALMQVMOMRANGEMAX = true` (127 > 125)
- Шаг 4: `hmi.history` возвращает запись: value=true, text содержит «расход превышает верхнюю границу 125.0 м³/ч, текущий 127.0 м³/ч»
- Шаг 7: `UR1_ALMQVMOMRANGEMAX = false` (сброшен)

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-007
title: Снятие ТУ с контроля
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-007
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-005, HY-CALC-009, HY-CALC-031]
status: verified
---

# HY-CALC-007 — Снятие ТУ с контроля

**Требование:** R-HYDR-023
**Описание:** Диспетчер останавливает мониторинг. Базовые значения аннулируются.
Все алармы давления, расхода, дебаланса перестают генерироваться. Нужно при
плановом/аварийном ремонте, смене режима.

**Что сбрасывается:**

```
PressStation → invalid
QVmomStation → invalid
GravitySegsReg → invalid/пусто
ControlOn → false (все сегменты)
LU_CONTROL → 0
```

**Предусловие:**

- `LU1_CONTROL = 1` (на контроле)
- `KIP1_PRESSSTATION = 5.0`, `UR1_QVMOMSTATION = 120.0` (зафиксированы)
- `SGLU1_CONTROLON = true`
- `LU1_GRAVITYSEGSREG` заполнен

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetControlOff", true)`
2. `WAIT(event)` — LuControlUnsetAlg
3. Проверить все теги

**Ожидаемый результат:**

1. `LU1_CONTROL = 0`
2. `LU1_GRAVITYSEGSREG.invalid = true`
3. `KIP1_PRESSSTATION.invalid = true`
4. `UR1_QVMOMSTATION.invalid = true`
5. `SGLU1_CONTROLON = false`
6. `LU1_TU_SETCONTROLOFF = false` (сброшен)
7. `KIP1_ALMDEVMAXRANGE = false`, `KIP1_ALMDEVMINRANGE = false`
8. `LU1_ALMDEVQMOM = false`
9. `LU1_ALMPRESSDEV = false` (аларм по смежным тоже сброшен) — если бы остался, диспетчер видит красный индикатор при выключенном контроле
10. `LU1_INDICATORCONTROL = 0` (сброшен до ControlOff) — не 1 (Norm)
11. `LU1_INDICATORLINK` **не изменяется** (связь не зависит от режима контроля)

**Teardown:** `RESET()`
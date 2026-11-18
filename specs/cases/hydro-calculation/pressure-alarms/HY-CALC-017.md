---
case_conflu: HY-CALC-017
title: "Аларм давления не генерируется без контроля (Control = 0)"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-017
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-014, HY-CALC-015, HY-CALC-018]
status: verified
---

# HY-CALC-017 — Аларм давления не генерируется без контроля (Control = 0)

**Требование:** R-HYDR-028
**Описание:** Без контроля (Control=0) давление может быть каким угодно — алармы
не генерируются. Нет базового состояния → нечего сравнивать.

**Предусловие:**

- `LU1_CONTROL = 0`
- `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9` (рассчитаны ранее, но неактивны)
- `KIP1_PRESS = 5.5` (высоко, но без контроля не важно)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.5)`
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`
4. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")`

**Ожидаемый результат:**

- `KIP1_ALMDEVMAXRANGE = false`
- `KIP1_ALMDEVMINRANGE = false`
- Без контроля алармы не генерируются, даже при значительном отклонении

**Teardown:** `RESET()`
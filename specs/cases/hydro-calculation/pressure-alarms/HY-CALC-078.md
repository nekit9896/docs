---
case_conflu: HY-CALC-078
title: "PLTM_ALMROINVALID: невалидная плотность"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-078
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-003, HY-CALC-018, HY-CALC-040]
status: verified
---

# HY-CALC-078 — PLTM_ALMROINVALID: невалидная плотность

**Требование:** R-HYDR-043
**Описание:** Если `PLTM_RO.invalid = true` при `PLTM_DISABLE = false` → аларм
достоверности `AlmRoInvalid`. Аналог `KIP_ALMFAILON` для плотномера.

**Предусловие:**

- `PLTM1_DISABLE = false`
- `PLTM1_RO = 850` (валидный)
- `PLTM1_ALMROINVALID = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.PLT1.TI.Ro", 850, invalid=true)`
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.PLT1.Alm.AlmRoInvalid")`
4. `hmi.set("MT1.LU1.SGLU1.PLT1.TI.Ro", 850, invalid=false)`
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.PLT1.Alm.AlmRoInvalid")`

**Ожидаемый результат:**

- Шаг 3: `PLTM1_ALMROINVALID = true`
- Шаг 6: `PLTM1_ALMROINVALID = false`

**Teardown:** `RESET()`
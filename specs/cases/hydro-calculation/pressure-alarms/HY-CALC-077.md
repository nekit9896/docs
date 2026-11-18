---
case_conflu: HY-CALC-077
title: "KIP_ALMGRAVITYPOSSIBLE: напор близок к высоте в конфигурации"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-077
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-ALGO-LU-GRAV-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-013, HY-CALC-038, HY-CALC-039]
status: verified
---

# HY-CALC-077 — KIP_ALMGRAVITYPOSSIBLE: напор близок к высоте в конфигурации

**Требование:** R-HYDR-035
**Описание:** На уровне высоты конкретного датчика: если
`Head_KIP − GravityPossible < H_конфигурации` на этом км → аларм на датчике.
Это более точечное предупреждение, чем `LU_ALMGRAVITYPOSSIBLE`.

**Предусловие:**

- Конфигурация ТУ1: пик км 65, H = 400 м
- KIP2 (км 80): `H = 300 м`, `Ro = 850`
- `LU1_GRAVITYPOSSIBLE = 50` м
- KIP2: `Press = 0.85` → `Head = 402.0 м`
- `Head − GravityPossible = 402.0 − 50 = 352.0 < 400` → риск

**Действия:**

1. `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.85)`
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU2.KIP2.Alm.AlmGravityPossible")`
4. `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 2.0)` — поднять
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU2.KIP2.Alm.AlmGravityPossible")`

**Ожидаемый результат:**

- Шаг 3: `KIP2_ALMGRAVITYPOSSIBLE = true` (352 < 400)
- Шаг 6: `KIP2_ALMGRAVITYPOSSIBLE = false` (Head = 539.9, 539.9 − 50 = 489.9 > 400)

**Teardown:** `RESET()`
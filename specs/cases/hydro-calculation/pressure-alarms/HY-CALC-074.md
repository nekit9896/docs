---
case_conflu: HY-CALC-074
title: "Отклонение расхода (UrQVmomDeltaAlg)"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-074
requires: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-022, HY-CALC-079]
status: verified
---

# HY-CALC-074 — Отклонение расхода (UrQVmomDeltaAlg)

**Требование:** R-HYDR-029
**Описание:** Расчёт отклонения текущего расхода от базового. При `Manual=true`
используется `QVmomManual` вместо потокового `QVmom`.

**Формула:**

```
QVmom_for_calc = Manual ? QVmomManual : QVmom
QVmomDelta = QVmom_for_calc − QVmomStation
```

**Предусловие:**

- `LU1_CONTROL = 1`
- `UR1_DISABLE = false`, `UR1_MANUAL = false`
- `UR1_QVMOMSTATION = 120.0` (зафиксировано при Control=1)
- `UR1_QVMOM = 120.0` (штатно, Delta = 0)
- `UR1_QVMOMDELTA = 0.0`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 125.0)` — расход вырос
2. `WAIT(event)` — UrQVmomDeltaAlg
3. `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`
4. `hmi.set("MT1.LU1.SGLU1.UR1.State.Manual", true)` — ручной режим
5. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmomManual", 123.0)`
6. `WAIT(event)`
7. `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`
8. `hmi.set("MT1.LU1.SGLU1.UR1.State.Manual", false)` — выключить
9. `WAIT(event)`
10. `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`
11. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 118.0)` — расход упал
12. `WAIT(event)`
13. `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`
14. `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0)` — вернуть
15. `WAIT(event)`
16. `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`

**Ожидаемый результат:**

- Шаг 3: `UR1_QVMOMDELTA = 5.0` м³/ч (125.0 − 120.0)
- Шаг 7: `UR1_QVMOMDELTA = 3.0` м³/ч (123.0 − 120.0, используется QVmomManual)
- Шаг 10: `UR1_QVMOMDELTA = 5.0` м³/ч (125.0 − 120.0, Manual=false)
- Шаг 13: `UR1_QVMOMDELTA = −2.0` м³/ч (118.0 − 120.0)
- Шаг 16: `UR1_QVMOMDELTA = 0.0` м³/ч

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-053
title: "Унификация дельт на все датчики"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-053
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-005, HY-CALC-034]
status: verified
---

# HY-CALC-053 — Унификация дельт на все датчики

**Требование:** R-HYDR-026
**Описание:** Диспетчер задаёт единое значение дельты на уровне ТУ — все дочерние
KIP/UR получают его мгновенно. 6 пар унификации:

| LU-тег | KIP/UR-тег | Применимость |
|---|---|---|
| `LU_UNIFIED_PRESSDELTARANGEMAX` | `KIP_PRESSDELTARANGEMAX` | Все KIP на ТУ |
| `LU_UNIFIED_PRESSDELTARANGEMIN` | `KIP_PRESSDELTARANGEMIN` | Все KIP на ТУ |
| `LU_UNIFIED_QVMOMDELTARANGEMAX` | `UR_QVMOMDELTARANGEMAX` | Все UR на ТУ |
| `LU_UNIFIED_QVMOMDELTARANGEMIN` | `UR_QVMOMDELTARANGEMIN` | Все UR на ТУ |
| `LU_UNIFIED_PRESSDELTASCHEDULERANGEMAX` | `KIP_PRESSDELTASCHEDULERANGEMAX` | Все KIP на ТУ |
| `LU_UNIFIED_PRESSDELTASCHEDULERANGEMIN` | `KIP_PRESSDELTASCHEDULERANGEMIN` | Все KIP на ТУ |

**Предусловие:**

- ТУ1: 3 KIP (KIP1, KIP2, KIP3), 2 UR (UR1, UR2)
- Разные значения: KIP1: ΔMax=0.2, KIP2: ΔMax=0.3, KIP3: ΔMax=0.1
- UR1: QVΔMax=5.0, UR2: QVΔMax=7.0

**Действия:**

1. `hmi.set("MT1.LU1.TI.UnifiedPressDeltaRangeMax", 0.4)`
2. `hmi.set("MT1.LU1.TI.UnifiedPressDeltaRangeMin", -0.15)`
3. `hmi.set("MT1.LU1.TI.UnifiedQVmomDeltaRangeMax", 6.0)`
4. `WAIT(event)` — LuUnifiedAlg
5. Проверить все дочерние теги:
   - `hmi.get("KIP1.TI.PressDeltaRangeMax")` → 0.4
   - `hmi.get("KIP2.TI.PressDeltaRangeMax")` → 0.4
   - `hmi.get("KIP3.TI.PressDeltaRangeMax")` → 0.4
   - `hmi.get("KIP1.TI.PressDeltaRangeMin")` → −0.15
   - `hmi.get("UR1.TI.QVmomDeltaRangeMax")` → 6.0
   - `hmi.get("UR2.TI.QVmomDeltaRangeMax")` → 6.0

**Ожидаемый результат:**

- Все KIP получили `PressDeltaRangeMax = 0.4`
- Все KIP получили `PressDeltaRangeMin = −0.15`
- Все UR получили `QVmomDeltaRangeMax = 6.0`

**Teardown:** `RESET()`
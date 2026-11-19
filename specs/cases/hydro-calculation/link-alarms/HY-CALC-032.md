---
case_conflu: HY-CALC-032
title: "Отклонение по двум и более смежным датчикам"
service: hydro-calculation
group: link-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-032
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-ALGO-LU-IND-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-014, HY-CALC-015, HY-CALC-037]
status: verified
---

# HY-CALC-032 — Отклонение по двум и более смежным датчикам

**Требование:** R-HYDR-030, R-HYDR-021 (HYDRO-232, HYDRO-91)
**Описание:** Если 2+ датчика на одном SGLU одновременно имеют `AlmDevMaxRange`
или `AlmDevMinRange` → аларм на уровне ТУ `AlmPressDev`. Это более надёжный
признак, чем одиночный.

**Связь с индикатором:**

- Одиночное отклонение (1 KIP) → `IndicatorControl = 2` (жёлтый)
- Смежное (2+ KIP) → `IndicatorControl = 3` (красный)

**Обоснование:**

- 3 KIP на SGLU1: KIP1, KIP2, KIP3
- Все на контроле, PressStation = 5.0, RangeMax = 5.2
- KIP1: Press = 5.3 → AlmDevMaxRange = true (одиночное)
- KIP2: Press = 5.35 → AlmDevMaxRange = true (второй на том же SGLU)
- 2 ≥ 2 → AlmPressDev = true

**Предусловие:**

- `LU1_CONTROL = 1`
- `SGLU1_CONTROLON = true`
- KIP1, KIP2, KIP3 на SGLU1: `Disable = false`, `PressStation = 5.0`, `PressRangeMax = 5.2`
- KIP1: `Press = 5.3` → `AlmDevMaxRange = true`
- KIP2: `Press = 5.0` (штатно)
- KIP3: `Press = 5.0` (штатно)
- `LU1_ALMPRESSDEV = false`
- `LU1_INDICATORCONTROL = 2` (одиночное отклонение)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.35)` — второй датчик выходит
2. `WAIT(event)` — LuAlmPressDevAlg
3. `hmi.get("MT1.LU1.Alm.AlmPressDev")`
4. `hmi.get("MT1.LU1.State.IndicatorControl")`
5. `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.0)` — вернуть
6. `WAIT(event)`
7. `hmi.get("MT1.LU1.Alm.AlmPressDev")`
8. `hmi.get("MT1.LU1.State.IndicatorControl")`

**Ожидаемый результат:**

- Шаг 3: `LU1_ALMPRESSDEV = true` (2 смежных с отклонением)
- Шаг 4: `LU1_INDICATORCONTROL = 3` (красный)
- Шаг 7: `LU1_ALMPRESSDEV = false`
- Шаг 8: `LU1_INDICATORCONTROL = 2` (вернулся к одиночному)

**Teardown:** `RESET()`
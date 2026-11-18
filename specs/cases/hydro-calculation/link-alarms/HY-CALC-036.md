---
case_conflu: HY-CALC-036
title: "Датчиков на связи меньше нормы"
service: hydro-calculation
group: link-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-036
requires: [KB-CALC-ALGO-LU-IND-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-035, HY-CALC-037]
status: verified
---

# HY-CALC-036 — Датчиков на связи меньше нормы

**Требование:** R-HYDR-038, R-HYDR-020
**Описание:** `0 < CounterKIP < LimitKIP` → аларм `AlmKIPCountLink`,
индикатор = 1 (жёлтый).

**Обоснование:**

- 5 KIP, `LimitKIP = 3`
- Теряем 3 → `CounterKIP = 2 < 3` → аларм
- Но > 0 → не критический (не AllLink)

**Предусловие:**

- 5 KIP, все валидны, `CounterKIP = 5`, `LimitKIP = 3`

**Действия:**

1. Установить `invalid=true` на 3 KIP (KIP1, KIP2, KIP3)
2. `WAIT(2c)`
3. `hmi.get("MT1.LU1.State.CounterKIP")`
4. `hmi.get("MT1.LU1.Alm.AlmKIPCountLink")`
5. `hmi.get("MT1.LU1.State.IndicatorLink")`
6. Восстановить 2 KIP (KIP1, KIP2) → `CounterKIP = 4 ≥ 3`
7. `WAIT(2c)`
8. `hmi.get("MT1.LU1.State.IndicatorLink")`

**Ожидаемый результат:**

- Шаг 3: `LU1_COUNTERKIP = 2`
- Шаг 4: `LU1_ALMKIPCOUNTLINK = true`
- Шаг 5: `LU1_INDICATORLINK = 1` (жёлтый)
- Шаг 8: `LU1_INDICATORLINK = 0` (4 ≥ 3, норма)

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-057
title: "Диапазон напора: верхняя граница выше несущей"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-057
requires: [KB-CALC-FORMULA-001, KB-CALC-ALGO-LU-CTRL-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-056, HY-CALC-013, HY-CALC-011]
status: verified
---

# HY-CALC-057 — Диапазон напора: верхняя граница выше несущей

**Требование:** R-HYDR-032
**Описание:** **Предупреждающий** аларм: верхняя граница диапазона напора
превышает несущую. Фактический напор ещё в норме, но если давление продолжит
расти — будет разрушение.

**Формула:**

```
Если HeadRangeMax > CarrierHeadDef[km] → AlmDevRangeHeadCarrier = true
```

**Обоснование:**

- CarrierHeadDef[km 75] ≈ 801.3 м
- Для HeadRangeMax > 801.3: `(PressRangeMax/850)×101970 + 63.5 > 801.3`
- → `PressRangeMax > (801.3 − 63.5) × 850 / 101970 = 737.8 × 850 / 101970 = 6.15 МПа`
- Увеличиваем ΔMax до 1.5: `PressRangeMax = 5.0 + 1.5 = 6.5 МПа`
- `HeadRangeMax = (6.5/850)×101970 + 63.5 = 779.5 + 63.5 = 843.0 м > 801.3 м` → аларм

**Предусловие:**

- `LU1_CONTROL = 1`
- `KIP1_PRESSSTATION = 5.0`
- `KIP1_PRESSDELTARANGEMAX = 0.2` (штатно)
- `LU1_CARRIERHEADDEF[km_75] ≈ 801.3 м`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.PressDeltaRangeMax", 1.5)` — завысить дельту
2. `WAIT(event)` — пересчёт RangeMax и HeadRangeMax
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadRangeMax")`
4. Проверить аларм (тег уточняется — вероятно `KIP_ALMDEVRANGEHEADCARRIER`)
5. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.PressDeltaRangeMax", 0.2)` — вернуть
6. `WAIT(event)`
7. Проверить: аларм сброшен

**Ожидаемый результат:**

- Шаг 3: `KIP1_HEADRANGEMAX = 843.0 м`
- Шаг 4: Аларм = true (843.0 > 801.3)
- Шаг 7: Аларм = false (возврат к 687.5 < 801.3)

**Teardown:** `RESET()`
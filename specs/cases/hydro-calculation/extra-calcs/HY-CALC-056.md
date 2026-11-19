---
case_conflu: HY-CALC-056
title: "Расчёт диапазона напора (HeadRange)"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-056
requires: [KB-CALC-FORMULA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-057, HY-CALC-005, HY-CALC-010]
status: verified
---

# HY-CALC-056 — Расчёт диапазона напора (HeadRange)

**Требование:** R-HYDR-007, R-HYDR-032, R-HYDR-008
**Описание:** Границы диапазона давления пересчитываются в метры столба жидкости.
HeadRange используется для проверок: не выходит ли верхняя граница за несущую, не
опускается ли нижняя ниже конфигурации ТУ.

**Формулы:**

```
HeadRangeMax = (PressRangeMax / ρ) × 101970 + H
HeadRangeMin = (PressRangeMin / ρ) × 101970 + H
```

**Обоснование:**

- PressRangeMax = 5.2, PressRangeMin = 4.9
- ρ = 850, H = 63.5
- HeadRangeMax = (5.2/850)×101970 + 63.5 = 624.0 + 63.5 = **687.5 м**
- HeadRangeMin = (4.9/850)×101970 + 63.5 = 587.9 + 63.5 = **651.4 м**

**Два контрольных срабатывания:**

1. `HeadRangeMin < H_конфигурации` → аларм (нижняя граница ниже конфигурации)
2. `HeadRangeMax > CarrierHeadDef` → предупреждающий аларм (верхняя граница выше несущей)

**Предусловие:**

- `LU1_CONTROL = 1`
- `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9`
- `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`
- `LU1_CARRIERHEADDEF[km_75] ≈ 801.3 м`
- `LU1_HEIGHT[km_75] = 63.5 м`

**Действия:**

1. `WAIT(event)`
2. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadRangeMax")`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadRangeMin")`
4. Проверить: 687.5 < 801.3 (не выше несущей) и 651.4 > 63.5 (не ниже конфигурации) → штатно

**Ожидаемый результат:**

- `KIP1_HEADRANGEMAX = 687.5 м`
- `KIP1_HEADRANGEMIN = 651.4 м`
- `KIP1_HEADDELTARANGEMAX = (0.2 / 850) × 101970 = 24.0 м`
- `KIP1_HEADDELTARANGEMIN = (0.1 / 850) × 101970 = 12.0 м`
- Штатно: ни одна граница не нарушает несущую/конфигурацию

**Teardown:** `RESET()`
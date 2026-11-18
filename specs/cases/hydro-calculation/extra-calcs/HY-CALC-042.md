---
case_conflu: HY-CALC-042
title: "Скорость изменения давления: алгоритм 1 (двухточечный)"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-042
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-033, HY-CALC-043, HY-CALC-065]
status: verified
---

# HY-CALC-042 — Скорость изменения давления: алгоритм 1 (двухточечный)

**Требование:** R-HYDR-005
**Описание:** Берутся два последних значения давления, разница делится на разницу
времени. Работает мгновенно, но чувствителен к единичным выбросам.

**Формула:**

```
V = (P_кон − P_нач) / T_мин
```

**Обоснование:**

- P_нач = 5.0 МПа (t = 0)
- P_кон = 5.5 МПа (t = 60 с = 1 мин)
- V = (5.5 − 5.0) / 1 = **0.5 МПа/мин**
- Порог: 0.05 МПа/мин → 0.5 >> 0.05 → превышение
- Граничный: менее 2 точек → invalid

**Предусловие:**

- `LU1_PRESSRATEALGORITHM = 1` (двухточечный, из ИМ)
- `LU1_PRESSRATEKIPINTERVAL = 60` с
- `KIP1_PRESS = 5.0` (стабильно, история ≥ 2 точек)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.5)` — скачок за 1 цикл
2. `WAIT(60c)` — KipPressRateAlg по циклу
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressRate")`
4. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — стабилизировать
5. `WAIT(60c)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressRate")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_PRESSRATE ≈ 0.5` МПа/мин
- Шаг 6: `KIP1_PRESSRATE ≈ 0.0` МПа/мин (стабильно)

**Граничные случаи [НИЗКИЙ ПРИОРИТЕТ]:**

| # | Сценарий | Ожидаемое |
|---|---|---|
| 1 | Первая запись Press (0 точек истории) | `KIP1_PRESSRATE.invalid = true` |
| 2 | Одна точка (не хватает пары) | `KIP1_PRESSRATE.invalid = true` |
| 3 | Два значения с одинаковым timestamp (t1 = t2) | `KIP1_PRESSRATE = 0` или `invalid` (не NaN/Inf). Зафиксировать |
| 4 | `PressRateKIPInterval = 0` (через Redis) | `KIP1_PRESSRATE.invalid = true` или лог ошибка. Система не упала |

**Teardown:** `RESET()`
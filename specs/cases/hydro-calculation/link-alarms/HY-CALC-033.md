---
case_conflu: HY-CALC-033
title: "Превышение скорости изменения давления (гидроудар)"
service: hydro-calculation
group: link-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-033
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-042, HY-CALC-043, HY-CALC-065]
status: verified
---

# HY-CALC-033 — Превышение скорости изменения давления (гидроудар)

**Требование:** R-HYDR-034, R-HYDR-005
**Описание:** Гидроудар — резкий рост давления. Система следит за скоростью:
если количество KIP с `V > PressRateLimit` ≥ `PressRateKiplimit` → аларм на ТУ.

**Формула (алгоритм 1):**

```
V = (P_кон − P_нач) / T
```

**Обоснование:**

- `PressRateLimit = 0.05` МПа/мин (из ИМ) — порог
- `PressRateKiplimit = 1` (из ИМ) — минимум 1 датчик с превышением
- KIP1: P растёт с 5.0 до 5.4 за 30 с = 0.5 мин → V = 0.4/0.5 = **0.8 МПа/мин** >> 0.05
- KIP2: аналогично → V = 0.8 МПа/мин
- Count = 2 ≥ 1 → аларм

**Предусловие:**

- `LU1_CONTROL = 1`
- `LU1_PRESSRATELIMIT = 0.05` МПа/мин (из ИМ)
- `LU1_PRESSRATEKIPLIMIT = 1` (из ИМ)
- `LU1_PRESSRATEALGORITHM = 1` (двухточечный)
- KIP1, KIP2: `Press = 5.0` (стабильно, история накоплена)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.4)` — резкий рост KIP1
2. `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.4)` — резкий рост KIP2
3. `WAIT(60c)` — KipPressRateAlg по циклу рассчитывает скорость
4. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressRate")`
5. `hmi.get("MT1.LU1.SGLU1.KIP2.TI.PressRate")`
6. `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")`
7. `hmi.wait_alarm("MT1.LU1.Alm.AlmRateLimitPress")` — подтвердить доставку
8. `hmi.history("MT1.LU1.Alm.AlmRateLimitPress", from=ts_start, to=ts_now)` — проверить текст
9. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — стабилизировать
10. `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.0)`
11. `WAIT(60c)`
12. `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")`

**Ожидаемый результат:**

- Шаг 4: `KIP1_PRESSRATE ≈ 0.8` МПа/мин (> 0.05)
- Шаг 5: `KIP2_PRESSRATE ≈ 0.8` МПа/мин
- Шаг 6: `LU1_ALMPRESSRATELIMIT = true` (2 ≥ 1)
- Шаг 7: `hmi.history` возвращает запись: value=true, text содержит «скорость нарастания давления превышает допустимую (0.05 МПа/мин) на 2 датчиках»
- Шаг 11: `LU1_ALMPRESSRATELIMIT = false` (сброшен)

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-065
title: "Расширение: скорость давления — PressRateKiplimit > 1"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-065
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-033, HY-CALC-042, HY-CALC-043]
status: verified
---

# HY-CALC-065 — Расширение: скорость давления — PressRateKiplimit > 1

**Требование:** R-HYDR-034
**Описание:** HY-CALC-033 проверяет `PressRateKiplimit = 1` (достаточно 1
датчика). Дополнительно проверяем: при `PressRateKiplimit = 2` — нужно минимум
2 датчика с превышением для аларма.

**Обоснование:**

- `PressRateKiplimit = 2` (из ИМ — для ТУ с большим числом датчиков)
- 1 KIP с V = 0.8 МПа/мин → count = 1 < 2 → **аларма нет**
- 2 KIP с V = 0.8 МПа/мин → count = 2 ≥ 2 → **аларм**

**Предусловие:**

- `LU1_CONTROL = 1`
- `LU1_PRESSRATELIMIT = 0.05` МПа/мин
- `LU1_PRESSRATEKIPLIMIT = 2` (из ИМ)
- `LU1_PRESSRATEALGORITHM = 1`
- 3 KIP: KIP1, KIP2, KIP3, все Press = 5.0 (стабильно)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.4)` — только 1 датчик
2. `WAIT(60c)`
3. `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")` — должен быть false
4. `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.4)` — второй датчик
5. `WAIT(60c)`
6. `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")` — должен быть true
7. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — стабилизировать первый
8. `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.0)` — стабилизировать второй
9. `WAIT(60c)`
10. `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")` — false

**Ожидаемый результат:**

- Шаг 3: `LU1_ALMPRESSRATELIMIT = false` (1 < 2, недостаточно)
- Шаг 6: `LU1_ALMPRESSRATELIMIT = true` (2 ≥ 2, достаточно)
- Шаг 10: `LU1_ALMPRESSRATELIMIT = false` (сброшен)

**Teardown:** `RESET()`
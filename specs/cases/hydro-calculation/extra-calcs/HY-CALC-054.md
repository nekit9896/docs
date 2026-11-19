---
case_conflu: HY-CALC-054
title: "Уставка ЦСПА: контроль вне режима контроля"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-054
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-013, HY-CALC-017]
status: verified
---

# HY-CALC-054 — Уставка ЦСПА: контроль вне режима контроля

**Требование:** R-HYDR-010, R-HYDR-036
**Описание:** Уставка ЦСПА — последний рубеж защиты. Превышение генерирует
`AlmLimitCSPA` **всегда**, независимо от режима контроля. Даже при Control=0
(ремонт, профилактика) превышение фиксируется.

**Формула:**

```
Если Press > LimitMaxPressCSPA → AlmLimitCSPA = true
HeadLimitMaxCSPA = (LimitMaxPressCSPA / ρ) × 101970 + H (для визуализации)
```

**Обоснование:**

- `LimitMaxPressCSPA = 6.0` МПа (из ИМ)
- P = 6.5 > 6.0 → аларм
- HeadLimit = (6.0/850)×101970 + 63.5 = 719.5 + 63.5 = 783.0 м
- P = 5.5 < 6.0 → без аларма

**Предусловие:**

- `LU1_CONTROL = 0` (не на контроле — проверка что ЦСПА работает вне контроля)
- `KIP1_LIMITMAXPRESSCSPA = 6.0` МПа (из ИМ)
- `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`
- `KIP1_PRESS = 5.5` (ниже уставки)
- `KIP1_ALMLIMITCSPA = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 6.5)` — превышение
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmLimitCSPA")`
4. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadLimitMaxCSPA")`
5. `hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmLimitCSPA")` — подтвердить доставку
6. `hmi.history("MT1.LU1.SGLU1.KIP1.Alm.AlmLimitCSPA", from=ts_start, to=ts_now)` — проверить текст
7. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.5)` — вернуть
8. `WAIT(event)`
9. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmLimitCSPA")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_ALMLIMITCSPA = true` (6.5 > 6.0) — **даже при Control=0**
- Шаг 4: `KIP1_HEADLIMITMAXCSPA = 783.0 м`
- Шаг 5: `hmi.history` возвращает запись: value=true, text содержит «Давление превышает уставку ЦСПА 6.0 МПа, текущее 6.5 МПа»
- Шаг 8: `KIP1_ALMLIMITCSPA = false` (сброшен)

**Teardown:** `RESET()`
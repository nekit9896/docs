---
case_conflu: HY-CALC-013
title: "Напор выше несущей: критический аларм AlmDevHeadCarrier"
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-013
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-FORMULA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-008, HY-CALC-010, HY-CALC-077]
status: verified
---

# HY-CALC-013 — Напор выше несущей: критический аларм AlmDevHeadCarrier

**Требование:** R-HYDR-031, R-HYDR-003
**Описание:** Давление в трубе превышает допустимое для данного участка → напор
превышает несущую. Аларм `AlmDevHeadCarrier` **не подавляется** даже при Control=2.

**Формула проверки:**

```
Если Head > CarrierHeadDef[km_датчика] → AlmDevHeadCarrier = true
```

**Обоснование выбора значений:**

- `CarrierHeadDef[km 75]` — для датчика на км 75 (между км 50 и 100)
- Интерполяция несущей: между 793.6 (км 50) и 809.0 (км 100) → `793.6 + (809.0−793.6)×(75−50)/(100−50) = 793.6 + 7.7 = 801.3 м`
- Для срабатывания аларма: `Head > 801.3 м`
- При ρ = 850, H = 63.5: `Head = (P/850)×101970 + 63.5 > 801.3` → `P > (801.3 − 63.5) × 850 / 101970 = 737.8 × 850 / 101970 = 6.15 МПа`
- Тестируем: P = 6.5 МПа → `Head = (6.5/850)×101970 + 63.5 = 779.5 + 63.5 = 843.0 м > 801.3 м` → аларм
- Контроль: P = 5.0 МПа → `Head = 663.2 м < 801.3 м` → без аларма

**Предусловие:**

- `LU1_CONTROL = 1` (на контроле)
- `KIP1_KM = 75`, `KIP1_HEIGHT = 63.5 м`, `KIP1_RO = 850`
- `LU1_CARRIERHEADDEF` рассчитан: значение для км 75 ≈ 801.3 м
- `KIP1_PRESS = 5.0` МПа → `KIP1_HEAD = 663.2 м` (ниже несущей — штатно)
- `LU1_ALMDEVHEADCARRIER = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 6.5)` — превысить несущую
2. `WAIT(event)` — LuAlmDevHeadCarrierAlg
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")`
4. `hmi.get("MT1.LU1.Alm.AlmDevHeadCarrier")`
5. `hmi.wait_alarm("MT1.LU1.Alm.AlmDevHeadCarrier")` — подтвердить доставку
6. `hmi.history("MT1.LU1.Alm.AlmDevHeadCarrier", from=ts_start, to=ts_now)` — проверить текст
7. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — вернуть в норму
8. `WAIT(event)`
9. `hmi.get("MT1.LU1.Alm.AlmDevHeadCarrier")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_HEAD = (6.5/850)×101970 + 63.5 = 843.0 м`
- Шаг 4: `LU1_ALMDEVHEADCARRIER = true` (843.0 > 801.3)
- Шаг 5: `hmi.history` возвращает запись: value=true, text содержит «напор превышает несущую»
- Шаг 8: `LU1_ALMDEVHEADCARRIER = false` (663.2 < 801.3, сброшен)

**Примечание:** Аларм НЕ подавляется при Control=2. Для проверки — см. HY-CALC-008.

**Teardown:** `RESET()`
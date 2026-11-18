---
case_conflu: HY-CALC-039
title: "Возможность самотека: прогнозируемый риск"
service: hydro-calculation
group: gravity-reliability
source: confluence/test-plan-hydro-calculation.md#HY-CALC-039
requires: [KB-CALC-ALGO-LU-GRAV-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-038, HY-CALC-077]
status: verified
---

# HY-CALC-039 — Возможность самотека: прогнозируемый риск

**Требование:** R-HYDR-019, R-HYDR-035
**Описание:** Система предупреждает заранее — до того, как самотек станет
реальностью. `GravityPossible` — запас (в метрах), определяющий «насколько близко
напор к конфигурации ТУ». Если `Head − GravityPossible < H_peak` → предупреждение.

**Формула:**

```
Head_possible = Head − GravityPossible
Если Head_possible < H_peak_сегмента → AlmGravityPossible = true
```

**Обоснование:**

- При Head = 420, H_peak = 400, GravityPossible = 50:
- Head = 420 > 400 → **не самотек** (реального перевала нет)
- Head_possible = 420 − 50 = 370 < 400 → **риск** (если напор упадёт на 50 м — будет самотек)

**Обоснование расчётов:**

- KIP2: P = 0.85 МПа, Ro = 850, H = 300 → `Head = (0.85/850)×101970 + 300 = 102.0 + 300 = 402.0 м`
- H_peak = 400 → Head = 402 > 400 (чуть выше, самотека нет)
- GravityPossible = 50 → `Head_possible = 402 − 50 = 352 < 400` → риск

**Предусловие:**

- Конфигурация как в HY-CALC-038 (пик км 65, H = 400 м)
- `LU1_GRAVITYPOSSIBLE = 50` м (из ИМ)
- KIP1 (км 50): `Press = 3.0` (Head = 709.5, высоко)
- KIP2 (км 80): `Press = 0.85` (Head = 402.0, чуть выше пика)
- `LU1_ALMGRAVITY = false` (реального самотека нет)
- `LU1_ALMGRAVITYPOSSIBLE = false` (до начала)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 3.0)`
2. `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.85)`
3. `WAIT(event)`
4. `hmi.get("MT1.LU1.Alm.AlmGravity")`
5. `hmi.get("MT1.LU1.Alm.AlmGravityPossible")`
6. `hmi.get("MT1.LU1.TI.PassPointsPossible")`
7. `hmi.wait_alarm("MT1.LU1.Alm.AlmGravityPossible")` — подтвердить доставку
8. `hmi.history("MT1.LU1.Alm.AlmGravityPossible", from=ts_start, to=ts_now)` — проверить текст
9. `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 2.0)` — поднять (Head = 539.9 >> 400)
10. `WAIT(event)`
11. `hmi.get("MT1.LU1.Alm.AlmGravityPossible")`

**Ожидаемый результат:**

- Шаг 4: `LU1_ALMGRAVITY = false` (Head = 402 > 400, реального самотека нет)
- Шаг 5: `LU1_ALMGRAVITYPOSSIBLE = true` (Head − 50 = 352 < 400, риск)
- Шаг 6: `LU1_PASSPOINTSPOSSIBLE = [65]`
- Шаг 7: `hmi.history` возвращает запись: value=true, text содержит «риск перехода в самотечный режим, перевальная точка на км 65»
- Шаг 10: `LU1_ALMGRAVITYPOSSIBLE = false` (риск устранён)

**Teardown:** `RESET()`
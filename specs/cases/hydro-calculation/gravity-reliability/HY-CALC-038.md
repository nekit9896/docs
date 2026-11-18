---
case_conflu: HY-CALC-038
title: "Самотечный участок обнаружен"
service: hydro-calculation
group: gravity-reliability
source: confluence/test-plan-hydro-calculation.md#HY-CALC-038
requires: [KB-CALC-ALGO-LU-GRAV-001, KB-CALC-FORMULA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-039, HY-CALC-069, HY-CALC-077]
status: verified
---

# HY-CALC-038 — Самотечный участок обнаружен

**Требование:** R-HYDR-018, R-HYDR-035
**Описание:** На горном участке ТУ жидкость не преодолевает перевал за счёт
напора — сегмент ниже перевала работает в самотёчном режиме. Система обнаруживает
самотеки: находит перевальные точки (пики конфигурации ТУ) и проверяет, не
опускается ли линия напора ниже конфигурации.

**Логика алгоритма:**

```
1. Найти пики конфигурации ТУ (максимальные высоты локально)
2. Для каждого сегмента между KIP:
   Если Head_KIP < H_peak_сегмента → сегмент самотечный
3. Записать в GravitySegs (пары км), PassPoints (координаты перевалов)
4. Сгенерировать аларм AlmGravity
```

**Обоснование значений (горный участок):**

- Конфигурация ТУ1: пик на км 65, **H_peak = 400 м** (горный хребет)
- KIP1 (км 50): H = 350 м
- KIP2 (км 80): H = 300 м
- Для самотека: `Head_KIP2 < H_peak = 400 м`
- При P = 0.5 МПа, Ro = 850: `Head = (0.5/850)×101970 + 300 = 59.9 + 300 = 359.9 м < 400` → **самотек**
- При P = 2.0 МПа: `Head = (2.0/850)×101970 + 300 = 239.9 + 300 = 539.9 м > 400` → **не самотек**

**Предусловие:**

- Конфигурация ТУ1: `LU_KM = [0, 50, 65, 80, 100, 200]`, `LU_HEIGHT = [300, 350, 400, 300, 280, 250]`
- Пик: км 65, H = 400 м
- KIP1 (км 50): `Ro = 850`, `H = 350 м`
- KIP2 (км 80): `Ro = 850`, `H = 300 м`
- `LU1_ALMGRAVITY = false` (до начала теста)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 3.0)` — KIP1 высоко (Head = 709.5 > 400)
2. `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.5)` — KIP2 низко (Head = 359.9 < 400)
3. `WAIT(event)` — LuGravitySegsAlg
4. `hmi.get("MT1.LU1.Alm.AlmGravity")`
5. `hmi.get("MT1.LU1.TI.GravitySegs")`
6. `hmi.get("MT1.LU1.TI.PassPoints")`
7. `hmi.wait_alarm("MT1.LU1.Alm.AlmGravity")` — подтвердить доставку
8. `hmi.history("MT1.LU1.Alm.AlmGravity", from=ts_start, to=ts_now)` — проверить текст
9. `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 2.0)` — поднять напор (Head = 539.9 > 400)
10. `WAIT(event)`
11. `hmi.get("MT1.LU1.Alm.AlmGravity")`

**Ожидаемый результат:**

- Шаг 4: `LU1_ALMGRAVITY = true`
- Шаг 5: `LU1_GRAVITYSEGS = ["50,80"]` (сегмент км 50–80 самотечный)
- Шаг 6: `LU1_PASSPOINTS = [65]` (перевал на км 65)
- Шаг 7: `hmi.history` возвращает запись: value=true, text содержит «самотечный участок км 50–80, перевальная точка на км 65»
- Шаг 10: `LU1_ALMGRAVITY = false` (напор восстановлен, самотек устранён)

**Teardown:** `RESET()`
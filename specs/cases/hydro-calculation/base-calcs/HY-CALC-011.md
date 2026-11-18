---
case_conflu: HY-CALC-011
title: Несущая давления: пользователь занижает ограничение
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-011
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-010, HY-CALC-012, HY-CALC-081]
status: verified
---

# HY-CALC-011 — Несущая давления: пользователь занижает ограничение

**Требование:** R-HYDR-004, R-HYDR-037
**Описание:** Оператор обнаружил дефект и занижает допустимое давление через
`PressManualLimit`. Система берёт `min(PmaxDefault, PressManualLimit)` и
генерирует аларм `AlmCarrierOnUser`.

**Формат PressManualLimit:**

```
"км_от,км_до,лимит_МПа;км_от,км_до,лимит_МПа;..."
```

**Обоснование:**

- PmaxDefault на км 50 = 6.1 МПа
- Ограничение: "50,100,5.5" — оператор снижает до 5.5 МПа на км 50–100 (обнаружена коррозия)
- Результат: `CarrierDef[км 50..100] = min(6.1, 5.5) = 5.5` и `min(6.2, 5.5) = 5.5`

**Предусловие:**

- Конфигурация ТУ1 как в HY-CALC-010
- `LU1_PRESSMANUALLIMIT` — пуст
- `LU1_CARRIERDEF` рассчитан по PmaxDefault

**Действия:**

1. `hmi.set("MT1.LU1.TI.PressManualLimit", "50,100,5.5")` — задать ограничение
2. `WAIT(event)` — LuMaxAllowablePAlg срабатывает
3. `hmi.get("MT1.LU1.TI.CarrierDef")`
4. `hmi.get("MT1.LU1.Alm.AlmCarrierOnUser")`
5. `hmi.wait_alarm("MT1.LU1.Alm.AlmCarrierOnUser")` — подтвердить доставку
6. `hmi.history("MT1.LU1.Alm.AlmCarrierOnUser", from=ts_start, to=ts_now)` — проверить текст

**Ожидаемый результат:**

- `LU1_CARRIERDEF[1]` (км 50) = 5.5 МПа (занижено с 6.1)
- `LU1_CARRIERDEF[2]` (км 100) = 5.5 МПа (занижено с 6.2)
- `LU1_CARRIERDEF[0]` (км 0) = 6.0 (без изменений)
- `LU1_CARRIERDEF[3]` (км 150) = 6.3 (без изменений)
- `LU1_ALMCARRIERONUSER = true`
- `hmi.history` возвращает запись: value=true, text содержит «ограничение несущей задано пользователем», «км 50–100», «5.5 МПа»

**Teardown:** `hmi.set("MT1.LU1.TI.PressManualLimit", "")` → `WAIT(event)` → `RESET()`
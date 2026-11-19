---
case_conflu: HY-CALC-012
title: Несущая давления: пользователь снимает ограничение
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-012
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-010, HY-CALC-011, HY-CALC-081]
status: verified
---

# HY-CALC-012 — Несущая давления: пользователь снимает ограничение

**Требование:** R-HYDR-004, R-HYDR-037
**Описание:** Оператор устранил дефект и снимает ручное ограничение. Система
возвращает заводское значение и генерирует аларм об удалении ограничения (аудит).

**Предусловие:**

- `LU1_PRESSMANUALLIMIT = "50,100,5.5"` (установлено ранее)
- `LU1_CARRIERDEF[1] = 5.5` (занижено)
- `LU1_ALMCARRIERONUSER = true`

**Действия:**

1. `hmi.set("MT1.LU1.TI.PressManualLimit", "")` — очистить (снять ограничение)
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.TI.CarrierDef")`
4. `hmi.wait_alarm("MT1.LU1.Alm.AlmCarrierOnUser")` — подтвердить доставку
5. `hmi.history("MT1.LU1.Alm.AlmCarrierOnUser", from=ts_start, to=ts_now)` — проверить текст

**Ожидаемый результат:**

- `LU1_CARRIERDEF[1]` (км 50) = 6.1 МПа (возврат к PmaxDefault)
- `LU1_CARRIERDEF[2]` (км 100) = 6.2 МПа (возврат)
- `LU1_ALMCARRIERONUSER = true` (аларм о снятии — для аудита)
- `hmi.history` возвращает запись: value=true, text содержит «ограничение несущей снято пользователем»

**Teardown:** `RESET()`
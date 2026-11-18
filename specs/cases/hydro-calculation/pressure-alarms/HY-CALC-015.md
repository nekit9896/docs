---
case_conflu: HY-CALC-015
title: "Аларм выхода давления за нижнюю границу"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-015
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-SIDEFX-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-014, HY-CALC-016, HY-CALC-017]
status: verified
---

# HY-CALC-015 — Аларм выхода давления за нижнюю границу

**Требование:** R-HYDR-028
**Описание:** Давление упало ниже нижней границы диапазона. Риск кавитации,
воздухонакопления. Условие строгое (`<`).

**Формула:**

```
Если Press < PressRangeMin → AlmDevMinRange = true
```

**Обоснование:**

- `PressStation = 5.0`, `PressDeltaRangeMin = 0.1` → `PressRangeMin = 4.9`
- Тестируем: P = 4.8 → 4.8 < 4.9 → аларм
- Возврат: P = 4.92 → 4.92 > 4.9 → сброс

**Предусловие:**

- `LU1_CONTROL = 1`
- `SGLU1_CONTROLON = true`
- `KIP1_DISABLE = false`
- `KIP1_PRESSSTATION = 5.0`
- `KIP1_PRESSDELTARANGEMIN = 0.1` → `KIP1_PRESSRANGEMIN = 4.9`
- `KIP1_PRESS = 5.0` (в диапазоне)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.8)` — ниже границы
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")`
4. `hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")` — подтвердить доставку
5. `hmi.history("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange", from=ts_start, to=ts_now)` — проверить текст
6. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.92)` — вернуть
7. `WAIT(event)`
8. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_ALMDEVMINRANGE = true` (4.8 < 4.9)
- Шаг 4: `hmi.history` возвращает запись: value=true, text содержит «ниже минимальной границы диапазона 4.9 МПа, текущее 4.8 МПа»
- Шаг 7: `KIP1_ALMDEVMINRANGE = false` (сброшен)

**Teardown:** `RESET()`
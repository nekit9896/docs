---
case_conflu: HY-CALC-014
title: "Аларм выхода давления за верхнюю границу"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-014
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-SIDEFX-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-015, HY-CALC-016, HY-CALC-017, HY-CALC-073]
status: verified
---

# HY-CALC-014 — Аларм выхода давления за верхнюю границу

**Требование:** R-HYDR-028
**Описание:** На контроле система следит за давлением. Превышение верхней границы
диапазона → аларм `AlmDevMaxRange`. Условие строгое (`>`), ровно на границе —
аларма нет. Аларм генерируется при `Control=1 AND Disable=false`.

**Формула:**

```
Если Press > PressRangeMax → AlmDevMaxRange = true
```

**Обоснование значений:**

- `PressStation = 5.0` МПа (зафиксировано при постановке)
- `PressDeltaRangeMax = 0.2` МПа (из ИМ для данного KIP)
- `PressRangeMax = 5.0 + 0.2 = 5.2` МПа
- Тестируем: P = 5.3 → 5.3 > 5.2 → аларм
- Возврат: P = 5.15 → 5.15 < 5.2 → сброс

**Предусловие:**

- `LU1_CONTROL = 1` (на контроле)
- `SGLU1_CONTROLON = true`
- `KIP1_DISABLE = false`
- `KIP1_PRESSSTATION = 5.0`
- `KIP1_PRESSDELTARANGEMAX = 0.2` → `KIP1_PRESSRANGEMAX = 5.2`
- `KIP1_PRESS = 5.0` (в диапазоне)
- `KIP1_ALMDEVMAXRANGE = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)` — выше границы
2. `WAIT(event)` — KipAlmDevRangeMaxMinAlg
3. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`
4. `hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")` — подтвердить доставку
5. `hmi.history("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange", from=ts_start, to=ts_now)` — проверить текст
6. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.15)` — вернуть в диапазон
7. `WAIT(event)`
8. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_ALMDEVMAXRANGE = true` (5.3 > 5.2)
- Шаг 4: `hmi.history` возвращает запись: value=true, text содержит «превышает максимальную границу», «5.2 МПа», «5.3 МПа»
- Шаг 7: `KIP1_ALMDEVMAXRANGE = false` (5.15 < 5.2, сброшен)

**Teardown:** `RESET()`
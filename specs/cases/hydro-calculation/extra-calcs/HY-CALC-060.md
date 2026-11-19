---
case_conflu: HY-CALC-060
title: "Статус ремонта: автоматическое отключение/включение"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-060
requires: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-006, HY-CALC-041, HY-CALC-061]
status: verified
---

# HY-CALC-060 — Статус ремонта: автоматическое отключение/включение

**Требование:** EVOSCADA-21706 (DisableAndRemontStatusAlg)
**Описание:** При переходе датчика в ремонт (`RemontStatus ≠ 0`) система
автоматически ставит `Disable = true`. При возвращении из ремонта
(`RemontStatus = 0`) — `Disable = false`. Работает для KIP, UR, PLTM.

**Логика:**

```
RemontStatus ≠ 0 AND Disable = false → Disable = true (отключаем)
RemontStatus = 0 AND Disable = true → Disable = false (включаем)
```

**Дополнительно (TU.SetOn/Off):**

- `TU.SetOff = true` → `Disable = true` (команда отключения)
- `TU.SetOn = true` AND `RemontStatus ≠ 0` → **НЕ включается** (в ремонте)
- `TU.SetOn = true` AND `RemontStatus = 0` → `Disable = false` (включается)

**Обоснование:**

- RemontStatus = 1 → ремонт → автоматическое отключение
- RemontStatus = 0 → норма → автоматическое включение
- При ремонте команда SetOn игнорируется (защита от случайного включения)

**Предусловие:**

- `KIP1_DISABLE = false`
- `KIP1_REMONTSTATUS = 0` (норма)
- `KIP1_TU_SETON = false`, `KIP1_TU_SETOFF = false`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.State.RemontStatus", 1)` — в ремонт
2. `WAIT(event)` — DisableAndRemontStatusAlg
3. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")`
4. `hmi.set("MT1.LU1.SGLU1.KIP1.TU.SetOn", true)` — попытка включения в ремонте
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")` — должен остаться true
7. `hmi.set("MT1.LU1.SGLU1.KIP1.State.RemontStatus", 0)` — вернули из ремонта
8. `WAIT(event)`
9. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")`
10. `hmi.set("MT1.LU1.SGLU1.KIP1.TU.SetOff", true)` — команда отключения
11. `WAIT(event)`
12. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")`
13. `hmi.set("MT1.LU1.SGLU1.KIP1.TU.SetOn", true)` — команда включения
14. `WAIT(event)`
15. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")`

**Ожидаемый результат:**

- Шаг 3: `Disable = true` (автоматически, из-за ремонта)
- Шаг 6: `Disable = true` (SetOn игнорируется — датчик в ремонте)
- Шаг 9: `Disable = false` (вернули из ремонта, автоматически включён)
- Шаг 12: `Disable = true` (команда SetOff)
- Шаг 15: `Disable = false` (команда SetOn, ремонт не активен)

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-071
title: "Расширение: стационарность LU — зона «недостаточно данных»"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-071
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-026, HY-CALC-027, HY-CALC-035]
status: verified
---

# HY-CALC-071 — Расширение: стационарность LU — зона «недостаточно данных»

**Требование:** R-HYDR-017
**Описание:** HY-CALC-026 проверяет «достоверно стационарный», HY-CALC-027 —
«достоверно нестационарный». Дополнительно: третья зона — «недостаточно данных».

**Логика:**

```
Зона 1 (стационарный): нестационарных < CountKIPNoStation AND стационарных ≥ LimitKIP → true
Зона 2 (нестационарный): нестационарных ≥ CountKIPNoStation → false
Зона 3 (недостаточно данных): стационарных < LimitKIP AND нестационарных < CountKIPNoStation → false
```

**Обоснование:**

- 5 KIP: 1 стационарен, 4 нестационарны
- `CountKIPNoStation = 2`, `LimitKIP = 3`
- Нестационарных = 4 ≥ 2 → **Зона 2** (нестационарный)

**Вариант для Зоны 3:**

- 5 KIP: 1 стационарен, 1 нестационарен, 3 invalid
- Нестационарных = 1 < 2 (порог)
- Стационарных = 1 < 3 (LimitKIP)
- → **Зона 3** (недостаточно данных) → false

**Предусловие:**

- 5 KIP: KIP1 (Station=true), KIP2 (Station=false), KIP3–KIP5 (invalid=true)
- `LU1_COUNTKIPNOSTATION = 2`
- `LU1_LIMITKIP = 3`

**Действия:**

1. `hmi.set("KIP3.Press", 5.0, invalid=true)`
2. `hmi.set("KIP4.Press", 5.0, invalid=true)`
3. `hmi.set("KIP5.Press", 5.0, invalid=true)`
4. `WAIT(event)` — LuStationAlg
5. `hmi.get("MT1.LU1.State.Station")`
6. `hmi.get("MT1.LU1.State.CounterKIP")`

**Ожидаемый результат:**

- Шаг 5: `LU1_STATION = false` (Зона 3: стационарных = 1 < LimitKIP = 3, нестационарных = 1 < CountKIPNoStation = 2)
- Шаг 6: `LU1_COUNTERKIP = 1` (только KIP1 валиден)

**Teardown:** `RESET()`
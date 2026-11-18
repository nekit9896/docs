---
case_conflu: HY-CALC-062
title: "Отклонение напора и давления (KipHeadDeltaPressAlg)"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-062
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-FORMULA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-076, HY-CALC-064]
status: verified
---

# HY-CALC-062 — Отклонение напора и давления (KipHeadDeltaPressAlg)

**Требование:** R-HYDR-028
**Описание:** После фиксации базового состояния (Control=1) система рассчитывает
отклонения текущего напора и давления от базовых значений. Используются для
визуализации на АРМ и генерации алармов.

**Формулы:**

```
HeadDelta = Head − HeadStation
PressDelta = Press − PressStation
```

**Обоснование:**

- PressStation = 5.0 МПа, HeadStation = 663.2 м (зафиксировано при Control=1)
- P = 5.3 → Head = (5.3/850)×101970 + 63.5 = 635.8 + 63.5 = 699.3 м
- `PressDelta = 5.3 − 5.0 = 0.3` МПа
- `HeadDelta = 699.3 − 663.2 = 36.1` м
- P = 4.8 → Head = (4.8/850)×101970 + 63.5 = 573.6 + 63.5 = 637.1 м
- `PressDelta = 4.8 − 5.0 = −0.2` МПа
- `HeadDelta = 637.1 − 663.2 = −26.1` м

**Предусловие:**

- `LU1_CONTROL = 1`
- `KIP1_PRESSSTATION = 5.0`
- `KIP1_HEADSTATION = 663.2 м`
- `KIP1_PRESS = 5.0` (штатно, Delta = 0)
- `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)` — отклонение вверх
2. `WAIT(event)` — KipHeadDeltaPressAlg
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressDelta")`
4. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadDelta")`
5. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.8)` — отклонение вниз
6. `WAIT(event)`
7. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressDelta")`
8. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadDelta")`
9. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — вернуть в норму
10. `WAIT(event)`
11. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressDelta")`
12. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadDelta")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_PRESSDELTA = 0.3` МПа
- Шаг 4: `KIP1_HEADDELTA = 36.1` м
- Шаг 7: `KIP1_PRESSDELTA = −0.2` МПа
- Шаг 8: `KIP1_HEADDELTA = −26.1` м
- Шаг 11: `KIP1_PRESSDELTA = 0.0` МПа
- Шаг 12: `KIP1_HEADDELTA = 0.0` м

**Teardown:** `RESET()`
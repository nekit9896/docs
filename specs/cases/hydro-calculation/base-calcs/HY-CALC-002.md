---
case_conflu: HY-CALC-002
title: Расчётный напор: ручная корректировка высоты
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-002
requires: [KB-CALC-FORMULA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-001, HY-CALC-055]
status: verified
---

# HY-CALC-002 — Расчётный напор: ручная корректировка высоты

**Требование:** R-HYDR-001
**Описание:** Оператор вручную задаёт поправку к высоте (`HeightCorrection`) —
это нужно, когда геометрическая высота датчика в конфигурации ТУ известна
неточно. В ручном режиме расчёт напора использует `HeightCorrection` вместо
интерполированной `Height`.

**Формула (режим ручной корректировки):**

```
При Manual = true:  Head = (P / ρ) × 101970 + HeightCorrection
При Manual = false: Head = (P / ρ) × 101970 + Height (из конфигурации ТУ)
```

**Обоснование:**

- Height = 63.5 м (из конфигурации ТУ, как в HY-CALC-001)
- HeightCorrection = 70.0 м — оператор знает, что датчик стоит на эстакаде, фактически выше
- Расчёт при Manual=1: `(5.0 / 850) × 101970 + 70.0 = 599.7 + 70.0 = 669.7 м`
- Расчёт при Manual=0: `(5.0 / 850) × 101970 + 63.5 = 599.7 + 63.5 = 663.2 м`

**Предусловие:**

- `KIP1_HEIGHT = 63.5 м` (из конфигурации ТУ)
- `KIP1_HEIGHTCORRECTION = 70.0 м` (уже задано оператором ранее)
- `KIP1_MANUAL = false`
- `KIP1_RO = 850`
- `KIP1_PRESS = 5.0` МПа (стабильно)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.State.Manual", true)` — включить ручной режим
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` — проверить при Manual=1
4. `hmi.set("MT1.LU1.SGLU1.KIP1.State.Manual", false)` — выключить ручной режим
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` — проверить при Manual=0

**Ожидаемый результат:**

- При Manual=1: `KIP1_HEAD = 669.7 м` (используется HeightCorrection = 70.0)
- При Manual=0: `KIP1_HEAD = 663.2 м` (используется Height = 63.5 из конфигурации ТУ)

**Teardown:** `RESET()`
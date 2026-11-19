---
case_conflu: HY-CALC-055
title: "Высота датчика: расчёт из конфигурации ТУ"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-055
requires: [KB-CALC-FORMULA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-001, HY-CALC-002, HY-CALC-056, HY-CALC-082]
status: verified
---

# HY-CALC-055 — Высота датчика: расчёт из конфигурации ТУ

**Требование:** R-HYDR-002 (HYDRO-76)
**Описание:** Высота датчика определяется линейной интерполяцией между точками
конфигурации ТУ. Без высоты формула напора не завершается.

**Формула:**

```
H_на_km = H_ниже + (H_выше − H_ниже) × (km − km_ниже) / (km_выше − km_ниже)
```

**Обоснование:**

- Конфигурация: км [0, 50, 100, 150, 200], H [60, 62, 65, 68, 70]
- KIP на км 75: между (50, 62) и (100, 65)
- H = 62 + (65−62) × (75−50)/(100−50) = 62 + 3×0.5 = **63.5 м**
- Граничные:
  - KIP на км 50 (ровно на точке): H = 62 м
  - KIP на км 225 (вне диапазона 0–200): не рассчитывается
  - Пустые LU_KM/LU_HEIGHT: не рассчитывается

**Предусловие:**

- `LU1_KM = [0, 50, 100, 150, 200]`, `LU1_HEIGHT = [60, 62, 65, 68, 70]`
- `KIP1_KM = 75`

**Действия:**

1. `WAIT(60c)` — KipHeightAlg по циклу
2. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Height")`
3. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Km", 50)` — ровно на точке
4. `WAIT(60c)`
5. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Height")`
6. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Km", 225)` — вне диапазона
7. `WAIT(60c)`
8. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Height")`

**Ожидаемый результат:**

- Шаг 2: `KIP1_HEIGHT = 63.5 м` (интерполяция)
- Шаг 5: `KIP1_HEIGHT = 62 м` (ровно на точке конфигурации)
- Шаг 8: `KIP1_HEIGHT` не меняется (остаётся 62) или `invalid = true` — вне диапазона

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-010
title: Несущая давления: заводские значения (PmaxDefault)
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-010
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-FORMULA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-011, HY-CALC-012, HY-CALC-013, HY-CALC-082]
status: verified
---

# HY-CALC-010 — Несущая давления: заводские значения (PmaxDefault)

**Требование:** R-HYDR-004, R-HYDR-003
**Описание:** Каждый км ТУ имеет паспортную характеристику — предельно допустимое
давление `PmaxDefault`. Из этого массива рассчитывается несущая напора
`CarrierHeadDef` — порог, за которым начинается разрушение. Это главный защитный
барьер.

**Формулы:**

```
CarrierDef[km] = PmaxDefault[km]  (если PressManualLimit пуст)
CarrierHeadDef[km] = (CarrierDef[km] / ρ_def) × 101970 + H[km]
```

**Обоснование выбора значений:**

- `PmaxDefault` задано в МПа (не в кгс/см²) — все давления в системе МПа
- Конфигурация ТУ1: 5 точек по км, PmaxDefault = [6.0, 6.1, 6.2, 6.3, 6.4] МПа
- `DensDef = 850` кг/м³ — типовая плотность
- Высоты: [60, 62, 65, 68, 70] м

**Расчёт для км 50 (второй элемент):**

```
CarrierDef = 6.1 МПа
CarrierHeadDef = (6.1 / 850) × 101970 + 62 = 731.6 + 62 = 793.6 м
```

**Расчёт для км 100 (третий элемент):**

```
CarrierDef = 6.2 МПа
CarrierHeadDef = (6.2 / 850) × 101970 + 65 = 744.0 + 65 = 809.0 м
```

**Предусловие:**

- Конфигурация ТУ1 загружена в data-manager:
  - `LU1_KM = [0, 50, 100, 150, 200]` км
  - `LU1_HEIGHT = [60, 62, 65, 68, 70]` м
  - `LU1_PMAXDEFAULT = [6.0, 6.1, 6.2, 6.3, 6.4]` МПа
- `LU1_PRESSMANUALLIMIT` — пуст (нет ручных ограничений)
- `LU1_DENSDEF = 850` кг/м³

**Действия:**

1. Убедиться, что конфигурация ТУ1 загружена (проверка через PostgreSQL/Redis)
2. `WAIT(60c)` — LuMaxAllowablePAlg и LuCarrierHeadDefAlg выполняются по циклу
3. `hmi.get("MT1.LU1.TI.CarrierDef")` — прочитать массив несущей
4. `hmi.get("MT1.LU1.TI.CarrierHeadDef")` — прочитать массив несущей напора

**Ожидаемый результат:**

- `LU1_CARRIERDEF = [6.0, 6.1, 6.2, 6.3, 6.4]` МПа (без изменений, PressManualLimit пуст)
- `LU1_CARRIERHEADDEF ≈ [779.5, 793.6, 809.0, 824.0, 838.0]` м
  - км 0: `(6.0/850)×101970 + 60 = 719.5 + 60 = 779.5` м
  - км 50: `(6.1/850)×101970 + 62 = 731.6 + 62 = 793.6` м
  - км 100: `(6.2/850)×101970 + 65 = 744.0 + 65 = 809.0` м
  - км 150: `(6.3/850)×101970 + 68 = 756.0 + 68 = 824.0` м
  - км 200: `(6.4/850)×101970 + 70 = 768.0 + 70 = 838.0` м
- `LU1_ALMCARRIERONUSER = false`

**Teardown:** `RESET()`
---
id: KB-CALC-FORMULA-001
title: Формулы, единицы измерения, форматтеры (hydro-calculation)
service: hydro-calculation
group: formulas
source: confluence/repo_description_hydro-calculation#«Бизнес-логика», #2.Configuration Layer, #12.Utils
requires: []
related: [KB-CALC-ALGO-001, KB-CALC-MODEL-001]
status: verified
---

# Формулы и единицы

## Расчёт напора (BaseAlgorithm.calculateHead)

```
head = (pressure / density) * 101970 + height
```

- `pressure` — давление, `density` — плотность (кг/м³), `height` — высота.
- **Минимальная плотность**: `MIN_DENSITY = 500f` кг/м³ (константа BaseAlgorithm).
- 101970 — коэффициент пересчёта (м вод. ст.).

## Линейная интерполяция (calculateInterpolated)

```
value = valueLeft + (coordTarget - coordLeft) / (coordRight - coordLeft) * (valueRight - valueLeft)
```

Результат ограничивается `fitInRange` по диапазону соседних значений.

## Диапазоны

```
isInRange(value, a, b) = (a <= value && value <= b) || (b <= value && value <= a)   # включая границы
fitInRange(value, a, b) = clamp(value, a, b)
```

Порядок границ неважен (min/max могут быть перепутаны).

## Единицы давления (PressureUnits / UnitConversion)

- `pressureKgsToMpa(kgs)` — кгс/см² → МПа
- `pressureMpaToKgs(mpa)` — МПа → кгс/см²

## Форматирование (FormattingProps, CommaFormatter, PressureFormatter)

| Константа/метод | Формат |
|---|---|
| `DECIMAL_FORMATTER` | 3 знака после запятой |
| `FLOAT_FORMATTER` | 2 знака после запятой |
| `DOUBLE_FORMATTER` | 7 знаков после запятой |
| `CommaFormatter.format2digits(float)` | 2 знака, с запятой |
| `PressureFormatter.format(float)` | форматирование давления |
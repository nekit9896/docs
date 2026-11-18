---
id: KB-CALC-ALGO-LU-GRAV-001
title: LuGravitySegsAlg — самотёчные участки (HYDRO-173)
service: hydro-calculation
group: algorithms
source: confluence/repo_description_hydro-calculation#10.Algorithm Layer (LuGravitySegsAlg)
requires: [KB-CALC-ALGO-001, KB-CALC-TAGS-LU-001]
related: [KB-CALC-FORMULA-001, KB-CALC-SIDEFX-001]
status: verified
---

# LuGravitySegsAlg — расчёт самотёчных участков на ТУ

## Методы
- `calc()` — инициализирует подписки на события.
- `updateAndCalcLu(luName)` — обновить данные и посчитать.
- `calcGravityForLu(luName)` — самотёки в реальном времени;
  `calcGravityScheduleForLu(luName)` — плановые самотёки.
- `calcGravitySegs(...)` — основной алгоритм расчёта самотёчного участка.
- `getPassPointIndex(...)` — поиск перевальной точки.
- `registerAlarm(...)` / `clearAlarm(...)` — аларм о самотёке (LU_ALMGRAVITY,
  LU_ALMGRAVITYPOSSIBLE).

## Структуры данных

```java
record LuData(
    List<Pair<Float, String>> allKipsSortedByKm,
    List<Float> luKmList,
    List<Float> luHeightList,
    List<Integer> heightPeakIndexes,
    Integer controlState,
    Float gravityPossible
) {}

record GravityReport(
    Float passPoint,
    List<String> gravitySegsList,
    Float passPointPossible
) {}
```

## Алгоритмы поиска
- `findPeakIndexesPlateauVersion()` — пики с учётом плато (горизонтальных участков).
- `findPeakIndexes()` — пики без учёта плато.
- `findIntersectionWalkFromRight()` — пересечение линии самотёка с профилем трубы справа налево.
- `findIndexIntersectionWalkFromLeft()` — то же слева направо.

## Теги
LU_KM, LU_HEIGHT, LU_GRAVITYSEGS, LU_GRAVITYPOSSIBLE, LU_GRAVITYSEGSSCHEDULE,
LU_PASSPOINTS, LU_PASSPOINTSPOSSIBLE — см. KB-CALC-TAGS-LU-001.
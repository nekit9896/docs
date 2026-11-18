---
id: KB-CALC-ALGO-LU-IND-001
title: Индикаторы контроля и связи (LuIndicatorControlAlg, LuIndicatorLinkAlg)
service: hydro-calculation
group: algorithms
source: confluence/repo_description_hydro-calculation#10.Algorithm Layer (LuIndicatorControlAlg HYDRO-91, LuIndicatorLinkAlg HYDRO-92)
requires: [KB-CALC-ALGO-001, KB-CALC-STATE-001]
related: [KB-CALC-TAGS-LU-001, KB-CALC-ALGO-LU-CTRL-001]
status: verified
---

# LuIndicatorControlAlg — индикатор контроля (HYDRO-91)

- `calc()` → обработка всех ЛУ в scope → `processLu(luName)` (подписка) →
  `calcIndicatorControlCB(...)` (расчёт).
- `getState(List<Tag>)` определяет состояние — enum `IndicatorControlState`
  (значения — KB-CALC-STATE-001).
- Запись: тег `LU_INDICATORCONTROL`.

# LuIndicatorLinkAlg — индикатор связи (HYDRO-92)

- `calc()` → обработка ЛУ → `processLu` (подписка) → `calcIndicatorLinkCB(...)`.
- `calcIndicatorLinkState(...)` — состояние связи; enum `IndicatorLinkState`
  (значения — KB-CALC-STATE-001).
- Запись: тег `LU_INDICATORLINK`; связан с алармами
  LU_ALMKIPCOUNTLINK / LU_ALMKIPALLLINK (KB-CALC-ALGO-LU-CTRL-001).
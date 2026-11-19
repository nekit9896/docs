---
id: KB-CALC-ALGO-SGLU-UR-001
title: Алгоритмы Sglu*/Ur* (сегменты, расходомеры)
service: hydro-calculation
group: algorithms
source: confluence/repo_description_hydro-calculation#10.Algorithm Layer (SgluPartGrzdvActivityAlg, SgluVisibleAlg, UrAlmDevRangeMaxMinAlg, UrQVmomDeltaAlg)
requires: [KB-CALC-ALGO-001, KB-CALC-TAGS-UR-001]
related: [KB-CALC-TAGS-LU-001, KB-CALC-SIDEFX-001]
status: verified
---

# SgluPartGrzdvActivityAlg — активность сегмента (HYDRO-146)

- `calc()` → все ЛУ в scope; `processLu(luName)` — подписки на задвижки;
  `calcSgluPartGrzdvActivityCB(...)` — расчёт.
- Теги: `SGLU_PARTGRZDV` (`.PartGRZDV` — список задвижек),
  `GRZDV_STATUS` (`.Status`), `GRZDV_ACTIVITY` (`.Activity`).

# SgluVisibleAlg — видимость сегмента (HYDRO-198)

- `calc()` → все ЛУ; `processLu` (подписки); `calcSgluVisibleCB(...)` — расчёт.

## Логика видимости (таблица истинности)

| Priority | ControlOn | Activity | Visible |
|---|---|---|---|
| 0 | — | — | false |
| >0 | 0 | true | true |
| 1 | 1 | — | true |
| иначе | — | — | false |

# UrAlmDevRangeMaxMinAlg — коридор расхода (HYDRO-228)

- Контроль выхода расхода за границы коридора: `calcAlmDevRangeMaxMinCB(...)`.
- Теги: `UR_QVMOMDELTARANGEMAX/MIN` (пределы),
  `UR_ALMQVMOMRANGEMAX/MIN` (алармы превышения).

# UrQVmomDeltaAlg — отклонения расхода (HYDRO-229)

- Подписка, `calcUrEvents(...)` — расчёт отклонения.
- Теги: `UR_QVMOM` (автоматический расход), `UR_QVMOMMANUAL` (ручной),
  `UR_QVMOMSTATION` (стационарный), `UR_QVMOMDELTA` (отклонение),
  `UR_ALMQVMOMINVALID` (флаг невалидности).
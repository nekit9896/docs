---
id: KB-CALC-TAGS-UR-001
title: Теги UR / SGLU / GRZDV / ZDV / PLTM
service: hydro-calculation
group: tags
source: confluence/repo_description_hydro-calculation#11.Structure Layer (UrParameters, SgluParameters, GrzdvParameters, ZdvParameters, PltmParameters)
requires: [KB-CALC-MODEL-001]
related: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-TAGS-LU-001]
status: verified
---

# Теги UR_* (расходомер)

| Тег | Описание |
|---|---|
| `UR_QVMOM` | моментальный расход |
| `UR_QVMOMMANUAL` | ручной расход |
| `UR_QVMOMSTATION` | стационарный расход |
| `UR_QVMOMDELTA` | отклонение расхода |
| `UR_ALMQVMOMINVALID` | флаг невалидности |
| `UR_ALMQVMOMRANGEMAX` / `UR_ALMQVMOMRANGEMIN` | аларм макс/мин диапазона |
| `UR_QVMOMDELTARANGEMAX` / `UR_QVMOMDELTARANGEMIN` | верхний/нижний предел отклонения расхода (коридор) |
| `UR_DISABLE` | отключён |
| `UR_MANUAL` | ручной режим |
| `UR_KM` | километр |

# Теги SGLU_* (сегмент)

| Тег | Описание |
|---|---|
| `SGLU_VISIBLE` | видим |
| `SGLU_ACTIVITY` | активен |
| `SGLU_PARTGRZDV` | список задвижек (`.PartGRZDV`) |
| `SGLU_PARTPLTM` | список плотмеростроений |
| `SGLU_PARTUR` | список расходомеров |
| `SGLU_PRIORITY` | приоритет |
| `SGLU_CONTROLON` | контроль включён |
| `SGLU_DIAMETER` | диаметр |
| `SGLU_KM` | километр |

# Теги GRZDV_* / ZDV_* (задвижка / клапан)

| Тег | Описание |
|---|---|
| `GRZDV_STATUS` (`.Status`) | статус задвижки |
| `GRZDV_ACTIVITY` (`.Activity`) | активность сегмента по задвижкам |
| `ZDV_STATUS` | статус клапана |
| `ZDV_ACTIVITY` | активность клапана |

# Теги PLTM_* (плотмеростроение)

| Тег | Описание |
|---|---|
| `PLTM_RO` | плотность |
| `PLTM_ROMANUAL` | ручная плотность |
| `PLTM_ISMANUAL` | ручной режим |
| `PLTM_DISABLE` | отключён |
| `PLTM_KM` | километр |
| `PLTM_ALMROINVALID` | флаг невалидности |
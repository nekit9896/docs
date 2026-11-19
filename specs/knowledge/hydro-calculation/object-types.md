---
id: KB-CALC-MODEL-001
title: Типы объектов и иерархия (hydro-calculation)
service: hydro-calculation
group: domain
source: confluence/repo_description_hydro-calculation#«Важные константы», #10.BaseAlgorithm, «Точки интеграции»
requires: []
related: [KB-CALC-TAGS-LU-001, KB-CALC-TAGS-KIP-001, KB-CALC-TAGS-UR-001, KB-CALC-API-001]
status: verified
---

# Типы объектов

| Константа | Тип | Расшифровка |
|---|---|---|
| `MT_TYPE` | `MT` | Магистральный Трубопровод (МП) |
| `LU_TYPE` | `LU` | Линейный Участок (ЛУ) |
| `KIP_TYPE` | `KIP` | Датчик давления |
| `GRZDV_TYPE` | `GRZDV` | Задвижка |
| `SGLU_TYPE` | `SGLU` | Сегмент |
| `ZDV_TYPE` | `ZDV` | Клапан |
| `UR_TYPE` | `UR` | Расходомер |
| `PLTM_TYPE` | `PLTM` | Плотмеростроение |

- `ANY_ROOT = "."` — суффикс/маркер для корневых тегов.
- `MIN_DENSITY = 500f` — минимальная плотность (кг/м³), см. KB-CALC-FORMULA-001.

## Иерархия (по фактическим обращениям в коде)

- Обход объектов — через Evo API: `objectNames(pattern, type)`,
  `getObjectChildren(parent)`, `getObjectParent(child)`, `objectExists(name)`.
- Датчики KIP находятся внутри ЛУ (`BaseAlgorithm.getKipFromLu(luName)`).
- Сегменты SGLU входят в ЛУ (`LuRoDistribAlg.dataLuSglus`), внутри сегмента —
  задвижки GRZDV (`SGLU_PARTGRZDV`), плотмеростроения PLTM (`SGLU_PARTPLTM`),
  расходомеры UR (`SGLU_PARTUR`).
- Имя ЛУ маппится в читаемое имя МП (`luName2MtReadable`).
- Полный путь объекта в сообщении аларма: `.МП.ТУ.ЛУ.ЛУ..Текст.n`
  (см. KB-CALC-SIDEFX-001).
---
id: KB-CALC-ALGO-LU-CTRL-001
title: Алгоритмы Lu*: контроль, алармы, несущая (LuAlm*, LuAutoControl*, LuControl*, LuCounterKip, LuMaxAllowableP, LuNewControlTime, Checklist, DisableAndRemont, GrzdvState)
service: hydro-calculation
group: algorithms
source: confluence/repo_description_hydro-calculation#10.Algorithm Layer (соответствующие Lu*), #11.LuParameters
requires: [KB-CALC-ALGO-001, KB-CALC-TAGS-LU-001]
related: [KB-CALC-STATE-001, KB-CALC-SIDEFX-001, KB-CALC-ALGO-LU-IND-001]
status: verified
---

# Алгоритмы контроля и алармов ЛУ

Описания «только назначение + `calc()`» (детали отсутствуют в источнике):
ChecklistAlg (проверка списка параметров), DisableAndRemontStatusAlg
(статус ремонта/отключения), GrzdvStateAlg (состояние задвижки),
LuCarrierHeadDefAlg (определение несущей ЛУ),
LuControlSetAlg / LuControlUnsetAlg (установка/снятие состояния контроля ЛУ),
LuAutoControlCanceResetlAlg / LuAutoControlOffAlg / LuAutoControlOnAlg /
LuAutoControlTimeLeftAlg (отмена-сброс / отключение / включение / время до
конца автоматического контроля, тег `LU_CONTROLAUTOTIMELEFT`).

## Алармы (LuAlm*)

| Алгоритм | Назначение | Теги |
|---|---|---|
| LuAlmDevHeadCarrierAlg | Аларм отклонения несущей | LU_ALMDEVHEADCARRIER |
| LuAlmKipAllLinkAlg | Аларм потери связи со всеми датчиками | LU_ALMKIPALLLINK |
| LuAlmKipCountLinkAlg | Аларм потери связи с числом датчиков | LU_ALMKIPCOUNTLINK |
| LuAlmPressDevAlg | Аларм отклонения давления | LU_ALMDEVPRESS |
| LuAlmRateLimitPressAlg | Аларм превышения предела скорости изменения давления | LU_ALMRATELIMITPRESS |

## LuCounterKipAlg — подсчёт активных датчиков

- `calc()` — запускается с задержкой 2 секунды, повторяется каждые 2 секунды.
- `countKipOnline()` — считает активные датчики по давлению (`KIP_PRESS`).
- `getKipFromLu(luName)` — датчики из ЛУ.
- Пороговые теги: `LU_COUNTKIPNOSTATION`, `LU_LIMITKIP`.

## LuMaxAllowablePAlg — максимально допустимые давления (HYDRO-78)

- Расчёт несущей (LU_CARRIERDEF): `getNewDef(...)` применяет правила,
  `applyCorrections(...)` — ограничения по диапазонам км,
  `getRulesByIntervals(...)` парсит правила из строки.
- `lastRulesByTagName` — кэш последних применённых правил (отслеживание изменений).
- Связанные теги: LU_PRESSMANUALLIMIT, LU_ALMCARRIERONUSER.

## LuNewControlTimeAlg — перенос времени контроля

- Подписка на `LU_SETTIMESHIFT`; событие → `performTimeshift(...)`
  переносит значения датчиков на новую дату.
- `loadHistorySliceAtDatetime(...)` — история значений на момент времени;
  `getTagsForLu(luName)` — список тегов для выгрузки.
- Теги: `LU_NEWCONTROLTIME`, `LU_SETTIMESHIFT`.
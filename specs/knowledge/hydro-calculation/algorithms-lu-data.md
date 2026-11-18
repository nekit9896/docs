---
id: KB-CALC-ALGO-LU-DATA-001
title: Алгоритмы Lu*: данные, плотность, план, трассировка (LuDataThinning, LuDiffQ, LuRoDistrib, LuStation, LuTracing, LuUnified, PumpingPlan)
service: hydro-calculation
group: algorithms
source: confluence/repo_description_hydro-calculation#10.Algorithm Layer (LuDataThinningAlg, LuDiffQAlg, LuRoDistribAlg, LuStationAlg, LuTracingAlg, LuUnifiedAlg, PumpingPlanAlg)
requires: [KB-CALC-ALGO-001, KB-CALC-TAGS-LU-001]
related: [KB-CALC-FORMULA-001, KB-CALC-TAGS-KIP-001]
status: verified
---

# LuDataThinningAlg — прореживание данных (HYDRO-74)

- Прореживание/фильтрация/сглаживание сырых данных ЛУ: берёт
  `LU_CARRIER_DATA1`, `LU_CARRIER_DATA2`, `LU_KM`, пишет результат в
  `LU_CARRIERDEF`, `LU_KM`, `LU_CARRIER_DATA1/2`.
- `getPipeSlices()` — извлечение срезов трубопровода, проверка корректности,
  удаление внутренних повторов (кроме краевых);
  возвращает `Triple<LinkedList<Slice>, Integer, Float>`.
- `thinByInterpolation()` — удаляет срезы, совпадающие с интерполяцией между
  соседними (точность **0.001**).
- `thinByScale()` — удаляет срезы с расстоянием между соседними
  `< coordScaleEpsilon` (**1/3000 от длины**) или попадающие внутрь диапазона
  между соседними.
- `Slice (record float km, float v1, float v2)`.
- `dryRunThinning` (MtProps) — режим тестирования прореживания.

# LuDiffQAlg — разница расходов (HYDRO-276)

- Контроль разницы расходов между **краевыми расходомерами**
  (`extractBorderUR(luName)` — по координате).
- `calcAvg()` — каждые 2 секунды, средние значения за час.
- Теги `.TI.DiffQ*` / алармы `.Alm.AlmDevQ*` — см. KB-CALC-TAGS-LU-001.
- `History (class)`: `lastPoll: long`, `fetchedData: TreeMap<Long, Float>`.

# LuRoDistribAlg — распределение плотности по ТУ (HYDRO-224)

- Подписки на LU, SGLU, UR, PLTM, KIP; callback'и `calcSgLuParamsCB`,
  `calcUrParamsCB`, `calcPltmParamsCB`; основной цикл `calcRoDistrib()`.
- Планировщик: расчёт каждые **1000 мс с задержкой 2000 мс**.
- Состояние: `dataLuList`, `dataRoDistrib`, `dataKmDistrib`, `dataDensDef`,
  `dataDensLimit`, `dataDensTime`, `dataPrevCalcTime`, `dataSglu`,
  `dataLuSglus`, `dataQvmom`, `dataQvmomKm`, `dataRo`, `dataRoKm`.
- Ручной ввод: `initDataDistrib(...)` (LU_RODISTRIBMANUAL).

# LuStationAlg — стационарность давлений на ТУ (HYDRO-161)

- `calc()` → подписки; `collectLuSettingsAndCalc(...)`;
  `triggerOnKipUpdates(...)` — триггер на обновления датчиков;
  `calcStationsLu(luName)` — расчёт стационарности.
- Параметры: `LU_COUNTKIPNOSTATION` (порог нестационарных),
  `LU_LIMITKIP` (порог активных датчиков).

# LuTracingAlg — трассировка (HYDRO-406)

- Включение/выключение (`luTraceOnOff`), `startTracingFor`/`stopTracingFor`,
  итерации `doTraceIteration`, `registerDataItem(...)` регистрирует тег,
  `getTraceTTLSecs(...)` — TTL.
- `nameToData: Map<String, HashMap<Pair<String,String>, LinkedHashMap<Long,String>>>`;
  ключ пары — (тег_чтения, тег_записи), значение — LinkedHashMap с TTL.
- Теги LU_TRACE* — см. KB-CALC-TAGS-LU-001.

# LuUnifiedAlg — унифицированные диапазоны отклонений

Подписки на 6 параметров (значение ЛУ применяется ко вложенным объектам,
`updateNested(...)`):

| С ЛУ | На объектах |
|---|---|
| LU_UNIFIED_PRESSDELTARANGEMAX | KIP_PRESSDELTARANGEMAX |
| LU_UNIFIED_PRESSDELTARANGEMIN | KIP_PRESSDELTARANGEMIN |
| LU_UNIFIED_QVMOMDELTARANGEMAX | UR_QVMOMDELTARANGEMAX |
| LU_UNIFIED_QVMOMDELTARANGEMIN | UR_QVMOMDELTARANGEMIN |
| LU_UNIFIED_PRESSDELTASCHEDULERANGEMAX | KIP_PRESSDELTASCHEDULERANGEMAX |
| LU_UNIFIED_PRESSDELTASCHEDULERANGEMIN | KIP_PRESSDELTASCHEDULERANGEMIN |

# PumpingPlanAlg — план перекачки

- `calc()` — планировщик на 60 минут; `tickPlan()` — тик каждую минуту.
- `updatePlans(...)` / `updatePlansByKipEvent(...)` / `updatePlanForLu(luName)`;
  `getRegimesData(...)` парсит режимы из JSON.
- `luPlans: Map<имя ЛУ, Map< Pair<ZonedDateTime,ZonedDateTime>, Map<тег, значение>>>`.
- Теги: LU_ARMT_PUMPPLAN, LU_SCHEDULEREGIMNAME (KB-CALC-TAGS-LU-001).
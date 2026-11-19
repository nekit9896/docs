---
id: KB-CALC-ALGO-001
title: AlgoManager, BaseAlgorithm, реестр алгоритмов
service: hydro-calculation
group: algorithms
source: confluence/repo_description_hydro-calculation#4.Algorithm Manager, #10.BaseAlgorithm, #5.Algorithm Status
requires: [KB-CALC-OVERVIEW-001]
related: [KB-CALC-FORMULA-001, KB-CALC-API-001, KB-CALC-STATE-001]
status: verified
---

# AlgoManager

- `@Component`, инициализация `@PostConstruct initAlgorithms()` через `AlgoFactory`.
- `@Scheduled(fixedRate = 60000)` — все алгоритмы каждые 60 секунд
  (`runAllAlgorithms()` → `algo.run()`), ошибки логируются.
- `@PreDestroy` — очистка.

# AlgoStatus

Поля: `algoName`, `startTime`, `success`, `errorMsg` — отслеживание выполнения.

# BaseAlgorithm — общий каркас

## Поля
`evo` (Evo API), `data` / `dataInvalid` (кэши значений/флагов),
`luName2MtReadable` (ЛУ → читаемое имя МП), `knownSubscriptions`,
`knownExecutors`, `lastClock`.

## Методы
| Метод | Факт |
|---|---|
| `run()` | запуск с замером времени и обработкой исключений; `calc()` — абстрактный |
| `getMtNames(scope)` | список МП с фильтром по `MtProps.scope` |
| `calculateHead(pressure, density, height)` | напор — KB-CALC-FORMULA-001 |
| `calculateInterpolated(...)` | интерполяция — KB-CALC-FORMULA-001 |
| `setValueAndInvalid(tag, value, invalid)` | запись тега + флаг невалидности + кэш |
| `setAlarm(tag, text, text0, value, alertClassName, sequencedId, occuredAt)` | аларм через `evo.makeAlarm()` |
| `getParseableAlarmMessageForLu(luName, message)` | формат сообщения: `.МП.ТУ.ЛУ.ЛУ..Текст.n` (KB-CALC-SIDEFX-001) |
| `getUniqueObjects` / `getUniqueParentObjects` | уникальные имена объектов из списка тегов |
| `getKipFromLu(luName)` | датчики KIP внутри ЛУ |
| `getFiniteValueOrNull` / `getIntegerValueOrNull` / `getStringValueOrNull` / `getBooleanValueOrNull` / `getListStringOrNull` | безопасное чтение (валидация — KB-CALC-API-001) |
| `isInRange` / `fitInRange` | диапазоны — KB-CALC-FORMULA-001 |
| `destroy()` | освобождение подписок и исполнителей |

# Реестр алгоритмов (40 классов, все наследуют BaseAlgorithm)

| Алгоритм | Фрагмент с деталями |
|---|---|
| ChecklistAlg, DisableAndRemontStatusAlg, GrzdvStateAlg | KB-CALC-ALGO-LU-CTRL-001 (описание: только назначение + `calc()`) |
| KipAlarmsAlg, KipAlmDevRangeMaxMinAlg, KipHeadAlg, KipHeadDeltaPressAlg, KipHeightAlg, KipPressRangeAlg, KipPressRateAlg, KipStationAlg, KipVisibleAlg | KB-CALC-ALGO-KIP-001 |
| LuAlmDevHeadCarrierAlg, LuAlmKipAllLinkAlg, LuAlmKipCountLinkAlg, LuAlmPressDevAlg, LuAlmRateLimitPressAlg | KB-CALC-ALGO-LU-CTRL-001 |
| LuAutoControlCanceResetlAlg, LuAutoControlOffAlg, LuAutoControlOnAlg, LuAutoControlTimeLeftAlg | KB-CALC-ALGO-LU-CTRL-001 |
| LuCarrierHeadDefAlg, LuControlSetAlg, LuControlUnsetAlg, LuCounterKipAlg, LuMaxAllowablePAlg, LuNewControlTimeAlg | KB-CALC-ALGO-LU-CTRL-001 |
| LuDataThinningAlg, LuDiffQAlg, LuRoDistribAlg, LuStationAlg, LuTracingAlg, LuUnifiedAlg, PumpingPlanAlg | KB-CALC-ALGO-LU-DATA-001 |
| LuGravitySegsAlg | KB-CALC-ALGO-LU-GRAV-001 |
| LuIndicatorControlAlg, LuIndicatorLinkAlg | KB-CALC-ALGO-LU-IND-001 |
| SgluPartGrzdvActivityAlg, SgluVisibleAlg, UrAlmDevRangeMaxMinAlg, UrQVmomDeltaAlg | KB-CALC-ALGO-SGLU-UR-001 |
# Матрица «модуль репозитория ↔ кейсы» (trace)

Назначение: привязка модулей `hydro-calculation` (и далее
`hydro-history-and-model`) к сценариям тестирования. Колонка «Кейсы»
заполнена в фазе F (валидация тест-планов по описаниям репозиториев, D33).

Кандидаты в колонку «Кейсы» — `case_conflu` вида `HY-CALC-<NNN>`,
`HY-HIST-<NNN>`, `HY-SYS-<NNN>` (см. `cases/`).

Источник модулей: `confluence/repo_description_hydro-calculation` (полный
реестр из 40 алгоритмов; строка «Проанализировано» подтверждает полноту).

Легенда: **жирным** — прямое упоминание класса в кейсе; `*` — привязка по
смыслу (назначение алгоритма ↔ название/логика кейса, прямого упоминания нет).

| Модуль (класс) | Тикет | Назначение | Кейсы |
|---|---|---|---|
| ChecklistAlg | — | Проверка списка параметров | — (нет кейсов; белое пятно) |
| DisableAndRemontStatusAlg | — | Статус ремонта/отключения | **HY-CALC-060** |
| GrzdvStateAlg | — | Состояние задвижки | **HY-CALC-045**, HY-CALC-048* |
| KipAlarmsAlg | — | Алармы датчиков давления | **HY-CALC-018**, **HY-CALC-040**, **HY-CALC-041** |
| KipAlmDevRangeMaxMinAlg | — | Выход давления за диапазон | **HY-CALC-014**, **HY-CALC-073**, **HY-CALC-085**, HY-CALC-015…017* |
| KipHeadAlg | — | Напор датчиков | **HY-CALC-001**, HY-CALC-002…004* |
| KipHeadDeltaPressAlg | — | Разница напора | **HY-CALC-062** |
| KipHeightAlg | — | Высота датчиков | **HY-CALC-055**, **HY-CALC-082**, HY-CALC-002* |
| KipPressRangeAlg | — | Давление в диапазоне | **HY-CALC-009**, **HY-CALC-073**, **HY-CALC-085** |
| KipPressRateAlg | — | Скорость изменения давления | **HY-CALC-033**, **HY-CALC-042**, **HY-CALC-043**, HY-CALC-065* |
| KipStationAlg | — | Стационарность датчиков | HY-CALC-023…025* (KIP_STATION) |
| KipVisibleAlg | — | Видимость датчиков | **HY-CALC-061** |
| LuAlmDevHeadCarrierAlg | — | Аларм отклонения несущей | **HY-CALC-013** |
| LuAlmKipAllLinkAlg | — | Аларм потери связи со всеми | HY-CALC-035* (AlmKIPAllLink), HY-CALC-084* |
| LuAlmKipCountLinkAlg | — | Аларм потери связи с числом | HY-CALC-036* (AlmKIPCountLink) |
| LuAlmPressDevAlg | — | Аларм отклонения давления | **HY-CALC-032** |
| LuAlmRateLimitPressAlg | — | Аларм предела скорости давления | HY-CALC-033*, HY-CALC-065* (PressRateKiplimit) |
| LuAutoControlCanceResetlAlg | — | Отмена/сброс автоконтроля | HY-CALC-029*, HY-CALC-072* |
| LuAutoControlOffAlg | — | Отключение автоконтроля | HY-CALC-031* |
| LuAutoControlOnAlg | — | Включение автоконтроля | HY-CALC-028* |
| LuAutoControlTimeLeftAlg | — | Время до автоконтроля | **HY-CALC-028**, HY-CALC-030* |
| LuCarrierHeadDefAlg | — | Определение несущей ЛУ | **HY-CALC-010**, HY-CALC-011…012* |
| LuControlSetAlg | — | Установка контроля ЛУ | **HY-CALC-005**, **HY-CALC-008**, **HY-CALC-028** |
| LuControlUnsetAlg | — | Снятие контроля ЛУ | **HY-CALC-007** |
| LuCounterKipAlg | — | Подсчёт активных датчиков | **HY-CALC-035**, HY-CALC-036* |
| LuDataThinningAlg | HYDRO-74 | Прореживание данных ЛУ | **HY-CALC-044**, **HY-CALC-068** |
| LuDiffQAlg | HYDRO-276 | Разница расходов | **HY-CALC-019**, **HY-CALC-075**, HY-CALC-020…022*, HY-CALC-058*, HY-CALC-070* |
| LuGravitySegsAlg | HYDRO-173 | Самотёчные участки | **HY-CALC-038**, HY-CALC-039*, HY-CALC-059*, HY-CALC-069* |
| LuIndicatorControlAlg | HYDRO-91 | Индикатор контроля | HY-CALC-037* (0–5) |
| LuIndicatorLinkAlg | HYDRO-92 | Индикатор связи | HY-CALC-035*, HY-CALC-036* |
| LuMaxAllowablePAlg | HYDRO-78 | Максимально допустимые давления | **HY-CALC-010**, **HY-CALC-011**, **HY-CALC-082**, HY-CALC-012* |
| LuNewControlTimeAlg | — | Перенос времени контроля | **HY-CALC-064** |
| LuRoDistribAlg | HYDRO-224 | Распределение плотности | **HY-CALC-051**, **HY-CALC-052**, **HY-CALC-067** |
| LuStationAlg | HYDRO-161 | Стационарность давлений на ТУ | **HY-CALC-026**, **HY-CALC-071**, HY-CALC-027* |
| LuTracingAlg | HYDRO-406 | Трассировка | **HY-CALC-049**, HY-CALC-050*, HY-CALC-066* |
| LuUnifiedAlg | — | Унифицированные диапазоны | **HY-CALC-053** |
| PumpingPlanAlg | — | План перекачки | **HY-CALC-063**, HY-CALC-080* (KIP_ROSCHEDULE) |
| SgluPartGrzdvActivityAlg | HYDRO-146 | Активность сегмента | **HY-CALC-045**, HY-CALC-046* |
| SgluVisibleAlg | HYDRO-198 | Видимость сегмента | HY-CALC-047* |
| UrAlmDevRangeMaxMinAlg | HYDRO-228 | Коридор расхода | **HY-CALC-034** |
| UrQVmomDeltaAlg | HYDRO-229 | Отклонения расхода | **HY-CALC-074**, HY-CALC-079* (UR_ALMQVMOMINVALID) |

## hydro-history-and-model: модули ↔ HY-HIST-кейсы

Привязка на уровне модулей (фрагменты KB-HM-*); детализация — в `cases/hydro-history-and-model/`.

| Модуль (фрагмент) | Кейсы |
|---|---|
| Менеджер сессий, статусы (KB-HM-SESSIONS-001) | HY-HIST-001…013 (lifecycle) |
| Плеер Timeline/tick (KB-HM-PLAYER-001) | HY-HIST-014…020 (historical), HY-HIST-033…036 (watermark-progress) |
| SessionWorker (KB-HM-WORKER-001) | HY-HIST-021…025 (modelling), HY-HIST-047…049 (timeshift) |
| WorkerExecutor / команды (KB-HM-EXEC-001) | HY-HIST-047…049 (timeshift) |
| Data Exchange (KB-HM-ZIP-001) | HY-HIST-026…029 (import), HY-HIST-030…032 (export) |
| Отказоустойчивость (KB-HM-FAULT-001) | HY-HIST-037…039 (fault-tolerance) |
| Конфигурация (KB-HM-CONFIG-001/002) | HY-HIST-040…044 (config-edge-cases) |
| Сохранение модельной сессии (KB-HM-SAVE-001) | HY-HIST-045…046 (save-play) |
| Watermark-сервис (KB-HM-WATERMARK-001) | HY-HIST-033…036 |
| Очистка импортированных (KB-HM-CLEANUP-001) | HY-HIST-029* (ttl imported), HY-HIST-013* (TTL) |

## system-tests: HY-SYS ↔ базовые кейсы

Системные сценарии — цепочки сервисов; привязка к модулям — через базовые
кейсы: alarm-stubs (HY-SYS-001…026) → HY-CALC-* (колонки выше);
hist-derived (HY-SYS-027…045) → HY-HIST-*; new-scenarios (HY-SYS-046…052) —
сквозные, щупы SPOT_* (KB-SYS-TESTSTAND-001).

## Кросс-сверки (выполнено в фазе F, 2026-11-17)

- [x] Формула напора `head = (pressure/density)*101970 + height` ↔ формулировки
  тест-планов/требований `H = P/ρ + Z`. **Итог:** канон — МПа (коэффициент
  101970 согласован, примеры HY-CALC-001 сходятся); в HY-HIST §1.4 P указан в
  «кгс/см²» — расхождение единиц G19 (needs-review HY-HIST кейсов с формулой).
- [x] `MIN_DENSITY = 500` ↔ упоминания в планах. **Итог:** покрыт кейсом
  HY-CALC-003 (аномальная плотность, `MIN_DENSITY=500` в предусловии);
  в KB-CALC-FORMULA-001 / KB-CALC-MODEL-001 — те же значения. Расхождений нет.
- [x] Формат сообщения аларма `.МП.ТУ.ЛУ.ЛУ..Текст.n` ↔ ожидания кейсов.
  **Итог:** формат живёт только в KB-CALC-SIDEFX-001 / KB-CALC-ALGO-001;
  кейсы HY-CALC проверяют теги алармов (`KIP_ALM*`), но не текст сообщения.
  Текст проверяют HY-SYS-046/048 (`alarm.text`) и ориентиры E2E (KB-PLAT-TESTOPS-001)
  — до прихода док-ции alarm-service (G28) сверка текста невозможна. Белое пятно
  зафиксировано.
- [x] Тайминги: AlgoManager 60 с, LuCounterKip 2 с, LuDiffQ.calcAvg 2 с,
  LuRoDistrib 1000/2000 мс, PumpingPlan 60 мин/тик 1 мин ↔ таймауты кейсов.
  **Итог:** кейсы используют `WAIT(2c)` (HY-CALC-035/036/084 — цикл LuCounterKip),
  `WAIT(60c)` (HY-CALC-010/082/042–044/055/058 — цикл AlgoManager),
  `WAIT(60min)` (HY-CALC-063 — скан плана). Таймауты согласованы; расхождений нет.
- [x] Состояния LU_CONTROL (0/1/2) ↔ прежние гипотезы аудита «2/3/4».
  **Итог:** подтверждена модель **0/1/2** (KB-CALC-STATE-001; HY-CALC-037:
  0=ControlOn, 1=Norm, 2=TransitionOn; приоритет 5>4>3>2>1>0 — индикатор).
  Прежняя гипотеза «2/3/4» — отвергнута (вывод фазы 2 был преждевременным).
- [x] C4: «Алгоритмов: 18» ↔ фактический реестр **40** алгоритмов.
  **Итог:** подтверждённое расхождение G1; в KB-PLAT-C4-001 помечено;
  правка C4 — по команде (D36).

## Белые пятна матрицы (в работу после прихода док-ции)

- ChecklistAlg — кейсов нет (проверка списка параметров не покрыта планами; D34:
  новые сценарии не создаём — только фиксация).
- Привязки со звёздочкой `*` — смысловые; при первом прогоне уточнить по коду.
- alarm-service / alarm-view-service: модули не описаны (G28) — HY-SYS-001…026,
  HY-SYS-046/048 остаются заглушками/needs-review.
- data-manager REST (G29) — HY-SYS-049 placeholder.
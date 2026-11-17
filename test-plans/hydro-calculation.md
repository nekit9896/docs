

## Легенда источников

| Сокр. | Документ |
| --- | --- |
| **ТРП** | Технические требования — проект ЭВОСКАДА/Гидроуклон |
| **РА** | Руководство Администратора |
| **АЛГ** | Алгоритмы Гидроуклона |
| **ИО** | Информационное обеспечение (таблицы параметров LU, KIP, SGLU, UR, PLTM…) |
| **СИМ** | Сервис моделирования и истории (v2) (3 режима, диаграммы) |



## 1. Описание микросервиса hydro-calculation

### 1.0 Назначение и контекст

**hydro-calculation** — расчётный микросервис системы СДКУ Гидроуклон. Его задача — непрерывно читать поток текущих данных (давления, расходы, состояния задвижек, уставки), прогонять их через набор гидравлических алгоритмов (расчёт напоров, диапазонов давления, отклонений, индикаторов) и записывать р

езультаты обратно в поток данных и в алармы.
Микросервис является **вычислительным ядром** подсистемы гидроуклона. Он не принимает решений о генерации алармов (это делает alarm-service), но формирует все входные данные, на которые alarm-service реагирует. Он также делает сырые давления пригодными для визуализации, пересчитывая их в напоры, отклонения, коридоры.
Микросервис работает в трёх режимах:
| Режим | Описание | Топик входа | Топик выхода |
| --- | --- | --- | --- |
| **Оперативный** | Обработка живых данных СДКУ в реальном времени | `cspa-main` | `cspa-main` (рассчитанные значения) |
| **Моделирование** | Обработка исторических/смоделированных данных сессии | `model_main_{sessionId}` | `model_main_{sessionId}` |
| **FAST (time-shift)** | Ускоренный перерасчёт истории при переносе контроля | `model_main_{sessionId}` | `model_main_{sessionId}` |

### 1.1 Архитектура развёртывания

| ```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Тестовый стенд                                   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              hydro-calculation (Java Spring Boot)               │    │
│  │                                                                 │    │
│  │  ┌────────────────────────────────────────────────────────────┐ │    │
│  │  │                 (N экземпляров, 1 лидер)                   │ │    │
│  │  │                                                            │ │    │
│  │  │  Экз. 1 (Leader)    Экз. 2 (Follower)    Экз. 3            │ │    │
│  │  │  — ведёт расчёт     — повторяет расчёт     — повторяет     │ │    │
│  │  │  — пишет в Kafka    — хранит буфер         — хранит буфер  │ │    │
│  │  │                                                            │ │    │
│  │  │  При падении лидера → автоматические перевыборы            │ │    │
│  │  │  Новый лидер берёт свой буфер → публикует в Kafka          │ │    │
│  │  └────────────────────────────────────────────────────────────┘ │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌────────────────┐  ┌────────────────────┐   │    │
│  │  │  KafkaSource │  │ CalculationCore│  │  KafkaSink         │   │    │
│  │  │ (потребление)│  │ (57 алгоритмов)│  │  (публикация)      │   │    │
│  │  └──────────────┘  └────────────────┘  └────────────────────┘   │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌────────────────┐  ┌────────────────────┐   │    │
│  │  │  ConfigCache │  │  SessionManager│  │  HealthController  │   │    │
│  │  │  (Redis/CH)  │  │  (управление   │  │  (RAFT heartbeat,  │   │    │
│  │  │              │  │   сессиями)    │  │   /actuator/health)│   │    │
│  │  └──────────────┘  └────────────────┘  └────────────────────┘   │    │
│  │                                                                 │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│         ▲                     ▲                   ▲                     │
│         │                     │                   │                     │
│  ┌──────┴──────┐  ┌───────────┴───────┐  ┌────────┴─────────┐           │
│  │ Kafka       │  │ PostgreSQL        │  │ Redis/ClickHouse │           │
│  │ cspa-main   │  │ (конфигурация LU, │  │ (ИМ, уставки,    │           │
│  │ model_main_*│  │  KIP, профиль,    │  │  кэш расчётов)   │           │
│  │             │  │  уставки)         │  │                  │           │
│  └─────────────┘  └───────────────────┘  └──────────────────┘           │
│         ▲                     ▲                   ▲                     │
│         │                     │                   │                     │
│  ┌──────┴──────┐  ┌───────────┴───────┐  ┌────────┴─────────┐           │
│  │ Контроллеры │  │ data-manager      │  │ alarm-service    │           │
│  │ телемеханики│  │ (ИМ, Redis-кэш)   │  │ (алармы)         │           │
│  │ СДКУ        │  │                   │  │                  │           │
│  └─────────────┘  └───────────────────┘  └──────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
``` |
| --- |

**Иерархия объектов:**
| ```
MT (магистральный трубопровод)
 └─ LU (линейный участок)
     ├─ SGLU (сегмент участка)
     │   ├─ KIP (датчик давления)
     │   ├─ UR (расходомер)
     │   └─ PLTM (плотномер)
     ├─ GRZDV (группа задвижек)
     │   └─ ZDV (задвижка)
     └─ [другие объекты]
``` |
| --- |




### 1.2 Взаимодействие с внешними сервисами

| Сервис | Протокол | Направление | Данные |
| --- | --- | --- | --- |
| **hmi-backend** | REST `POST /v2/tag-set` | ← вход (оператор → hmi-backend → Kafka) | Запись одного тега. Body: `{"tag":"...","data":{"value":"...","invalid":false,"ts":...}}`. Заголовки: `X-USER-FULLNAME`, `X-USER-ALLOW-PATTERNS`. Публикуется в hot topic (→ `cspa-main` или `model_main_{sessionId}`) |
| **hmi-backend** | REST `POST /v2/tags-set` | ← вход | Массовая запись. Body: массив `TagSetRequest` |
| **hmi-backend** | REST `GET /v2/tag-get?tagName=...` | ← вход (оператор → hmi-backend) | Чтение одного тега из DataStream (Kafka consumer → буфер). Ответ: `{"tag":"...","data":{"value":"...","invalid":false,"ts":...,"ts2":...}}` |
| **hmi-backend** | REST `GET|POST /v2/tags-get` | ← вход | Массовое чтение |
| **hmi-backend** | REST `POST /v2/tags-get-history` | ← вход | История из ClickHouse. Body: `{"startTime":...,"endTime":...,"tags":["..."],"limit":1000}` |
| **hmi-backend** | WS V2 `ws://hmi-backend:8080/v2/hotlink` | → выход (hmi-backend → клиент) | Подписка на изменения (`SUBSCRIBE`), чтение (`TAG_GET`), запись (`TAG_SET`). Окно агрегации: **50 мс** |
| **hmi-backend** | WS V2 `PONG` | → выход | Heartbeat-ответ на `PING` |
| **alarm-service** | Kafka (потребление) | → вход | Рассчитанные значения: напоры, отклонения, коридоры |
| **alarm-service** | HTTP POST | → уведомление | `[LU].State.IndicatorControl`, `[LU].State.IndicatorLink`, `[LU].State.CounterKIP` |
| **data-manager** | HTTP GET / Redis | ← конфиг | Теги, уставки, профиль ИМ |
| **alarm-view-service** | Kafka (потребление) | ← вход | Рассчитанные значения (alaрм-источник) |
| **mod-hist** | HTTP POST | ← сессия | `calculationType = REAL_TIME / FAST`, топики |
| **mod-hist** | HTTP POST | ← close | Освобождение ресурсов сессии |

hmi-backend выступает прокси между тестированием и Kafka. POST /v2/tag-set публикует сообщение в топик (конфигурируются через CSPA_TOPICS / TopicRouteConfig). Для hydro-calculation hot topic должен совпадать с cspa-main (оперативный режим) или model_main_{sessionId} (моделирование/FAST)

### 1.3 Константы и числовые значения

| Константа | Значение | Источник | Назначение |
| --- | --- | --- | --- |
| Минимальная плотность для расчёта | 500 кг/м³ | ```
BaseAlgorithm.MIN_DENSITY
``` | Если Ro < 500 → Ro = 500 (защита от деления на слишком малую плотность (влияет на напор)) |
| Плотность по умолчанию | 850 кг/м³ Зависит от конфигурации ТУ | ```
[LU].TI.DensDef
``` | Используется в расчёте несущей |
| Порог формирования партии | Зависит от конфигурации ТУ (обычно 5 кг/м³) | ```
[LU].TI.DensLimit
``` | Если Δρ > DensLimit → новая партия |
| Интервал перерасчёта партий | Зависит от конфигурации ТУ (обычно 3600 с) | ```
[LU].TI.DensTime
``` | Периодичность пересчёта LuRoDistribAlg |
| Диапазон отклонения стационарности (верхний) | Зависит от конфигурации ТУ (обычно 0.5 МПа) | ```
[KIP].TI.DevMaxStation
``` | Порог отклонения для KipStationAlg |
| Диапазон отклонения стационарности (нижний) | Зависит от конфигурации ТУ (обычно 0.1 МПа) | ```
[KIP].TI.DevMinStation
``` | Порог отклонения для KipStationAlg |
| Время установки стационарности | Зависит от конфигурации ТУ (обычно 120 с) | ```
[LU].State.TimeIntSetStation
``` | Минимальное время стабильности |
| Лимит датчиков на связи | Зависит от конфигурации ТУ (обычно 1) | ```
[LU].State.LimitKIP
``` | Порог для IndicatorLink |
| Порог скорости давления | Зависит от конфигурации ТУ (обычно 0.05 МПа/мин) | ```
[LU].TI.PressRateLimit
``` | Порог для LuAlmRateLimitPressAlg |
| Лимит датчиков с превышением скорости | Зависит от конфигурации ТУ (обычно 1) | ```
[LU].TI.PressRateKiplimit
``` | Мин. число датчиков для аларма скорости |
| Интервал МНК-аппроксимации | Зависит от конфигурации ТУ (обычно 60 с) | [LU].TI.PressRateKIPInterval | Окно для алгоритма 2 скорости |
| Макс. число точек истории скорости | Зависит от конфигурации ТУ (обычно 50) | [LU].TI.PressRateHistoryMaxCount | Ограничение буфера |
| Коэффициент пересчета напора | 101970 (МПа) | ```
BaseAlgorithm.calculateHead()
``` | `head = (P/ρ) × K + H`.
В коде константа `101970` для давления в МПа. Преобразует МПа/ (кг/м³) в метры столба жидкости |
| Дельта диапазона давления (верхняя) | Зависит от конфигурации ТУ для каждого KIP
(0.2 МПа) | ```
[KIP].TI.PressDeltaRangeMax
``` | `PressRangeMax = PressStation + ΔMax`
Значение задаётся в конфигурации ТУ для каждого датчика |
| Дельта диапазона давления (нижняя) | Зависит от конфигурации ТУ для каждого KIP
(0.1 МП) | ```
[KIP].TI.PressDeltaRangeMin
``` | PressRangeMin = PressStation − KIP_PRESSDELTARANGEMIN |
| Лимит дебаланса расходов (верхний) | Зависит от конфигурации ТУ (±1.5 м³/ч) | ```
[LU].TI.DiffQmomLimitMax
``` | Граница допустимого дебаланса |
| Лимит дебаланса расходов (нижний) | Зависит от конфигурации ТУ (±1.5 м³/ч) | ```
[LU].TI.DiffQmomLimitMin
``` | Граница допустимого дебаланса |
| Время автопостановки | Зависит от конфигурации ТУ (обычно 180 с) | [LU].State.ControlAutoTimeOut | Обратный отсчёт до автопостановки |
| Порог нестационарных датчиков | Зависит от конфигурации ТУ | [LU].State.CountKIPNoStation | Сколько нестационарных допустимо |
| Интервал трассировки | Зависит от конфигурации ТУ (обычно 10 с) | [LU].State.TraceInterval | Период записи следов |
| TTL трассировки | Зависит от конфигурации ТУ (обычно 60 с) | [LU].State.TracesTTL | Время жизни записей при TracesSave=false |
| Интервал сканера плана | Зависит от application.yml (обычно 60 мин) | PlanScannerProps.planScannerInterval | Периодичность PumpingPlanAlg |



### 1.4 Ключевые понятия и формулы

**Напор** — пьезометрический напор, давление, приведённое к высоте столба жидкости. Это главная расчётная величина.
| ```
Head = (P / ρ) × 101970 + H
``` |
| --- |


| Переменная | Единицы | Описание |
| --- | --- | --- |
| P | МПа | Статическое давление (KIP_PRESS) |
| ρ | кг/м³ | Плотность жидкости (KIP_RO), минимально 500 |
| 101970 | — | Коэффициент: 10⁶/g ≈ 101970 (перевод МПа·м³/кг → м) |
| H | м | Высота датчика над уровнем моря (KIP_HEIGHT) или KIP_HEIGHTCORRECTION при Manual=1 |
| Head | м | Результат: пьезометрический напор |


**Несущая напора (CarrierHeadDef)** — максимальная энергия(нагрузка), которую выдерживает трубопровод без риска разрушения. Рассчитывается по той же формуле, что и напор, но вместо фактического давления берётся предельно допустимое ( `CarrierDef` = `min(PmaxDefault, PressManualLimit)`).
| ```
CarrierDef[km] = min(PmaxDefault[km], PressManualLimit[km])  // в МПа
CarrierHeadDef[km] = (CarrierDef[km] / ρ_def) × 101970 + H[km]
``` |
| --- |


| Переменная | Единицы | Описание |
| --- | --- | --- |
| PmaxDefault | МПа | Заводское предельно допустимое давление (из ИМ) |
| PressManualLimit | МПа | Ручное ограничение оператора (формат: `"км_от,км_до,лимит;..."`) |
| ρ_def | кг/м³ | Плотность по умолчанию (LU_DENSDEF), минимально 500 |
| H[km] | м | Высота на данном км (из конфигурации ТУ) |


**Диапазон давления** — зона допустимых отклонений от базового состояния. Фиксируется при постановке на контроль.
| ```
PressRangeMax = PressStation + PressDeltaRangeMax
PressRangeMin = PressStation − PressDeltaRangeMin
``` |
| --- |

ΔMax и ΔMin — индивидуальные значения для каждого KIP, заданные в ИМ. В примерах тест-кейсов используются 0.2 и 0.1 как типовые значения для демонстрации логики. Граничные значения (ровно на границе) не дают аларма — условие строгое (`>` или `<`).

**Диапазон напора** — границы диапазона давления, пересчитанные в метры столба жидкости.
| ```
HeadRangeMax = (PressRangeMax / ρ) × 101970 + H
HeadRangeMin = (PressRangeMin / ρ) × 101970 + H
``` |
| --- |


**Скорость изменения давления**
Производная давления по времени. Индикатор гидроудара.

*   **Алгоритм 1 (двухточечный):** `V = (P_кон − P_нач) / T` — мгновенно, чувствителен к выбросам

*   **Алгоритм 2 (МНК):** аппроксимация серии значений за `PressRateKIPInterval` сек прямой, наклон = скорость — устойчивее


Порог срабатывания: если количество KIP с `V > PressRateLimit` ≥ `PressRateKiplimit` → `AlmPressRateLimit = true`

**Дебаланс расходов**
Разница расходов на входе и выходе ТУ. Индикатор утечки или неисправности СИКГ.
| ```
DiffQmom = QVmom_входной − QVmom_выходной
``` |
| --- |


**Распределение плотности** — карта партий жидкости в трубопроводе. Каждая партия — это участок трубы с однородной плотностью. Новая партия формируется при смене плотности более чем на 5 кг/м³ (`DensLimit`)
| ```
Если |Ro_новая − Ro_текущая| > DensLimit → новая партия
``` |
| --- |


**Конфигурация ТУ**
Массивы данных, описывающие геометрию и характеристики линейного участка:

*   `LU_KM` — километровые отметки точек конфигурации

*   `LU_HEIGHT` — высоты точек конфигурации

*   `LU_PMAXDEFAULT` — предельно допустимое давление по км

*   `LU_CARRIER_DATA1/2` — дополнительные массивы несущей


Конфигурация ТУ загружается в data-manager и хранится в PostgreSQL/Redis. Это полная параметрическая модель участка: геометрия (км, высоты), механические характеристики (PmaxDefault), технологические параметры (диаметр, плотность).

### 1.5 Алгоритмы — перечень и классификация

**Легенда по триггерам:**

*   **POLL(60с)** — алгоритм запускается каждые 60 секунд по расписанию (AlgoManager)

*   **POLL(2с)** — алгоритм имеет собственный планировщик с интервалом 2 секунды

*   **POLL(1с)** — алгоритм имеет собственный планировщик с интервалом 1 секунду

*   **EVENT** — алгоритм срабатывает по callback'у при изменении конкретного тега (подписка через Evo API)

*   **POLL(60мин)** — алгоритм имеет собственный планировщик с интервалом 60 минут


| # | Название | Класс | Триггер | Логика (кратко) | Выходные теги |
| --- | --- | --- | --- | --- | --- |
| 1 | Проверка чек-листа | `ChecklistAlg` | POLL(60с) | Проверяет наличие объектов MT и LU в метаданных. Если пусто → log.error с диагностикой. **Не влияет на расчёты** | — (только логи) |
| 2 | Статус ремонта/отключения | `DisableAndRemontStatusAlg` | EVENT | Связывает RemontStatus, TU.SetOn/Off с Disable для KIP/UR/PLTM | `KIP/UR/PLTM_DISABLE` |
| 3 | Состояние группы задвижек | `GrzdvStateAlg` | EVENT | Type 1 (OR): Status=1 если хотя бы одна ZDV Status=2. Type 2 (AND): Status=1 только если все ZDV Status=2. Без ZDV → Status=1 | `GRZDV_STATUS`: 0/1 |
| 4 | Алармы датчика | `KipAlarmsAlg` | EVENT | Противоречия Disable/invalid → AlmFailOn | `KIP_ALMFAILON`: true/false |
| 5 | Выход давления за границы | `KipAlmDevRangeMaxMinAlg` | EVENT | Press > PressRangeMax → AlmDevMaxRange. Press < PressRangeMin → AlmDevMinRange. Строгое неравенство. При Control=1 AND Disable=0 | `KIP_ALMDEVMAXRANGE`, `KIP_ALMDEVMINRANGE` |
| 6 | Расчёт напора | `KipHeadAlg` | EVENT | `head = (P/ρ)×101970 + H`. Manual=1 → H=HeightCorrection. P.invalid → head.invalid | `KIP_HEAD`: float, `.invalid` |
| 7 | Отклонение напора/давления | `KipHeadDeltaPressAlg` | EVENT | `headDelta = Head − HeadStation`. `pressDelta = Press − PressStation` | `KIP_HEADDELTA`, `KIP_PRESSDELTA` |
| 8 | Расчёт высоты | `KipHeightAlg` | POLL(60с) | Линейная интерполяция по LU_KM/LU_HEIGHT. Вне диапазона → не рассчитывается | `KIP_HEIGHT`: float (м) |
| 9 | Контроль давления в диапазоне | `KipPressRangeAlg` | EVENT | Аналог №5, записывает в PressRangeAlarm. При Control=1 AND Disable=0 AND SGLU_CONTROLON=true | `KIP_PRESSRANGEALARM`: true/false |
| 10 | Скорость изменения давления | `KipPressRateAlg` | POLL(60с) | Алг.1: V=(P2−P1)/T. Алг.2: МНК. <2 точек → invalid | `KIP_PRESSRATE`: float (МПа/мин) |
| 11 | Стационарность датчика | `KipStationAlg` | EVENT | |Press − PressStationaryMode| ≤ DevMax AND время > TimeIntSetStation → Station=true | `KIP_STATION`: true/false |
| 12 | Видимость датчика | `KipVisibleAlg` | EVENT | Visible = (Disable=0) AND (родительский SGLU Visible=true) | `KIP_VISIBLE`: true/false |
| 13 | Напор выше несущей | `LuAlmDevHeadCarrierAlg` | EVENT | Head > CarrierHeadDef[km] → аларм. **Не подавляется при Control=2** | `LU_ALMDEVHEADCARRIER`: true/false |
| 14 | Потеря связи со всеми | `LuAlmKipAllLinkAlg` | EVENT | CounterKIP ≤ 0 → аларм | `LU_ALMKIPALLLINK`: true/false |
| 15 | Потеря связи с частью | `LuAlmKipCountLinkAlg` | EVENT | 0 < CounterKIP < LimitKIP → аларм | `LU_ALMKIPCOUNTLINK`: true/false |
| 16 | Отклонение по смежным | `LuAlmPressDevAlg` | EVENT | 2+ KIP на SGLU с AlmDevMax/Min → аларм на LU | `LU_ALMPRESSDEV`: true/false |
| 17 | Превышение скорости | `LuAlmRateLimitPressAlg` | EVENT | Count(KIP с V > PressRateLimit) ≥ PressRateKiplimit → аларм | `LU_ALMPRESSRATELIMIT`: true/false |
| 18 | Отмена/сброс автоконтроля | `LuAutoControlCanceResetlAlg` | EVENT | Cancel → TimeLeft=−2. Reset → TimeLeft=ControlAutoTimeOut | `LU_CONTROLAUTOTIMELEFT`: int |
| 19 | Отключение автоконтроля | `LuAutoControlOffAlg` | EVENT | SetAutoControlOff → AutoControlOn=false, TimeLeft=−1 | `LU_AUTOCONTROLON`, `LU_CONTROLAUTOTIMELEFT` |
| 20 | Включение автоконтроля | `LuAutoControlOnAlg` | EVENT | SetAutoControlOn → AutoControlOn=true | `LU_AUTOCONTROLON`: bool |
| 21 | Таймер автопостановки | `LuAutoControlTimeLeftAlg` | POLL(60с) | Station=true AND AutoControlOn=true AND Control=0 → отсчёт. Station=false → −1. TimeLeft=0 → LuControlSetAlg | `LU_CONTROLAUTOTIMELEFT`: −2/−1/0..N |
| 22 | Несущая напора | `LuCarrierHeadDefAlg` | EVENT | CarrierDef = min(PmaxDefault, PressManualLimit). CarrierHeadDef = (CarrierDef/ρ_def)×101970 + H | `LU_CARRIERDEF`: float[], `LU_CARRIERHEADDEF`: float[] |
| 23 | Постановка на контроль | `LuControlSetAlg` | EVENT | Control=0 AND SetControlOn=1 → фиксирует PressStation, QVmomStation, GravitySegsReg, RangeMax/Min. Control→1 | `LU_CONTROL`, `KIP_PRESSSTATION`, `UR_QVMOMSTATION`, `KIP_PRESSRANGEMAX/MIN`, `SGLU_CONTROLON` |
| 24 | Снятие с контроля | `LuControlUnsetAlg` | EVENT | SetControlOff=1 → Control=0, все базовые → invalid | `LU_CONTROL`, все базовые → invalid |
| 25 | Подсчёт активных датчиков | `LuCounterKipAlg` | POLL(2с) | Считает KIP с валидным KIP_PRESS (не invalid, не NaN/Inf) | `LU_COUNTERKIP`: int |
| 26 | Фильтрация конфигурации | `LuDataThinningAlg` | POLL(60с) | 3 фильтра: дубли, шум (<0.001), частота (<1/3000 длины). Края сохраняются | `LU_CARRIERDEF`, `LU_KM`, `LU_CARRIER_DATA1/2` |
| 27 | Разница расходов | `LuDiffQAlg` | POLL(60с) + POLL(2с) | DiffQmom = QV_вход − QV_выход. DiffQavg — среднее за час. 4 аларма | `LU_DIFFQMOM/AVG/AVGSTATION`, `LU_ALMDEVQMOM/AVG/STATION/AVGSTATION` |
| 28 | Самотечные участки | `LuGravitySegsAlg` | EVENT | Перевальные точки (пики конфигурации). Head < H_max → самотек. GravityPossible → прогноз | `LU_GRAVITYSEGS`, `LU_PASSPOINTS`, `LU_ALMGRAVITY`, `LU_ALMGRAVITYPOSSIBLE` |
| 29 | Индикатор контроля | `LuIndicatorControlAlg` | EVENT | Приоритет: 5(Transition) > 4(TimeLeft) > 3(Ranged) > 2(Lonesome) > 1(Norm) > 0(Off) | `LU_INDICATORCONTROL`: 0–5 |
| 30 | Индикатор связи | `LuIndicatorLinkAlg` | EVENT | 2(AllLink) > 1(CountLink) > 0(Norm) | `LU_INDICATORLINK`: 0–2 |
| 31 | Несущая (правила) | `LuMaxAllowablePAlg` | EVENT | Парсит PressManualLimit, применяет min(PmaxDefault, limit) по диапазонам км | `LU_CARRIERDEF`: float[] |
| 32 | Перенос времени | `LuNewControlTimeAlg` | EVENT | SetTimeShift → загружает историю из ClickHouse, записывает как текущие | Перенос KIP/UR значений |
| 33 | Распределение плотности | `LuRoDistribAlg` | POLL(1с) | Manual → использовать. Иначе: партии по DensLimit, расчёт по PLTM/UR | `LU_RODISTRIB`: float[] |
| 34 | Стационарность LU | `LuStationAlg` | EVENT | Нестационарных ≥ CountKIPNoStation → false. Стационарных ≥ LimitKIP AND нестационарных < порог → true | `LU_STATION`: true/false |
| 35 | Трассировка | `LuTracingAlg` | EVENT + POLL | TracesOn → каждые TraceInterval записывает [value, ts]. TTL при Save=false | `KIP_TRACESPRESS/HEAD`, `UR_TRACESQVMOM` |
| 36 | Унификация дельт | `LuUnifiedAlg` | EVENT | Копирует LU_UNIFIED_* → все KIP/UR дочерние | `KIP_PRESSDELTARANGEMAX/MIN`, `UR_QVMOMDELTARANGEMAX/MIN` |
| 37 | План перекачки | `PumpingPlanAlg` | POLL(60мин) + EVENT | Парсит JSON плана, каждую минуту проверяет режим. По KIP-событиям обновляет | `KIP_PRESSSCHEDULE`, `KIP_HEADSCHEDULE`, `LU_SCHEDULEREGIMNAME` |
| 38 | Активность сегмента | `SgluPartGrzdvActivityAlg` | EVENT | PartGRZDV пуст → true. GRZDV_STATUS=1 → true. =0 → false | `SGLU_ACTIVITY`: true/false |
| 39 | Видимость сегмента | `SgluVisibleAlg` | EVENT | Priority=0 → false. Priority>0: (ControlOn=0 AND Activity=true) OR (ControlOn=1 AND Priority=1) → true | `SGLU_VISIBLE`: true/false |
| 40 | Выход расхода за коридор | `UrAlmDevRangeMaxMinAlg` | EVENT | QVmom > QVmomStation + ΔMax → Max=true. < QVmomStation + ΔMin → Min=true | `UR_ALMQVMOMRANGEMAX/MIN` |
| 41 | Отклонение расхода | `UrQVmomDeltaAlg` | EVENT | QVmom_for_calc = Manual? QVmomManual : QVmom. Delta = for_calc − QVmomStation | `UR_QVMOMDELTA`: float |

### 1.6 Справочник ключевых enum-значений и констант

#### LU_CONTROL (состояние контроля ТУ)

| Значение | Имя (enum в коде) | Описание |
| --- | --- | --- |
| 0 | ControlOff | Контроль выключен. Базовое состояние не зафиксировано. Алармы давления/расхода/дебаланса не генерируются |
| 1 | ControlOn | Контроль включён. PressStation, QVmomStation зафиксированы. Алармы активны |
| 2 | TransitionOn | Режим контроля перехода. Базовое состояние зафиксировано. Большинство алармов подавлены, **но AlmDevHeadCarrier генерируется** |

#### LU_INDICATORCONTROL (индикатор контроля)

| Значение | Имя (enum) | Цвет | Условие |
| --- | --- | --- | --- |
| 0 | ControlOn | Зелёный | `Control = 0` — контроль не ведётся |
| 1 | Norm | Зелёный | `Control = 1`, отклонений нет |
| 2 | LonesomeKipAlarmed | Жёлтый | `Control = 1`, одиночные `AlmDevMaxRange/MinRange = true`, `AlmPressDev = false` |
| 3 | RangedKipAlarmed | Красный | `Control = 1`, `AlmPressDev = true` (2+ смежных датчика) |
| 4 | ControlAutoTimeLeft | Оранжевый | `ControlAutoTimeLeft > 0` (идёт отсчёт автопостановки) |
| 5 | TransitionOn | Красный | `Control = 2` (режим перехода) |

#### LU_INDICATORLINK (индикатор связи)

| Значение | Имя | Цвет | Условие |
| --- | --- | --- | --- |
| 0 | Norm | Зелёный | `CounterKIP ≥ LimitKIP` |
| 1 | AlmKipCountLink | Жёлтый | `0 < CounterKIP < LimitKIP` |
| 2 | AlmKipAllLink | Красный | `CounterKIP ≤ 0` |

#### LU_CONTROLAUTOTIMELEFT (таймер автопостановки)

| Значение | Описание |
| --- | --- |
| −2 | Отменено диспетчером (Cancel). При следующем Station=true → −1 |
| −1 | Заблокировано / сброшено / Station=false. Автопостановка не выполняется |
| 0..N | Обратный отсчёт в секундах (N = ControlAutoTimeOut) |

#### GRZDV_STATUS

| Значение | Описание |
| --- | --- |
| 0 | Группа закрыта |
| 1 | Группа открыта |

#### ZDV_STATUS

| Значение | Описание |
| --- | --- |
| 0 | Закрыта |
| 2 | Открыта |
| 3 | Не определена / ремонт |

> **Важно:** GRZDV_STATUS принимает только 0 и 1. Значение 2 — это ZDV_STATUS (состояние отдельной задвижки). GrzdvStateAlg вычисляет GRZDV_STATUS на основе ZDV_STATUS дочерних задвижек.

#### KIP_DISABLE / UR_DISABLE / PLTM_DISABLE

| Значение | Описание |
| --- | --- |
| false (0) | Датчик активен, участвует в расчётах |
| true (1) | Датчик отключён, не участвует в расчётах |

> Тип тега — **boolean**. В Kafka/Redis передаётся как `true`/`false`.

#### KIP_MANUAL / UR_MANUAL

| Значение | Описание |
| --- | --- |
| false (0) | Автоматический режим (данные от СДКУ) |
| true (1) | Ручной режим (данные от оператора: HeightCorrection / QVmomManual) |

#### SGLU_CONTROLON

| Значение | Описание |
| --- | --- |
| false (0) | Сегмент не на контроле |
| true (1) | Сегмент на контроле |



### 1.7 Иерархия тегов

Имя тега в системе однозначно определяет объект и его параметр:

```
{MT}.{LU}.{SGLU}.{KIP/UR/PLTM/GRZDV/ZDV}.{TI/State/Alm/TU}.{Параметр}
```

**Слои в иерархии:**

*   `TI` — технологические параметры (входные и расчётные значения)

*   `State` — состояния (флаги, режимы)

*   `Alm` — алармы

*   `TU` — команды диспетчера (technological unit)




### Справочник тегов

| | Тег (кратко) | Путь | Тип | Источник | Описание |
| --- | --- | --- | --- | --- |
| LU_KM | `{LU}.TI.KM` | float[] | ИМ | Километровые отметки конфигурации |
| LU_HEIGHT | `{LU}.TI.Height` | float[] | ИМ | Высоты конфигурации |
| LU_PMAXDEFAULT | `{LU}.TI.PmaxDefault` | float[] (МПа) | ИМ | Предельно допустимое давление по км |
| LU_PRESSMANUALLIMIT | `{LU}.TI.PressManualLimit` | string | Оператор | Ручные ограничения несущей |
| LU_CARRIERDEF | `{LU}.TI.CarrierDef` | float[] (МПа) | Расчёт | Несущая давления |
| LU_CARRIERHEADDEF | `{LU}.TI.CarrierHeadDef` | float[] (м) | Расчёт | Несущая напора |
| LU_CARRIER_DATA1 | `{LU}.TI.CarrierData1` | float[] | ИМ/Расчёт | Данные несущей 1 |
| LU_CARRIER_DATA2 | `{LU}.TI.CarrierData2` | float[] | ИМ/Расчёт | Данные несущей 2 |
| LU_CONTROL | `{LU}.State.Control` | int (0/1/2) | Расчёт/Команда | Состояние контроля |
| LU_STATION | `{LU}.State.Station` | bool | Расчёт | Стационарность ТУ |
| LU_COUNTERKIP | `{LU}.State.CounterKIP` | int | Расчёт | Число активных датчиков |
| LU_LIMITKIP | `{LU}.State.LimitKIP` | int | ИМ | Лимит датчиков на связи |
| LU_COUNTKIPNOSTATION | `{LU}.State.CountKIPNoStation` | int | ИМ | Порог нестационарных |
| LU_TIMEINTSETSTATION | `{LU}.State.TimeIntSetStation` | int (с) | ИМ | Время установки стационарности |
| LU_AUTOCONTROLON | `{LU}.State.AutoControlOn` | bool | Расчёт/Команда | Флаг автопостановки |
| LU_CONTROLAUTOTIMELEFT | `{LU}.State.ControlAutoTimeLeft` | int | Расчёт | Таймер автопостановки |
| LU_CONTROLAUTOTIMEOUT | `{LU}.State.ControlAutoTimeOut` | int (с) | ИМ | Время автопостановки |
| LU_INDICATORCONTROL | `{LU}.State.IndicatorControl` | int (0–5) | Расчёт | Индикатор контроля |
| LU_INDICATORLINK | `{LU}.State.IndicatorLink` | int (0–2) | Расчёт | Индикатор связи |
| LU_ALMKIPALLLINK | `{LU}.Alm.AlmKIPAllLink` | bool | Расчёт | Аларм: нет связи со всеми |
| LU_ALMKIPCOUNTLINK | `{LU}.Alm.AlmKIPCountLink` | bool | Расчёт | Аларм: связь с частью |
| LU_ALMPRESSDEV | `{LU}.Alm.AlmPressDev` | bool | Расчёт | Аларм: отклонение по смежным |
| LU_ALMDEVHEADCARRIER | `{LU}.Alm.AlmDevHeadCarrier` | bool | Расчёт | Аларм: напор выше несущей |
| LU_ALMPRESSRATELIMIT | `{LU}.Alm.AlmRateLimitPress` | bool | Расчёт | Аларм: превышение скорости |
| LU_ALMGRAVITY | `{LU}.Alm.AlmGravity` | bool | Расчёт | Аларм: самотек |
| LU_ALMGRAVITYPOSSIBLE | `{LU}.Alm.AlmGravityPossible` | bool | Расчёт | Аларм: риск самотека |
| LU_ALMDEVQMOM | `{LU}.Alm.AlmDevQmom` | bool | Расчёт | Аларм: дебаланс (мгновенный) |
| LU_ALMDEVQAVG | `{LU}.Alm.AlmDevQavg` | bool | Расчёт | Аларм: дебаланс (средний) |
| LU_ALMDEVQAVGSTATION | `{LU}.Alm.AlmDevQavgStation` | bool | Расчёт | Аларм: дебаланс (стационарный) |
| LU_ALMCARRIERONUSER | `{LU}.Alm.AlmCarrierOnUser` | bool | Расчёт | Аларм: изменение несущей пользователем |
| LU_DIFFQMOM | `{LU}.TI.DiffQmom` | float (м³/ч) | Расчёт | Мгновенный дебаланс |
| LU_DIFFQAVG | `{LU}.TI.DiffQavg` | float (м³/ч) | Расчёт | Средний дебаланс |
| LU_DIFFQAVGSTATION | `{LU}.TI.DiffQavgStation` | float (м³/ч) | Расчёт | Стационарный дебаланс |
| LU_DIFFQMOMLIMITMAX | `{LU}.TI.DiffQmomLimitMax` | float | ИМ | Верхний лимит дебаланса |
| LU_DIFFQMOMLIMITMIN | `{LU}.TI.DiffQmomLimitMin` | float | ИМ | Нижний лимит дебаланса |
| LU_GRAVITYSEGS | `{LU}.TI.GravitySegs` | string[] | Расчёт | Самотечные участки |
| LU_GRAVITYSEGSREG | `{LU}.TI.GravitySegsReg` | string[] | Расчёт | Слепок самотеков при постановке |
| LU_PASSPOINTS | `{LU}.TI.PassPoints` | float | Расчёт | Перевальные точки |
| LU_PASSPOINTSPOSSIBLE | `{LU}.TI.PassPointsPossible` | float | Расчёт | Возможные перевальные точки |
| LU_GRAVITYPOSSIBLE | `{LU}.TI.GravityPossible` | float (м) | ИМ | Запас для прогноза самотека |
| LU_RODISTRIB | `{LU}.TI.RoDistrib` | float[] | Расчёт | Распределение плотности |
| LU_RODISTRIBMANUAL | `{LU}.TI.RoDistribManual` | string | Оператор | Ручное распределение плотности |
| LU_DENSDEF | `{LU}.TI.DensDef` | float (кг/м³) | ИМ | Плотность по умолчанию |
| LU_DENSLIMIT | `{LU}.TI.DensLimit` | float (кг/м³) | ИМ | Порог формирования партии |
| LU_DENSTIME | `{LU}.TI.DensTime` | int (с) | ИМ | Интервал перерасчёта |
| LU_PRESSRATELIMIT | `{LU}.TI.PressRateLimit` | float (МПа/мин) | ИМ | Порог скорости |
| LU_PRESSRATEKIPLIMIT | `{LU}.TI.PressRateKiplimit` | int | ИМ | Мин. число датчиков для аларма |
| LU_PRESSRATEALGORITHM | `{LU}.TI.PressRateAlgorithm` | int (1/2) | ИМ | Алгоритм расчёта скорости |
| LU_PRESSRATEKIPINTERVAL | `{LU}.TI.PressRateKIPInterval` | int (с) | ИМ | Интервал МНК |
| LU_PRESSRATEHISTORYMAXCOUNT | `{LU}.TI.PressRateHistoryMaxCount` | int | ИМ | Макс. точек истории |
| LU_UNIFIED_PRESSDELTARANGEMAX | `{LU}.TI.UnifiedPressDeltaRangeMax` | float | Оператор | Унифицированная дельта (верх) |
| LU_UNIFIED_PRESSDELTARANGEMIN | `{LU}.TI.UnifiedPressDeltaRangeMin` | float | Оператор | Унифицированная дельта (низ) |
| LU_UNIFIED_QVMOMDELTARANGEMAX | `{LU}.TI.UnifiedQVmomDeltaRangeMax` | float | Оператор | Унифицированная дельта расхода (верх) |
| LU_UNIFIED_QVMOMDELTARANGEMIN | `{LU}.TI.UnifiedQVmomDeltaRangeMin` | float | Оператор | Унифицированная дельта расхода (низ) |
| LU_UNIFIED_PRESSDELTASCHEDULERANGEMAX | `{LU}.TI.UnifiedPressDeltaScheduleRangeMax` | float | Оператор | Унифицированная дельта плана (верх) |
| LU_UNIFIED_PRESSDELTASCHEDULERANGEMIN | `{LU}.TI.UnifiedPressDeltaScheduleRangeMin` | float | Оператор | Унифицированная дельта плана (низ) |
| LU_TU_SETCONTROLON | `{LU}.TU.SetControlOn` | bool | Диспетчер | Команда: поставить на контроль |
| LU_TU_SETCONTROLOFF | `{LU}.TU.SetControlOff` | bool | Диспетчер | Команда: снять с контроля |
| LU_TU_TRANSITIONCONTROLON | `{LU}.TU.TransitionControlOn` | bool | Диспетчер | Команда: режим перехода |
| LU_TU_SETAUTOCONTROLON | `{LU}.TU.SetAutoControlOn` | bool | Диспетчер | Команда: включить автопостановку |
| LU_TU_SETAUTOCONTROLOFF | `{LU}.TU.SetAutoControlOff` | bool | Диспетчер | Команда: выключить автопостановку |
| LU_TU_SETAUTOCONTROLCANCEL | `{LU}.TU.SetAutoControlCancel` | bool | Диспетчер | Команда: отменить автопостановку |
| LU_TU_SETAUTOCONTROLRESET | `{LU}.TU.SetAutoControlReset` | bool | Диспетчер | Команда: сбросить таймер |
| LU_TU_TRACESON | `{LU}.TU.TracesOn` | bool | Диспетчер | Команда: включить трассировку |
| LU_TU_TRACESOFF | `{LU}.TU.TracesOff` | bool | Диспетчер | Команда: выключить трассировку |
| LU_TRACEINTERVAL | `{LU}.State.TraceInterval` | int (с) | ИМ | Интервал трассировки |
| LU_TRACETTL | `{LU}.State.TracesTTL` | int (с) | ИМ | TTL трассировки |
| LU_TRACESAVE | `{LU}.State.TracesSave` | bool | ИМ | Сохранять историю без TTL |
| LU_SETTIMESHIFT | `{LU}.TU.SetTimeShift` | bool | Диспетчер | Команда: перенос времени |
| LU_ARMT_PUMPPLAN | `{LU}.TI.ARMTPumpPlan` | JSON | Внешний |  | | Тег (кратко) | Путь | Тип | Источник | Описание | LU_KM | `{LU}.TI.KM` | float[] | ИМ | Километровые отметки конфигурации | LU_HEIGHT | `{LU}.TI.Height` | float[] | ИМ | Высоты конфигурации | LU_PMAXDEFAULT | `{LU}.TI.PmaxDefault` | float[] (МПа) | ИМ | Предельно допустимое давление по км | LU_PRESSMANUALLIMIT | `{LU}.TI.PressManualLimit` | string | Оператор | Ручные ограничения несущей | LU_CARRIERDEF | `{LU}.TI.CarrierDef` | float[] (МПа) | Расчёт | Несущая давления | LU_CARRIERHEADDEF | `{LU}.TI.CarrierHeadDef` | float[] (м) | Расчёт | Несущая напора | LU_CARRIER_DATA1 | `{LU}.TI.CarrierData1` | float[] | ИМ/Расчёт | Данные несущей 1 | LU_CARRIER_DATA2 | `{LU}.TI.CarrierData2` | float[] | ИМ/Расчёт | Данные несущей 2 | LU_CONTROL | `{LU}.State.Control` | int (0/1/2) | Расчёт/Команда | Состояние контроля | LU_STATION | `{LU}.State.Station` | bool | Расчёт | Стационарность ТУ | LU_COUNTERKIP | `{LU}.State.CounterKIP` | int | Расчёт | Число активных датчиков | LU_LIMITKIP | `{LU}.State.LimitKIP` | int | ИМ | Лимит датчиков на связи | LU_COUNTKIPNOSTATION | `{LU}.State.CountKIPNoStation` | int | ИМ | Порог нестационарных | LU_TIMEINTSETSTATION | `{LU}.State.TimeIntSetStation` | int (с) | ИМ | Время установки стационарности | LU_AUTOCONTROLON | `{LU}.State.AutoControlOn` | bool | Расчёт/Команда | Флаг автопостановки | LU_CONTROLAUTOTIMELEFT | `{LU}.State.ControlAutoTimeLeft` | int | Расчёт | Таймер автопостановки | LU_CONTROLAUTOTIMEOUT | `{LU}.State.ControlAutoTimeOut` | int (с) | ИМ | Время автопостановки | LU_INDICATORCONTROL | `{LU}.State.IndicatorControl` | int (0–5) | Расчёт | Индикатор контроля | LU_INDICATORLINK | `{LU}.State.IndicatorLink` | int (0–2) | Расчёт | Индикатор связи | LU_ALMKIPALLLINK | `{LU}.Alm.AlmKIPAllLink` | bool | Расчёт | Аларм: нет связи со всеми | LU_ALMKIPCOUNTLINK | `{LU}.Alm.AlmKIPCountLink` | bool | Расчёт | Аларм: связь с частью | LU_ALMPRESSDEV | `{LU}.Alm.AlmPressDev` | bool | Расчёт | Аларм: отклонение по смежным | LU_ALMDEVHEADCARRIER | `{LU}.Alm.AlmDevHeadCarrier` | bool | Расчёт | Аларм: напор выше несущей | LU_ALMPRESSRATELIMIT | `{LU}.Alm.AlmRateLimitPress` | bool | Расчёт | Аларм: превышение скорости | LU_ALMGRAVITY | `{LU}.Alm.AlmGravity` | bool | Расчёт | Аларм: самотек | LU_ALMGRAVITYPOSSIBLE | `{LU}.Alm.AlmGravityPossible` | bool | Расчёт | Аларм: риск самотека | LU_ALMDEVQMOM | `{LU}.Alm.AlmDevQmom` | bool | Расчёт | Аларм: дебаланс (мгновенный) | LU_ALMDEVQAVG | `{LU}.Alm.AlmDevQavg` | bool | Расчёт | Аларм: дебаланс (средний) | LU_ALMDEVQAVGSTATION | `{LU}.Alm.AlmDevQavgStation` | bool | Расчёт | Аларм: дебаланс (стационарный) | LU_ALMCARRIERONUSER | `{LU}.Alm.AlmCarrierOnUser` | bool | Расчёт | Аларм: изменение несущей пользователем | LU_DIFFQMOM | `{LU}.TI.DiffQmom` | float (м³/ч) | Расчёт | Мгновенный дебаланс | LU_DIFFQAVG | `{LU}.TI.DiffQavg` | float (м³/ч) | Расчёт | Средний дебаланс | LU_DIFFQAVGSTATION | `{LU}.TI.DiffQavgStation` | float (м³/ч) | Расчёт | Стационарный дебаланс | LU_DIFFQMOMLIMITMAX | `{LU}.TI.DiffQmomLimitMax` | float | ИМ | Верхний лимит дебаланса | LU_DIFFQMOMLIMITMIN | `{LU}.TI.DiffQmomLimitMin` | float | ИМ | Нижний лимит дебаланса | LU_GRAVITYSEGS | `{LU}.TI.GravitySegs` | string[] | Расчёт | Самотечные участки | LU_GRAVITYSEGSREG | `{LU}.TI.GravitySegsReg` | string[] | Расчёт | Слепок самотеков при постановке | LU_PASSPOINTS | `{LU}.TI.PassPoints` | float | Расчёт | Перевальные точки | LU_PASSPOINTSPOSSIBLE | `{LU}.TI.PassPointsPossible` | float | Расчёт | Возможные перевальные точки | LU_GRAVITYPOSSIBLE | `{LU}.TI.GravityPossible` | float (м) | ИМ | Запас для прогноза самотека | LU_RODISTRIB | `{LU}.TI.RoDistrib` | float[] | Расчёт | Распределение плотности | LU_RODISTRIBMANUAL | `{LU}.TI.RoDistribManual` | string | Оператор | Ручное распределение плотности | LU_DENSDEF | `{LU}.TI.DensDef` | float (кг/м³) | ИМ | Плотность по умолчанию | LU_DENSLIMIT | `{LU}.TI.DensLimit` | float (кг/м³) | ИМ | Порог формирования партии | LU_DENSTIME | `{LU}.TI.DensTime` | int (с) | ИМ | Интервал перерасчёта | LU_PRESSRATELIMIT | `{LU}.TI.PressRateLimit` | float (МПа/мин) | ИМ | Порог скорости | LU_PRESSRATEKIPLIMIT | `{LU}.TI.PressRateKiplimit` | int | ИМ | Мин. число датчиков для аларма | LU_PRESSRATEALGORITHM | `{LU}.TI.PressRateAlgorithm` | int (1/2) | ИМ | Алгоритм расчёта скорости | LU_PRESSRATEKIPINTERVAL | `{LU}.TI.PressRateKIPInterval` | int (с) | ИМ | Интервал МНК | LU_PRESSRATEHISTORYMAXCOUNT | `{LU}.TI.PressRateHistoryMaxCount` | int | ИМ | Макс. точек истории | LU_UNIFIED_PRESSDELTARANGEMAX | `{LU}.TI.UnifiedPressDeltaRangeMax` | float | Оператор | Унифицированная дельта (верх) | LU_UNIFIED_PRESSDELTARANGEMIN | `{LU}.TI.UnifiedPressDeltaRangeMin` | float | Оператор | Унифицированная дельта (низ) | LU_UNIFIED_QVMOMDELTARANGEMAX | `{LU}.TI.UnifiedQVmomDeltaRangeMax` | float | Оператор | Унифицированная дельта расхода (верх) | LU_UNIFIED_QVMOMDELTARANGEMIN | `{LU}.TI.UnifiedQVmomDeltaRangeMin` | float | Оператор | Унифицированная дельта расхода (низ) | LU_UNIFIED_PRESSDELTASCHEDULERANGEMAX | `{LU}.TI.UnifiedPressDeltaScheduleRangeMax` | float | Оператор | Унифицированная дельта плана (верх) | LU_UNIFIED_PRESSDELTASCHEDULERANGEMIN | `{LU}.TI.UnifiedPressDeltaScheduleRangeMin` | float | Оператор | Унифицированная дельта плана (низ) | LU_TU_SETCONTROLON | `{LU}.TU.SetControlOn` | bool | Диспетчер | Команда: поставить на контроль | LU_TU_SETCONTROLOFF | `{LU}.TU.SetControlOff` | bool | Диспетчер | Команда: снять с контроля | LU_TU_TRANSITIONCONTROLON | `{LU}.TU.TransitionControlOn` | bool | Диспетчер | Команда: режим перехода | LU_TU_SETAUTOCONTROLON | `{LU}.TU.SetAutoControlOn` | bool | Диспетчер | Команда: включить автопостановку | LU_TU_SETAUTOCONTROLOFF | `{LU}.TU.SetAutoControlOff` | bool | Диспетчер | Команда: выключить автопостановку | LU_TU_SETAUTOCONTROLCANCEL | `{LU}.TU.SetAutoControlCancel` | bool | Диспетчер | Команда: отменить автопостановку | LU_TU_SETAUTOCONTROLRESET | `{LU}.TU.SetAutoControlReset` | bool | Диспетчер | Команда: сбросить таймер | LU_TU_TRACESON | `{LU}.TU.TracesOn` | bool | Диспетчер | Команда: включить трассировку | LU_TU_TRACESOFF | `{LU}.TU.TracesOff` | bool | Диспетчер | Команда: выключить трассировку | LU_TRACEINTERVAL | `{LU}.State.TraceInterval` | int (с) | ИМ | Интервал трассировки | LU_TRACETTL | `{LU}.State.TracesTTL` | int (с) | ИМ | TTL трассировки | LU_TRACESAVE | `{LU}.State.TracesSave` | bool | ИМ | Сохранять историю без TTL | LU_SETTIMESHIFT | `{LU}.TU.SetTimeShift` | bool | Диспетчер | Команда: перенос времени | LU_ARMT_PUMPPLAN | `{LU}.TI.ARMTPumpPlan` | JSON | Внешний |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Тег (кратко) | Путь | Тип | Источник | Описание |
| LU_KM | `{LU}.TI.KM` | float[] | ИМ | Километровые отметки конфигурации |
| LU_HEIGHT | `{LU}.TI.Height` | float[] | ИМ | Высоты конфигурации |
| LU_PMAXDEFAULT | `{LU}.TI.PmaxDefault` | float[] (МПа) | ИМ | Предельно допустимое давление по км |
| LU_PRESSMANUALLIMIT | `{LU}.TI.PressManualLimit` | string | Оператор | Ручные ограничения несущей |
| LU_CARRIERDEF | `{LU}.TI.CarrierDef` | float[] (МПа) | Расчёт | Несущая давления |
| LU_CARRIERHEADDEF | `{LU}.TI.CarrierHeadDef` | float[] (м) | Расчёт | Несущая напора |
| LU_CARRIER_DATA1 | `{LU}.TI.CarrierData1` | float[] | ИМ/Расчёт | Данные несущей 1 |
| LU_CARRIER_DATA2 | `{LU}.TI.CarrierData2` | float[] | ИМ/Расчёт | Данные несущей 2 |
| LU_CONTROL | `{LU}.State.Control` | int (0/1/2) | Расчёт/Команда | Состояние контроля |
| LU_STATION | `{LU}.State.Station` | bool | Расчёт | Стационарность ТУ |
| LU_COUNTERKIP | `{LU}.State.CounterKIP` | int | Расчёт | Число активных датчиков |
| LU_LIMITKIP | `{LU}.State.LimitKIP` | int | ИМ | Лимит датчиков на связи |
| LU_COUNTKIPNOSTATION | `{LU}.State.CountKIPNoStation` | int | ИМ | Порог нестационарных |
| LU_TIMEINTSETSTATION | `{LU}.State.TimeIntSetStation` | int (с) | ИМ | Время установки стационарности |
| LU_AUTOCONTROLON | `{LU}.State.AutoControlOn` | bool | Расчёт/Команда | Флаг автопостановки |
| LU_CONTROLAUTOTIMELEFT | `{LU}.State.ControlAutoTimeLeft` | int | Расчёт | Таймер автопостановки |
| LU_CONTROLAUTOTIMEOUT | `{LU}.State.ControlAutoTimeOut` | int (с) | ИМ | Время автопостановки |
| LU_INDICATORCONTROL | `{LU}.State.IndicatorControl` | int (0–5) | Расчёт | Индикатор контроля |
| LU_INDICATORLINK | `{LU}.State.IndicatorLink` | int (0–2) | Расчёт | Индикатор связи |
| LU_ALMKIPALLLINK | `{LU}.Alm.AlmKIPAllLink` | bool | Расчёт | Аларм: нет связи со всеми |
| LU_ALMKIPCOUNTLINK | `{LU}.Alm.AlmKIPCountLink` | bool | Расчёт | Аларм: связь с частью |
| LU_ALMPRESSDEV | `{LU}.Alm.AlmPressDev` | bool | Расчёт | Аларм: отклонение по смежным |
| LU_ALMDEVHEADCARRIER | `{LU}.Alm.AlmDevHeadCarrier` | bool | Расчёт | Аларм: напор выше несущей |
| LU_ALMPRESSRATELIMIT | `{LU}.Alm.AlmRateLimitPress` | bool | Расчёт | Аларм: превышение скорости |
| LU_ALMGRAVITY | `{LU}.Alm.AlmGravity` | bool | Расчёт | Аларм: самотек |
| LU_ALMGRAVITYPOSSIBLE | `{LU}.Alm.AlmGravityPossible` | bool | Расчёт | Аларм: риск самотека |
| LU_ALMDEVQMOM | `{LU}.Alm.AlmDevQmom` | bool | Расчёт | Аларм: дебаланс (мгновенный) |
| LU_ALMDEVQAVG | `{LU}.Alm.AlmDevQavg` | bool | Расчёт | Аларм: дебаланс (средний) |
| LU_ALMDEVQAVGSTATION | `{LU}.Alm.AlmDevQavgStation` | bool | Расчёт | Аларм: дебаланс (стационарный) |
| LU_ALMCARRIERONUSER | `{LU}.Alm.AlmCarrierOnUser` | bool | Расчёт | Аларм: изменение несущей пользователем |
| LU_DIFFQMOM | `{LU}.TI.DiffQmom` | float (м³/ч) | Расчёт | Мгновенный дебаланс |
| LU_DIFFQAVG | `{LU}.TI.DiffQavg` | float (м³/ч) | Расчёт | Средний дебаланс |
| LU_DIFFQAVGSTATION | `{LU}.TI.DiffQavgStation` | float (м³/ч) | Расчёт | Стационарный дебаланс |
| LU_DIFFQMOMLIMITMAX | `{LU}.TI.DiffQmomLimitMax` | float | ИМ | Верхний лимит дебаланса |
| LU_DIFFQMOMLIMITMIN | `{LU}.TI.DiffQmomLimitMin` | float | ИМ | Нижний лимит дебаланса |
| LU_GRAVITYSEGS | `{LU}.TI.GravitySegs` | string[] | Расчёт | Самотечные участки |
| LU_GRAVITYSEGSREG | `{LU}.TI.GravitySegsReg` | string[] | Расчёт | Слепок самотеков при постановке |
| LU_PASSPOINTS | `{LU}.TI.PassPoints` | float | Расчёт | Перевальные точки |
| LU_PASSPOINTSPOSSIBLE | `{LU}.TI.PassPointsPossible` | float | Расчёт | Возможные перевальные точки |
| LU_GRAVITYPOSSIBLE | `{LU}.TI.GravityPossible` | float (м) | ИМ | Запас для прогноза самотека |
| LU_RODISTRIB | `{LU}.TI.RoDistrib` | float[] | Расчёт | Распределение плотности |
| LU_RODISTRIBMANUAL | `{LU}.TI.RoDistribManual` | string | Оператор | Ручное распределение плотности |
| LU_DENSDEF | `{LU}.TI.DensDef` | float (кг/м³) | ИМ | Плотность по умолчанию |
| LU_DENSLIMIT | `{LU}.TI.DensLimit` | float (кг/м³) | ИМ | Порог формирования партии |
| LU_DENSTIME | `{LU}.TI.DensTime` | int (с) | ИМ | Интервал перерасчёта |
| LU_PRESSRATELIMIT | `{LU}.TI.PressRateLimit` | float (МПа/мин) | ИМ | Порог скорости |
| LU_PRESSRATEKIPLIMIT | `{LU}.TI.PressRateKiplimit` | int | ИМ | Мин. число датчиков для аларма |
| LU_PRESSRATEALGORITHM | `{LU}.TI.PressRateAlgorithm` | int (1/2) | ИМ | Алгоритм расчёта скорости |
| LU_PRESSRATEKIPINTERVAL | `{LU}.TI.PressRateKIPInterval` | int (с) | ИМ | Интервал МНК |
| LU_PRESSRATEHISTORYMAXCOUNT | `{LU}.TI.PressRateHistoryMaxCount` | int | ИМ | Макс. точек истории |
| LU_UNIFIED_PRESSDELTARANGEMAX | `{LU}.TI.UnifiedPressDeltaRangeMax` | float | Оператор | Унифицированная дельта (верх) |
| LU_UNIFIED_PRESSDELTARANGEMIN | `{LU}.TI.UnifiedPressDeltaRangeMin` | float | Оператор | Унифицированная дельта (низ) |
| LU_UNIFIED_QVMOMDELTARANGEMAX | `{LU}.TI.UnifiedQVmomDeltaRangeMax` | float | Оператор | Унифицированная дельта расхода (верх) |
| LU_UNIFIED_QVMOMDELTARANGEMIN | `{LU}.TI.UnifiedQVmomDeltaRangeMin` | float | Оператор | Унифицированная дельта расхода (низ) |
| LU_UNIFIED_PRESSDELTASCHEDULERANGEMAX | `{LU}.TI.UnifiedPressDeltaScheduleRangeMax` | float | Оператор | Унифицированная дельта плана (верх) |
| LU_UNIFIED_PRESSDELTASCHEDULERANGEMIN | `{LU}.TI.UnifiedPressDeltaScheduleRangeMin` | float | Оператор | Унифицированная дельта плана (низ) |
| LU_TU_SETCONTROLON | `{LU}.TU.SetControlOn` | bool | Диспетчер | Команда: поставить на контроль |
| LU_TU_SETCONTROLOFF | `{LU}.TU.SetControlOff` | bool | Диспетчер | Команда: снять с контроля |
| LU_TU_TRANSITIONCONTROLON | `{LU}.TU.TransitionControlOn` | bool | Диспетчер | Команда: режим перехода |
| LU_TU_SETAUTOCONTROLON | `{LU}.TU.SetAutoControlOn` | bool | Диспетчер | Команда: включить автопостановку |
| LU_TU_SETAUTOCONTROLOFF | `{LU}.TU.SetAutoControlOff` | bool | Диспетчер | Команда: выключить автопостановку |
| LU_TU_SETAUTOCONTROLCANCEL | `{LU}.TU.SetAutoControlCancel` | bool | Диспетчер | Команда: отменить автопостановку |
| LU_TU_SETAUTOCONTROLRESET | `{LU}.TU.SetAutoControlReset` | bool | Диспетчер | Команда: сбросить таймер |
| LU_TU_TRACESON | `{LU}.TU.TracesOn` | bool | Диспетчер | Команда: включить трассировку |
| LU_TU_TRACESOFF | `{LU}.TU.TracesOff` | bool | Диспетчер | Команда: выключить трассировку |
| LU_TRACEINTERVAL | `{LU}.State.TraceInterval` | int (с) | ИМ | Интервал трассировки |
| LU_TRACETTL | `{LU}.State.TracesTTL` | int (с) | ИМ | TTL трассировки |
| LU_TRACESAVE | `{LU}.State.TracesSave` | bool | ИМ | Сохранять историю без TTL |
| LU_SETTIMESHIFT | `{LU}.TU.SetTimeShift` | bool | Диспетчер | Команда: перенос времени |
| LU_ARMT_PUMPPLAN | `{LU}.TI.ARMTPumpPlan` | JSON | Внешний |  |


| | Тег (кратко) | Путь | Тип | Источник | Описание |
| --- | --- | --- | --- | --- |
| KIP_PRESS | `{KIP}.TI.Press` | float (МПа) | СДКУ | Давление (сырой сигнал) |
| KIP_HEAD | `{KIP}.TI.Head` | float (м) | Расчёт | Пьезометрический напор |
| KIP_HEIGHT | `{KIP}.TI.Height` | float (м) | Расчёт | Высота датчика (интерполяция) |
| KIP_HEIGHTCORRECTION | `{KIP}.TI.HeightCorrection` | float (м) | Оператор | Ручная поправка высоты |
| KIP_KM | `{KIP}.TI.Km` | float | ИМ | Километровая отметка датчика |
| KIP_RO | `{KIP}.TI.Ro` | float (кг/м³) | СДКУ/Расчёт | Плотность жидкости |
| KIP_ROSCHEDULE | `{KIP}.TI.RoSchedule` | float (кг/м³) | Расчёт | Плановая плотность |
| KIP_STATION | `{KIP}.State.Station` | bool | Расчёт | Стационарность датчика |
| KIP_PRESSSTATIONARYMODE | `{KIP}.TI.PressStationaryMode` | float (МПа) | Расчёт | Эталонное давление для стационарности |
| KIP_DEVMAXSTATION | `{KIP}.TI.DevMaxStation` | float (МПа) | ИМ | Верхний порог стационарности |
| KIP_DEVMINSTATION | `{KIP}.TI.DevMinStation` | float (МПа) | ИМ | Нижний порог стационарности |
| KIP_PRESSSTATION | `{KIP}.TI.PressStation` | float (МПа) | Расчёт | Базовое давление (зафиксировано при Control=1) |
| KIP_PRESSRANGEMAX | `{KIP}.TI.PressRangeMax` | float (МПа) | Расчёт | Верхняя граница диапазона |
| KIP_PRESSRANGEMIN | `{KIP}.TI.PressRangeMin` | float (МПа) | Расчёт | Нижняя граница диапазона |
| KIP_PRESSDELTARANGEMAX | `{KIP}.TI.PressDeltaRangeMax` | float (МПа) | ИМ/Унификация | Дельта верхней границы |
| KIP_PRESSDELTARANGEMIN | `{KIP}.TI.PressDeltaRangeMin` | float (МПа) | ИМ/Унификация | Дельта нижней границы |
| KIP_PRESSDELTA | `{KIP}.TI.PressDelta` | float (МПа) | Расчёт | Отклонение давления от базового |
| KIP_HEADDELTA | `{KIP}.TI.HeadDelta` | float (м) | Расчёт | Отклонение напора от базового |
| KIP_HEADSTATION | `{KIP}.TI.HeadStation` | float (м) | Расчёт | Базовый напор (зафиксирован) |
| KIP_HEADRANGEMAX | `{KIP}.TI.HeadRangeMax` | float (м) | Расчёт | Верхняя граница диапазона напора |
| KIP_HEADRANGEMIN | `{KIP}.TI.HeadRangeMin` | float (м) | Расчёт | Нижняя граница диапазона напора |
| KIP_PRESSRANGEALARM | `{KIP}.Alm.PressRangeAlarm` | bool | Расчёт | Аларм: давление вне диапазона (KipPressRangeAlg) |
| KIP_ALMDEVMAXRANGE | `{KIP}.Alm.AlmDevMaxRange` | bool | Расчёт | Аларм: давление выше верхней границы |
| KIP_ALMDEVMINRANGE | `{KIP}.Alm.AlmDevMinRange` | bool | Расчёт | Аларм: давление ниже нижней границы |
| KIP_PRESSRATE | `{KIP}.TI.PressRate` | float (МПа/мин) | Расчёт | Скорость изменения давления |
| KIP_PRESSRATETAG | `{KIP}.TI.PressRateTag` | float | Расчёт | Тег скорости (внутренний) |
| KIP_PRESSRATETAGMIN | `{KIP}.TI.PressRateTagMin` | float | ИМ | Мин. порог скорости |
| KIP_PRESSRATETAGMAX | `{KIP}.TI.PressRateTagMax` | float | ИМ | Макс. порог скорости |
| KIP_PRESSRATETAGALARM | `{KIP}.Alm.PressRateTagAlarm` | bool | Расчёт | Аларм скорости на датчике |
| KIP_VISIBLE | `{KIP}.State.Visible` | bool | Расчёт | Видимость датчика |
| KIP_DISABLE | `{KIP}.State.Disable` | bool | Оператор/Расчёт | Отключение датчика |
| KIP_MANUAL | `{KIP}.State.Manual` | bool | Оператор | Ручной режим |
| KIP_ALMFAILON | `{KIP}.Alm.AlmFailOn` | bool | Расчёт | Аларм достоверности (противоречие Disable/invalid) |
| KIP_ALMGRAVITYPOSSIBLE | `{KIP}.Alm.AlmGravityPossible` | bool | Расчёт | Аларм: напор на датчике близок к профилю |
| KIP_LIMITMAXPRESSCSPA | `{KIP}.TI.LimitMaxPressCSPA` | float (МПа) | ИМ | Уставка ЦСПА (давление) |
| KIP_ALMLIMITCSPA | `{KIP}.Alm.AlmLimitCSPA` | bool | Расчёт | Аларм: превышение уставки ЦСПА |
| KIP_HEADLIMITMAXCSPA | `{KIP}.TI.HeadLimitMaxCSPA` | float (м) | Расчёт | Уставка ЦСПА (напор, для визуализации) |
| KIP_PRESSSCHEDULE | `{KIP}.TI.PressSchedule` | float (МПа) | Расчёт | Плановое давление |
| KIP_HEADSCHEDULE | `{KIP}.TI.HeadSchedule` | float (м) | Расчёт | Плановый напор |
| KIP_PRESSDELTASCHEDULERANGEMAX | `{KIP}.TI.PressDeltaScheduleRangeMax` | float | ИМ/Унификация | Дельта плана (верх) |
| KIP_PRESSDELTASCHEDULERANGEMIN | `{KIP}.TI.PressDeltaScheduleRangeMin` | float | ИМ/Унификация | Дельта плана (низ) |
| KIP_HEADDELTASCHEDULERANGEMAX | `{KIP}.TI.HeadDeltaScheduleRangeMax` | float | ИМ/Унификация | Дельта плана напора (верх) |
| KIP_HEADDELTASCHEDULERANGEMIN | `{KIP}.TI.HeadDeltaScheduleRangeMin` | float | ИМ/Унификация | Дельта плана напора (низ) |
| KIP_TRACESPRESS | `{KIP}.TI.TracesPress` | [[float, ts]] | Расчёт | Следы давления |
| KIP_TRACESHEAD | `{KIP}.TI.TracesHead` | [[float, ts]] | Расчёт | Следы напора |
| KIP_REMONTSTATUS | `{KIP}.State.RemontStatus` | int | СДКУ | Статус ремонта (0 = норма, ≠0 = ремонт) |
| KIP_TU_SETON | `{KIP}.TU.SetOn` | bool | Диспетчер | Команда: включить датчик |
| KIP_TU_SETOFF | `{KIP}.TU.SetOff` | bool | Диспетчер | Команда: отключить датчик | | Тег (кратко) | Путь | Тип | Источник | Описание | KIP_PRESS | `{KIP}.TI.Press` | float (МПа) | СДКУ | Давление (сырой сигнал) | KIP_HEAD | `{KIP}.TI.Head` | float (м) | Расчёт | Пьезометрический напор | KIP_HEIGHT | `{KIP}.TI.Height` | float (м) | Расчёт | Высота датчика (интерполяция) | KIP_HEIGHTCORRECTION | `{KIP}.TI.HeightCorrection` | float (м) | Оператор | Ручная поправка высоты | KIP_KM | `{KIP}.TI.Km` | float | ИМ | Километровая отметка датчика | KIP_RO | `{KIP}.TI.Ro` | float (кг/м³) | СДКУ/Расчёт | Плотность жидкости | KIP_ROSCHEDULE | `{KIP}.TI.RoSchedule` | float (кг/м³) | Расчёт | Плановая плотность | KIP_STATION | `{KIP}.State.Station` | bool | Расчёт | Стационарность датчика | KIP_PRESSSTATIONARYMODE | `{KIP}.TI.PressStationaryMode` | float (МПа) | Расчёт | Эталонное давление для стационарности | KIP_DEVMAXSTATION | `{KIP}.TI.DevMaxStation` | float (МПа) | ИМ | Верхний порог стационарности | KIP_DEVMINSTATION | `{KIP}.TI.DevMinStation` | float (МПа) | ИМ | Нижний порог стационарности | KIP_PRESSSTATION | `{KIP}.TI.PressStation` | float (МПа) | Расчёт | Базовое давление (зафиксировано при Control=1) | KIP_PRESSRANGEMAX | `{KIP}.TI.PressRangeMax` | float (МПа) | Расчёт | Верхняя граница диапазона | KIP_PRESSRANGEMIN | `{KIP}.TI.PressRangeMin` | float (МПа) | Расчёт | Нижняя граница диапазона | KIP_PRESSDELTARANGEMAX | `{KIP}.TI.PressDeltaRangeMax` | float (МПа) | ИМ/Унификация | Дельта верхней границы | KIP_PRESSDELTARANGEMIN | `{KIP}.TI.PressDeltaRangeMin` | float (МПа) | ИМ/Унификация | Дельта нижней границы | KIP_PRESSDELTA | `{KIP}.TI.PressDelta` | float (МПа) | Расчёт | Отклонение давления от базового | KIP_HEADDELTA | `{KIP}.TI.HeadDelta` | float (м) | Расчёт | Отклонение напора от базового | KIP_HEADSTATION | `{KIP}.TI.HeadStation` | float (м) | Расчёт | Базовый напор (зафиксирован) | KIP_HEADRANGEMAX | `{KIP}.TI.HeadRangeMax` | float (м) | Расчёт | Верхняя граница диапазона напора | KIP_HEADRANGEMIN | `{KIP}.TI.HeadRangeMin` | float (м) | Расчёт | Нижняя граница диапазона напора | KIP_PRESSRANGEALARM | `{KIP}.Alm.PressRangeAlarm` | bool | Расчёт | Аларм: давление вне диапазона (KipPressRangeAlg) | KIP_ALMDEVMAXRANGE | `{KIP}.Alm.AlmDevMaxRange` | bool | Расчёт | Аларм: давление выше верхней границы | KIP_ALMDEVMINRANGE | `{KIP}.Alm.AlmDevMinRange` | bool | Расчёт | Аларм: давление ниже нижней границы | KIP_PRESSRATE | `{KIP}.TI.PressRate` | float (МПа/мин) | Расчёт | Скорость изменения давления | KIP_PRESSRATETAG | `{KIP}.TI.PressRateTag` | float | Расчёт | Тег скорости (внутренний) | KIP_PRESSRATETAGMIN | `{KIP}.TI.PressRateTagMin` | float | ИМ | Мин. порог скорости | KIP_PRESSRATETAGMAX | `{KIP}.TI.PressRateTagMax` | float | ИМ | Макс. порог скорости | KIP_PRESSRATETAGALARM | `{KIP}.Alm.PressRateTagAlarm` | bool | Расчёт | Аларм скорости на датчике | KIP_VISIBLE | `{KIP}.State.Visible` | bool | Расчёт | Видимость датчика | KIP_DISABLE | `{KIP}.State.Disable` | bool | Оператор/Расчёт | Отключение датчика | KIP_MANUAL | `{KIP}.State.Manual` | bool | Оператор | Ручной режим | KIP_ALMFAILON | `{KIP}.Alm.AlmFailOn` | bool | Расчёт | Аларм достоверности (противоречие Disable/invalid) | KIP_ALMGRAVITYPOSSIBLE | `{KIP}.Alm.AlmGravityPossible` | bool | Расчёт | Аларм: напор на датчике близок к профилю | KIP_LIMITMAXPRESSCSPA | `{KIP}.TI.LimitMaxPressCSPA` | float (МПа) | ИМ | Уставка ЦСПА (давление) | KIP_ALMLIMITCSPA | `{KIP}.Alm.AlmLimitCSPA` | bool | Расчёт | Аларм: превышение уставки ЦСПА | KIP_HEADLIMITMAXCSPA | `{KIP}.TI.HeadLimitMaxCSPA` | float (м) | Расчёт | Уставка ЦСПА (напор, для визуализации) | KIP_PRESSSCHEDULE | `{KIP}.TI.PressSchedule` | float (МПа) | Расчёт | Плановое давление | KIP_HEADSCHEDULE | `{KIP}.TI.HeadSchedule` | float (м) | Расчёт | Плановый напор | KIP_PRESSDELTASCHEDULERANGEMAX | `{KIP}.TI.PressDeltaScheduleRangeMax` | float | ИМ/Унификация | Дельта плана (верх) | KIP_PRESSDELTASCHEDULERANGEMIN | `{KIP}.TI.PressDeltaScheduleRangeMin` | float | ИМ/Унификация | Дельта плана (низ) | KIP_HEADDELTASCHEDULERANGEMAX | `{KIP}.TI.HeadDeltaScheduleRangeMax` | float | ИМ/Унификация | Дельта плана напора (верх) | KIP_HEADDELTASCHEDULERANGEMIN | `{KIP}.TI.HeadDeltaScheduleRangeMin` | float | ИМ/Унификация | Дельта плана напора (низ) | KIP_TRACESPRESS | `{KIP}.TI.TracesPress` | [[float, ts]] | Расчёт | Следы давления | KIP_TRACESHEAD | `{KIP}.TI.TracesHead` | [[float, ts]] | Расчёт | Следы напора | KIP_REMONTSTATUS | `{KIP}.State.RemontStatus` | int | СДКУ | Статус ремонта (0 = норма, ≠0 = ремонт) | KIP_TU_SETON | `{KIP}.TU.SetOn` | bool | Диспетчер | Команда: включить датчик | KIP_TU_SETOFF | `{KIP}.TU.SetOff` | bool | Диспетчер | Команда: отключить датчик |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Тег (кратко) | Путь | Тип | Источник | Описание |
| KIP_PRESS | `{KIP}.TI.Press` | float (МПа) | СДКУ | Давление (сырой сигнал) |
| KIP_HEAD | `{KIP}.TI.Head` | float (м) | Расчёт | Пьезометрический напор |
| KIP_HEIGHT | `{KIP}.TI.Height` | float (м) | Расчёт | Высота датчика (интерполяция) |
| KIP_HEIGHTCORRECTION | `{KIP}.TI.HeightCorrection` | float (м) | Оператор | Ручная поправка высоты |
| KIP_KM | `{KIP}.TI.Km` | float | ИМ | Километровая отметка датчика |
| KIP_RO | `{KIP}.TI.Ro` | float (кг/м³) | СДКУ/Расчёт | Плотность жидкости |
| KIP_ROSCHEDULE | `{KIP}.TI.RoSchedule` | float (кг/м³) | Расчёт | Плановая плотность |
| KIP_STATION | `{KIP}.State.Station` | bool | Расчёт | Стационарность датчика |
| KIP_PRESSSTATIONARYMODE | `{KIP}.TI.PressStationaryMode` | float (МПа) | Расчёт | Эталонное давление для стационарности |
| KIP_DEVMAXSTATION | `{KIP}.TI.DevMaxStation` | float (МПа) | ИМ | Верхний порог стационарности |
| KIP_DEVMINSTATION | `{KIP}.TI.DevMinStation` | float (МПа) | ИМ | Нижний порог стационарности |
| KIP_PRESSSTATION | `{KIP}.TI.PressStation` | float (МПа) | Расчёт | Базовое давление (зафиксировано при Control=1) |
| KIP_PRESSRANGEMAX | `{KIP}.TI.PressRangeMax` | float (МПа) | Расчёт | Верхняя граница диапазона |
| KIP_PRESSRANGEMIN | `{KIP}.TI.PressRangeMin` | float (МПа) | Расчёт | Нижняя граница диапазона |
| KIP_PRESSDELTARANGEMAX | `{KIP}.TI.PressDeltaRangeMax` | float (МПа) | ИМ/Унификация | Дельта верхней границы |
| KIP_PRESSDELTARANGEMIN | `{KIP}.TI.PressDeltaRangeMin` | float (МПа) | ИМ/Унификация | Дельта нижней границы |
| KIP_PRESSDELTA | `{KIP}.TI.PressDelta` | float (МПа) | Расчёт | Отклонение давления от базового |
| KIP_HEADDELTA | `{KIP}.TI.HeadDelta` | float (м) | Расчёт | Отклонение напора от базового |
| KIP_HEADSTATION | `{KIP}.TI.HeadStation` | float (м) | Расчёт | Базовый напор (зафиксирован) |
| KIP_HEADRANGEMAX | `{KIP}.TI.HeadRangeMax` | float (м) | Расчёт | Верхняя граница диапазона напора |
| KIP_HEADRANGEMIN | `{KIP}.TI.HeadRangeMin` | float (м) | Расчёт | Нижняя граница диапазона напора |
| KIP_PRESSRANGEALARM | `{KIP}.Alm.PressRangeAlarm` | bool | Расчёт | Аларм: давление вне диапазона (KipPressRangeAlg) |
| KIP_ALMDEVMAXRANGE | `{KIP}.Alm.AlmDevMaxRange` | bool | Расчёт | Аларм: давление выше верхней границы |
| KIP_ALMDEVMINRANGE | `{KIP}.Alm.AlmDevMinRange` | bool | Расчёт | Аларм: давление ниже нижней границы |
| KIP_PRESSRATE | `{KIP}.TI.PressRate` | float (МПа/мин) | Расчёт | Скорость изменения давления |
| KIP_PRESSRATETAG | `{KIP}.TI.PressRateTag` | float | Расчёт | Тег скорости (внутренний) |
| KIP_PRESSRATETAGMIN | `{KIP}.TI.PressRateTagMin` | float | ИМ | Мин. порог скорости |
| KIP_PRESSRATETAGMAX | `{KIP}.TI.PressRateTagMax` | float | ИМ | Макс. порог скорости |
| KIP_PRESSRATETAGALARM | `{KIP}.Alm.PressRateTagAlarm` | bool | Расчёт | Аларм скорости на датчике |
| KIP_VISIBLE | `{KIP}.State.Visible` | bool | Расчёт | Видимость датчика |
| KIP_DISABLE | `{KIP}.State.Disable` | bool | Оператор/Расчёт | Отключение датчика |
| KIP_MANUAL | `{KIP}.State.Manual` | bool | Оператор | Ручной режим |
| KIP_ALMFAILON | `{KIP}.Alm.AlmFailOn` | bool | Расчёт | Аларм достоверности (противоречие Disable/invalid) |
| KIP_ALMGRAVITYPOSSIBLE | `{KIP}.Alm.AlmGravityPossible` | bool | Расчёт | Аларм: напор на датчике близок к профилю |
| KIP_LIMITMAXPRESSCSPA | `{KIP}.TI.LimitMaxPressCSPA` | float (МПа) | ИМ | Уставка ЦСПА (давление) |
| KIP_ALMLIMITCSPA | `{KIP}.Alm.AlmLimitCSPA` | bool | Расчёт | Аларм: превышение уставки ЦСПА |
| KIP_HEADLIMITMAXCSPA | `{KIP}.TI.HeadLimitMaxCSPA` | float (м) | Расчёт | Уставка ЦСПА (напор, для визуализации) |
| KIP_PRESSSCHEDULE | `{KIP}.TI.PressSchedule` | float (МПа) | Расчёт | Плановое давление |
| KIP_HEADSCHEDULE | `{KIP}.TI.HeadSchedule` | float (м) | Расчёт | Плановый напор |
| KIP_PRESSDELTASCHEDULERANGEMAX | `{KIP}.TI.PressDeltaScheduleRangeMax` | float | ИМ/Унификация | Дельта плана (верх) |
| KIP_PRESSDELTASCHEDULERANGEMIN | `{KIP}.TI.PressDeltaScheduleRangeMin` | float | ИМ/Унификация | Дельта плана (низ) |
| KIP_HEADDELTASCHEDULERANGEMAX | `{KIP}.TI.HeadDeltaScheduleRangeMax` | float | ИМ/Унификация | Дельта плана напора (верх) |
| KIP_HEADDELTASCHEDULERANGEMIN | `{KIP}.TI.HeadDeltaScheduleRangeMin` | float | ИМ/Унификация | Дельта плана напора (низ) |
| KIP_TRACESPRESS | `{KIP}.TI.TracesPress` | [[float, ts]] | Расчёт | Следы давления |
| KIP_TRACESHEAD | `{KIP}.TI.TracesHead` | [[float, ts]] | Расчёт | Следы напора |
| KIP_REMONTSTATUS | `{KIP}.State.RemontStatus` | int | СДКУ | Статус ремонта (0 = норма, ≠0 = ремонт) |
| KIP_TU_SETON | `{KIP}.TU.SetOn` | bool | Диспетчер | Команда: включить датчик |
| KIP_TU_SETOFF | `{KIP}.TU.SetOff` | bool | Диспетчер | Команда: отключить датчик |


| | Тег (кратко) | Путь | Тип | Источник | Описание |
| --- | --- | --- | --- | --- |
| UR_QVMOM | `{UR}.TI.QVmom` | float (м³/ч) | СДКУ | Моментальный расход |
| UR_QVMOMMANUAL | `{UR}.TI.QVmomManual` | float (м³/ч) | Оператор | Ручной расход |
| UR_QVMOMSTATION | `{UR}.TI.QVmomStation` | float (м³/ч) | Расчёт | Базовый расход (зафиксирован) |
| UR_QVMOMDELTA | `{UR}.TI.QVmomDelta` | float (м³/ч) | Расчёт | Отклонение расхода |
| UR_QVMOMDELTARANGEMAX | `{UR}.TI.QVmomDeltaRangeMax` | float | ИМ/Унификация | Дельта расхода (верх) |
| UR_QVMOMDELTARANGEMIN | `{UR}.TI.QVmomDeltaRangeMin` | float | ИМ/Унификация | Дельта расхода (низ) |
| UR_ALMQVMOMRANGEMAX | `{UR}.Alm.AlmQVmomRangeMax` | bool | Расчёт | Аларм: расход выше границы |
| UR_ALMQVMOMRANGEMIN | `{UR}.Alm.AlmQVmomRangeMin` | bool | Расчёт | Аларм: расход ниже границы |
| UR_ALMQVMOMINVALID | `{UR}.Alm.AlmQVmomInvalid` | bool | Расчёт | Флаг невалидности расхода |
| UR_DISABLE | `{UR}.State.Disable` | bool | Оператор/Расчёт | Отключение расходомера |
| UR_MANUAL | `{UR}.State.Manual` | bool | Оператор | Ручной режим |
| UR_KM | `{UR}.TI.Km` | float | ИМ | Километровая отметка |
| UR_TRACESQVMOM | `{UR}.TI.TracesQVmom` | [[float, ts]] | Расчёт | Следы расхода |
| UR_REMONTSTATUS | `{UR}.State.RemontStatus` | int | СДКУ | Статус ремонта |
| UR_TU_SETON | `{UR}.TU.SetOn` | bool | Диспетчер | Команда: включить |
| UR_TU_SETOFF | `{UR}.TU.SetOff` | bool | Диспетчер | Команда: отключить |
| SGLU_VISIBLE | `{SGLU}.State.Visible` | bool | Расчёт | Видимость сегмента |
| SGLU_ACTIVITY | `{SGLU}.State.Activity` | bool | Расчёт | Активность сегмента |
| SGLU_CONTROLON | `{SGLU}.State.ControlOn` | bool | Расчёт | Сегмент на контроле |
| SGLU_PRIORITY | `{SGLU}.TI.Priority` | int | ИМ | Приоритет (0=подкачка, 1=лупинг) |
| SGLU_PARTGRZDV | `{SGLU}.TI.PartGRZDV` | string[] | ИМ | Список задвижек |
| SGLU_PARTUR | `{SGLU}.TI.PartUR` | string[] | ИМ | Список расходомеров |
| SGLU_PARTPLTM | `{SGLU}.TI.PartPLTM` | string[] | ИМ | Список плотномеров |
| SGLU_PARTKIP | `{SGLU}.TI.PartKIP` | string[] | ИМ | Список датчиков |
| SGLU_DIAMETER | `{SGLU}.TI.Diameter` | float (м) | ИМ | Диаметр трубы |
| SGLU_KM | `{SGLU}.TI.Km` | float | ИМ | Километровая отметка |
| GRZDV_STATUS | `{GRZDV}.Status` | int (0/1) | Расчёт | Состояние группы |
| GRZDV_TYPE | `{GRZDV}.TI.Type` | int (1/2) | ИМ | Тип: 1=OR, 2=AND |
| GRZDV_ACTIVITY | `{GRZDV}.Activity` | bool | Расчёт | Активность группы |
| GRZDV_PART | `{GRZDV}.TI.Part` | string[] | ИМ | Список ZDV в группе |
| ZDV_STATUS | `{ZDV}.Status` | int (0/2/3) | СДКУ | Состояние задвижки |
| ZDV_ACTIVITY | `{ZDV}.Activity` | bool | Расчёт | Активность задвижки |
| PLTM_RO | `{PLTM}.TI.Ro` | float (кг/м³) | СДКУ | Плотность |
| PLTM_ROMANUAL | `{PLTM}.TI.RoManual` | float (кг/м³) | Оператор | Ручная плотность |
| PLTM_ISMANUAL | `{PLTM}.State.IsManual` | bool | Оператор | Ручной режим |
| PLTM_DISABLE | `{PLTM}.State.Disable` | bool | Оператор/Расчёт | Отключение |
| PLTM_KM | `{PLTM}.TI.Km` | float | ИМ | Километровая отметка |
| PLTM_ALMROINVALID | `{PLTM}.Alm.AlmRoInvalid` | bool | Расчёт | Флаг невалидности плотности |
| PLTM_REMONTSTATUS | `{PLTM}.State.RemontStatus` | int | СДКУ | Статус ремонта |
| PLTM_TU_SETON | `{PLTM}.TU.SetOn` | bool | Диспетчер | Команда: включить |
| PLTM_TU_SETOFF | `{PLTM}.TU.SetOff` | bool | Диспетчер | Команда: отключить | | Тег (кратко) | Путь | Тип | Источник | Описание | UR_QVMOM | `{UR}.TI.QVmom` | float (м³/ч) | СДКУ | Моментальный расход | UR_QVMOMMANUAL | `{UR}.TI.QVmomManual` | float (м³/ч) | Оператор | Ручной расход | UR_QVMOMSTATION | `{UR}.TI.QVmomStation` | float (м³/ч) | Расчёт | Базовый расход (зафиксирован) | UR_QVMOMDELTA | `{UR}.TI.QVmomDelta` | float (м³/ч) | Расчёт | Отклонение расхода | UR_QVMOMDELTARANGEMAX | `{UR}.TI.QVmomDeltaRangeMax` | float | ИМ/Унификация | Дельта расхода (верх) | UR_QVMOMDELTARANGEMIN | `{UR}.TI.QVmomDeltaRangeMin` | float | ИМ/Унификация | Дельта расхода (низ) | UR_ALMQVMOMRANGEMAX | `{UR}.Alm.AlmQVmomRangeMax` | bool | Расчёт | Аларм: расход выше границы | UR_ALMQVMOMRANGEMIN | `{UR}.Alm.AlmQVmomRangeMin` | bool | Расчёт | Аларм: расход ниже границы | UR_ALMQVMOMINVALID | `{UR}.Alm.AlmQVmomInvalid` | bool | Расчёт | Флаг невалидности расхода | UR_DISABLE | `{UR}.State.Disable` | bool | Оператор/Расчёт | Отключение расходомера | UR_MANUAL | `{UR}.State.Manual` | bool | Оператор | Ручной режим | UR_KM | `{UR}.TI.Km` | float | ИМ | Километровая отметка | UR_TRACESQVMOM | `{UR}.TI.TracesQVmom` | [[float, ts]] | Расчёт | Следы расхода | UR_REMONTSTATUS | `{UR}.State.RemontStatus` | int | СДКУ | Статус ремонта | UR_TU_SETON | `{UR}.TU.SetOn` | bool | Диспетчер | Команда: включить | UR_TU_SETOFF | `{UR}.TU.SetOff` | bool | Диспетчер | Команда: отключить | SGLU_VISIBLE | `{SGLU}.State.Visible` | bool | Расчёт | Видимость сегмента | SGLU_ACTIVITY | `{SGLU}.State.Activity` | bool | Расчёт | Активность сегмента | SGLU_CONTROLON | `{SGLU}.State.ControlOn` | bool | Расчёт | Сегмент на контроле | SGLU_PRIORITY | `{SGLU}.TI.Priority` | int | ИМ | Приоритет (0=подкачка, 1=лупинг) | SGLU_PARTGRZDV | `{SGLU}.TI.PartGRZDV` | string[] | ИМ | Список задвижек | SGLU_PARTUR | `{SGLU}.TI.PartUR` | string[] | ИМ | Список расходомеров | SGLU_PARTPLTM | `{SGLU}.TI.PartPLTM` | string[] | ИМ | Список плотномеров | SGLU_PARTKIP | `{SGLU}.TI.PartKIP` | string[] | ИМ | Список датчиков | SGLU_DIAMETER | `{SGLU}.TI.Diameter` | float (м) | ИМ | Диаметр трубы | SGLU_KM | `{SGLU}.TI.Km` | float | ИМ | Километровая отметка | GRZDV_STATUS | `{GRZDV}.Status` | int (0/1) | Расчёт | Состояние группы | GRZDV_TYPE | `{GRZDV}.TI.Type` | int (1/2) | ИМ | Тип: 1=OR, 2=AND | GRZDV_ACTIVITY | `{GRZDV}.Activity` | bool | Расчёт | Активность группы | GRZDV_PART | `{GRZDV}.TI.Part` | string[] | ИМ | Список ZDV в группе | ZDV_STATUS | `{ZDV}.Status` | int (0/2/3) | СДКУ | Состояние задвижки | ZDV_ACTIVITY | `{ZDV}.Activity` | bool | Расчёт | Активность задвижки | PLTM_RO | `{PLTM}.TI.Ro` | float (кг/м³) | СДКУ | Плотность | PLTM_ROMANUAL | `{PLTM}.TI.RoManual` | float (кг/м³) | Оператор | Ручная плотность | PLTM_ISMANUAL | `{PLTM}.State.IsManual` | bool | Оператор | Ручной режим | PLTM_DISABLE | `{PLTM}.State.Disable` | bool | Оператор/Расчёт | Отключение | PLTM_KM | `{PLTM}.TI.Km` | float | ИМ | Километровая отметка | PLTM_ALMROINVALID | `{PLTM}.Alm.AlmRoInvalid` | bool | Расчёт | Флаг невалидности плотности | PLTM_REMONTSTATUS | `{PLTM}.State.RemontStatus` | int | СДКУ | Статус ремонта | PLTM_TU_SETON | `{PLTM}.TU.SetOn` | bool | Диспетчер | Команда: включить | PLTM_TU_SETOFF | `{PLTM}.TU.SetOff` | bool | Диспетчер | Команда: отключить |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Тег (кратко) | Путь | Тип | Источник | Описание |
| UR_QVMOM | `{UR}.TI.QVmom` | float (м³/ч) | СДКУ | Моментальный расход |
| UR_QVMOMMANUAL | `{UR}.TI.QVmomManual` | float (м³/ч) | Оператор | Ручной расход |
| UR_QVMOMSTATION | `{UR}.TI.QVmomStation` | float (м³/ч) | Расчёт | Базовый расход (зафиксирован) |
| UR_QVMOMDELTA | `{UR}.TI.QVmomDelta` | float (м³/ч) | Расчёт | Отклонение расхода |
| UR_QVMOMDELTARANGEMAX | `{UR}.TI.QVmomDeltaRangeMax` | float | ИМ/Унификация | Дельта расхода (верх) |
| UR_QVMOMDELTARANGEMIN | `{UR}.TI.QVmomDeltaRangeMin` | float | ИМ/Унификация | Дельта расхода (низ) |
| UR_ALMQVMOMRANGEMAX | `{UR}.Alm.AlmQVmomRangeMax` | bool | Расчёт | Аларм: расход выше границы |
| UR_ALMQVMOMRANGEMIN | `{UR}.Alm.AlmQVmomRangeMin` | bool | Расчёт | Аларм: расход ниже границы |
| UR_ALMQVMOMINVALID | `{UR}.Alm.AlmQVmomInvalid` | bool | Расчёт | Флаг невалидности расхода |
| UR_DISABLE | `{UR}.State.Disable` | bool | Оператор/Расчёт | Отключение расходомера |
| UR_MANUAL | `{UR}.State.Manual` | bool | Оператор | Ручной режим |
| UR_KM | `{UR}.TI.Km` | float | ИМ | Километровая отметка |
| UR_TRACESQVMOM | `{UR}.TI.TracesQVmom` | [[float, ts]] | Расчёт | Следы расхода |
| UR_REMONTSTATUS | `{UR}.State.RemontStatus` | int | СДКУ | Статус ремонта |
| UR_TU_SETON | `{UR}.TU.SetOn` | bool | Диспетчер | Команда: включить |
| UR_TU_SETOFF | `{UR}.TU.SetOff` | bool | Диспетчер | Команда: отключить |
| SGLU_VISIBLE | `{SGLU}.State.Visible` | bool | Расчёт | Видимость сегмента |
| SGLU_ACTIVITY | `{SGLU}.State.Activity` | bool | Расчёт | Активность сегмента |
| SGLU_CONTROLON | `{SGLU}.State.ControlOn` | bool | Расчёт | Сегмент на контроле |
| SGLU_PRIORITY | `{SGLU}.TI.Priority` | int | ИМ | Приоритет (0=подкачка, 1=лупинг) |
| SGLU_PARTGRZDV | `{SGLU}.TI.PartGRZDV` | string[] | ИМ | Список задвижек |
| SGLU_PARTUR | `{SGLU}.TI.PartUR` | string[] | ИМ | Список расходомеров |
| SGLU_PARTPLTM | `{SGLU}.TI.PartPLTM` | string[] | ИМ | Список плотномеров |
| SGLU_PARTKIP | `{SGLU}.TI.PartKIP` | string[] | ИМ | Список датчиков |
| SGLU_DIAMETER | `{SGLU}.TI.Diameter` | float (м) | ИМ | Диаметр трубы |
| SGLU_KM | `{SGLU}.TI.Km` | float | ИМ | Километровая отметка |
| GRZDV_STATUS | `{GRZDV}.Status` | int (0/1) | Расчёт | Состояние группы |
| GRZDV_TYPE | `{GRZDV}.TI.Type` | int (1/2) | ИМ | Тип: 1=OR, 2=AND |
| GRZDV_ACTIVITY | `{GRZDV}.Activity` | bool | Расчёт | Активность группы |
| GRZDV_PART | `{GRZDV}.TI.Part` | string[] | ИМ | Список ZDV в группе |
| ZDV_STATUS | `{ZDV}.Status` | int (0/2/3) | СДКУ | Состояние задвижки |
| ZDV_ACTIVITY | `{ZDV}.Activity` | bool | Расчёт | Активность задвижки |
| PLTM_RO | `{PLTM}.TI.Ro` | float (кг/м³) | СДКУ | Плотность |
| PLTM_ROMANUAL | `{PLTM}.TI.RoManual` | float (кг/м³) | Оператор | Ручная плотность |
| PLTM_ISMANUAL | `{PLTM}.State.IsManual` | bool | Оператор | Ручной режим |
| PLTM_DISABLE | `{PLTM}.State.Disable` | bool | Оператор/Расчёт | Отключение |
| PLTM_KM | `{PLTM}.TI.Km` | float | ИМ | Километровая отметка |
| PLTM_ALMROINVALID | `{PLTM}.Alm.AlmRoInvalid` | bool | Расчёт | Флаг невалидности плотности |
| PLTM_REMONTSTATUS | `{PLTM}.State.RemontStatus` | int | СДКУ | Статус ремонта |
| PLTM_TU_SETON | `{PLTM}.TU.SetOn` | bool | Диспетчер | Команда: включить |
| PLTM_TU_SETOFF | `{PLTM}.TU.SetOff` | bool | Диспетчер | Команда: отключить |



### 1.8 Обозначения и соглашения для сценариев

| Обозначение | Реализация | Примечание |
| --- | --- | --- |
| `hmi.set(tag, value)` | `POST http://hmi-backend:8080/v2/tag-set` | Body: `{"tag":tag,"data":{"value":"<str>","invalid":false,"ts":<ms>}}`. Headers: `X-USER-FULLNAME: Test`, `X-USER-ALLOW-PATTERNS: ["MT1..*"]` |
| `hmi.set(tag, value, invalid=true)` | `POST /v2/tag-set` | Body: `{"tag":tag,"data":{"value":"<str>","invalid":true,"ts":<ms>}}` |
| `hmi.set_batch([...])` | `POST /v2/tags-set` | Body: массив объектов |
| `hmi.get(tag)` | `GET http://hmi-backend:8080/v2/tag-get?tagName=tag` | Headers: `X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]`. Ответ: `{"tag":"...","data":{"value":"<str>","invalid":<bool>,"ts":<ms>,"ts2":<ms>}}` |
| `hmi.get_batch([...])` | `POST /v2/tags-get` | Body: массив строк |
| `hmi.wait_change(tag, condition)` | WS `ws://hmi-backend:8080/v2/hotlink` → `SUBSCRIBE` → ожидание `SUB_ANSWER` | Агрегация 50 мс. Таймаут: WAIT + 10 с |
| `hmi.wait_alarm(pattern)` | WS `SUBSCRIBE` на теги matching `pattern` → ожидание `value:true` | Таймаут: WAIT + 10 с |
| `hmi.history(tag, from, to)` | `POST /v2/tags-get-history` | Ответ: массив `{ts, value, invalid}` |
| `kafka.send(topic, msg)` | Kafka Producer API напрямую | Обход hmi-backend (для симуляции СДКУ) |
| `kafka.consume(topic, filter)` | Kafka Consumer API | Проверка сообщений в топике |
| `redis.get(key)` / `redis.set(key, value)` | Redis CLI / client | Чтение/запись кэша ИМ |
| `WAIT(cycle)` | Ожидание по таймеру | 60с / 2с / 1с + margin 5с |
| `WAIT(event)` | Ожидание обработки callback | + margin 5с |
| `RESET()` | Cleanup | См. раздел 2.5 |
| `CONFIG_X = Y` | Значение из ИМ | Не является действием |

> **Важно:** В V2 значение тега — **плоский JSON-примитив** внутри `data.value` (строка: `"5.0"`, `"true"`, `"false"`). Тип валидируется сервером через `ProtoValidator` против типа тега. Несоответствие → HTTP 400.


**Правило ожидания:**

*   Для POLL(60с): `WAIT(60c)` — максимум 65 секунд

*   Для POLL(2с): `WAIT(2c)` — максимум 7 секунд

*   Для POLL(1с): `WAIT(1c)` — максимум 6 секунд

*   Для EVENT: `WAIT(event)` — максимум 5 секунд (callback срабатывает практически мгновенно после изменения тега)

*   Для POLL(60мин): `WAIT(60min)` — максимум 3605 секунд (ночные тесты)





## 2. ТЕСТОВЫЙ СТЕНД

### 2.1 Компоненты стенда

| Компонент | Назначение | Примечание |
| --- | --- | --- |
| **hydro-calculation** | Тестируемый сервис | Java Spring Boot, N экземпляров (1 лидер + followers) |
| **hmi-backend** | API для записи/чтения тегов | REST порт **8080**; WS V2: `ws://hmi-backend:8080/v2/hotlink`. Выступает прокси: REST/WS → Kafka hot topics → hydro-calculation → Kafka → hmi-backend → ответ |
| **clickhouse** | Хранение истории | Порт 8123 |
| **postgresql** | ИМ (конфигурация ТУ, несущая) | Порт 5432 |
| **redis** | Кэш ИМ, состояния | Порт 6379 |
| **kafka** | Брокер сообщений (KRaft) | Порт 9092 |

### 2.2 Механизмы ввода/вывода данных

Все взаимодействия с hydro-calculation в тест-кейсах осуществляются через **hmi-backend** (порт 8080). hmi-backend выступает прослойкой: REST/WS запросы → Kafka `cspa-main-topic` → hydro-calculation → Kafka → hmi-backend → ответ.

#### REST (однозначные запросы)

| Операция | Метод | URL | Body/Query |
| --- | --- | --- | --- |
| Чтение 1 тега | GET | `/v2/tag-get` | `?tagName=MT1.LU1.SGLU1.KIP1.TI.Press` |
| Чтение N тегов | POST | `/v2/tags-get` | `["tag1","tag2",...]` |
| Запись 1 тега | POST | `/v2/tag-set` | `{"tag":"...","data":{"value":5.0,"invalid":false}}` |
| Запись N тегов | POST | `/v2/tags-set` | `[{"tag":"...","data":{...}},...]` |
| История из CH | POST | `/v2/tags-get-history` | `{"startTime":...,"endTime":...,"tags":["..."],"limit":1000}` |

**Обязательные заголовки (запись):** X-USER-FULLNAME: Тестировщик X-USER-ALLOW-PATTERNS: ["MT1..*"]
**Обязательные заголовки (чтение):** X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]
**Формат ответа (чтение):**

```json
{"tag":"MT1.LU1.SGLU1.KIP1.TI.Press","data":{"value":5.0,"invalid":false,"ts":1700000000000}}
```

#### WebSocket (подписка на изменения, E2E-проверки)

Адрес: ws://:8080/v2/hotlink
Формат кадра V2:

```json
{"cmd":"SUBSCRIBE","id":"req-001","args":["MT1.LU1.SGLU1.KIP1.TI.Head"],"headers":{"X-USER-ALLOW-PATTERNS":"[\"MT1\\..*\"]","X-USER-FULLNAME":"Тестировщик"}}
```

Приём изменения:

```json
{"cmd":"SUB_ANSWER","id":"req-001","args":[{"tag":"MT1.LU1.SGLU1.KIP1.TI.Head","data":{"value":663.2,"invalid":false,"ts":1700000000000}}]}
```

**Использование в сценариях:**

*   Быстрая проверка (поллинг): REST GET /v2/tag-get — проще, синхронно

*   E2E-проверка: WS SUBSCRIBE → ожидание SUB_ANSWER — подтверждает, что изменение прошло через весь цикл (Kafka → hydro-calculation → Kafka → hmi-backend)

*   Алармы: WS SUBSCRIBE на MT1.LU1.Alm.* → ожидание SUB_ANSWER с value: true


**Выбор метода в сценариях**
| Обозначение в сценарии | Реализация | Когда использовать |
| --- | --- | --- |
| `hmi.set(tag, value)` | `POST /v2/tag-set` | Запись входных данных (давления, расходы, команды) |
| `hmi.set(tag, value, invalid=true)` | `POST /v2/tag-set` с `"invalid":true` | Симуляция невалидных данных |
| `hmi.set_batch([...])` | `POST /v2/tags-set` | Одновременная запись нескольких тегов |
| `hmi.get(tag)` | `GET /v2/tag-get?tagName=...` | Проверка расчётного значения (поллинг) |
| `hmi.get_batch([...])` | `POST /v2/tags-get` | Проверка нескольких тегов за один запрос |
| `hmi.wait_change(tag, expected)` | WS `SUBSCRIBE` + ожидание `SUB_ANSWER` | E2E-проверка: значение изменилось через полный цикл |
| `hmi.wait_alarm(pattern)` | WS `SUBSCRIBE` на паттерн + ожидание `SUB_ANSWER` | E2E-проверка: аларм сгенерирован и доставлен |
| `hmi.history(tag, from, to)` | `POST /v2/tags-get-history` | Проверка истории (ClickHouse) |

> **Ограничения hmi-backend, влияющие на автотесты:**
>
> 1.  **503 до готовности:** Все эндпоинты hmi-backend возвращают 503 до завершения AppWarmUp (`HmiEvoService.isReady() = true`). В автотесте: после `actuator/health = UP` дождаться `GET /diag/instance` → 200 (интервал опроса: 1 с, max 30 с).
>
> 2.  **Валидация типа:** `POST /v2/tag-set` с несовпадающим типом значения (например, `"value":"abc"` для DOUBLE-тега) → **HTTP 400** + `ValueConversionException`. В автотесте: использовать числовые значения как строки (`"5.0"`, не `5.0`).
>
> 3.  **Агрегация WS V2 (50 мс):** При подписке через WS V2 значения приходят пакетом не чаще чем раз в 50 мс. В автотесте: после `hmi.set` (через WS TAG_SET) ожидать `SUB_ANSWER` с таймаутом ≥ 200 мс.
>
> 4.  **Minuteman (30 с):** WS-сессия hmi-backend без активности будится каждые 30 с (`wake-time`), закрывается через 3600 с (`stale-time`, default). В длительных сценариях (> 2 мин) отправлять `PING` каждые 15–20 с.
>
> 5.  **Kafka-маршрутизация:** hmi-backend не знает о `cspa-main` или `model_main_{sessionId}` напрямую. Привязка hot topic к топику hydro-calculation — ответственность конфигурации (`CSPA_TOPICS` / `TopicRouteConfig`). Если hot topic ≠ `cspa-main` — значения не дойдут до hydro-calculation.
>
> 6.  **Заголовки обязательны:** Без `X-USER-FULLNAME` и `X-USER-ALLOW-PATTERNS` при записи → HTTP 401/403. Без `X-USER-GET-ALLOW-PATTERNS` при чтении → доступ по default `[".*"]` (все теги).
>

### 2.3 Топики Kafka

| Топик | Направление | Формат |
| --- | --- | --- |
| `main` | Вход + Выход | `{tag, ts, value, invalid}` |
| `alarm` | Выход | `{tag, ts, value, text, priority, state}` |
| `model_main_{id}` | Вход + Выход (моделирование) | `{tag, ts, value, invalid}` |
| `model_alarm_{id}` | Выход (моделирование) | `{tag, ts, value, text, priority, state}` |

### 2.4 Начальное состояние стенда

Перед запуском тестов стенд находится в следующем состоянии:

*   Конфигурация ТУ загружена в data-manager (PostgreSQL + Redis): массивы `LU_KM`, `LU_HEIGHT`, `LU_PMAXDEFAULT` для всех ТУ

*   Все KIP, UR, PLTM, GRZDV, ZDV, SGLU существуют в ИМ

*   Все датчики в состоянии `Disable = false`, `Manual = false`

*   `LU_CONTROL = 0` для всех ТУ

*   `LU_AUTOCONTROLON = false` для всех ТУ

*   Топик `main` наполнен текущими (штатными) значениями

*   Топик `alarm` пуст (или содержит только стартовые события)

*   Конфигурационные значения (ΔMax, ΔMin, DensLimit, PressRateLimit и т.д.) заданы в ИМ


> **Примечание:** Конкретная конфигурация ТУ для автотестов ещё не выбрана. В сценариях используются абстрактные адреса без привязки к конкретному ТДП: `MT1.LU1.SGLU1.KIP1` и т.д.



### 2.5 Cleanup (возврат к исходному состоянию)

После каждого тест-кейса:

1.  Все изменённые теги возвращаются к значениям из начального состояния

2.  Если был включён Control → снимается (`SetControlOff = 1`)

3.  Если был включён AutoControl → отключается (`SetAutoControlOff = 1`)

4.  Если были заданы PressManualLimit → очищаются

5.  Если была включена трассировка → выключается

6.  Алармы в топике `alarm` не очищаются (накапливаются), но при проверке используются только события, появившиеся после начала конкретного теста

7.  hmi-backend: WS-подписки отключены (команда `UNSUBSCRIBE_ALL` через `ws://hmi-backend:8080/v2/hotlink` или закрытие WS-сокета)

8.  hmi-backend: WS-сессия закрыта (если использовалась для `SUBSCRIBE` / `TAG_SET` / `TAG_GET` в рамках сценария)


> Cleanup не является объектом проверки. Он обеспечивает изоляцию тестов: каждый тест стартует с известного состояния.



### 2.6. Обозначения и соглашения для сценариев

| Обозначение | Реализация | Примечание |
| --- | --- | --- |
| `hmi.set(tag, value)` | `POST http://hmi:8080/v2/tag-set` | Body: `{"tag":tag,"data":{"value":value,"invalid":false}}` |
| `hmi.set(tag, value, invalid=true)` | `POST http://hmi:8080/v2/tag-set` | Body: `{"tag":tag,"data":{"value":value,"invalid":true}}` |
| `hmi.set_batch(tag1:v1, tag2:v2, ...)` | `POST http://hmi:8080/v2/tags-set` | Массив объектов |
| `hmi.get(tag)` | `GET http://hmi:8080/v2/tag-get?tagName=tag` | Ответ: `{"tag":...,"data":{"value":...,"invalid":...}}` |
| `hmi.get_batch(tag1, tag2, ...)` | `POST http://hmi:8080/v2/tags-get` | Body: массив строк |
| `hmi.wait_change(tag, condition)` | WS `ws://hmi:8080/v2/hotlink` → `SUBSCRIBE` → ожидание `SUB_ANSWER` | Таймаут: max_wait + 10 с |
| `hmi.wait_alarm(pattern)` | WS `SUBSCRIBE` на теги matching `pattern` → ожидание `value:true` | Таймаут: max_wait + 10 с |
| `hmi.history(tag, from, to)` | `POST http://hmi:8080/v2/tags-get-history` | Ответ: массив записей `{ts, value, invalid}` |
| `WAIT(cycle)` | Ожидание по таймеру (без запроса) | 60с / 2с / 1с + margin 5с |
| `WAIT(event)` | Ожидание обработки события + margin 5с | Для POLL(60с): 65с. Для POLL(2с): 7с. Для EVENT: 5с |
| `RESET()` | `POST /v2/tags-set` с начальными значениями | См. раздел 2.5 |
| `// PRIMECHANIE: ...` | Комментарий | Не является действием |

**Правила:**

*   `hmi.get` — поллинг: допустимо 3 повторных запроса с интервалом 2 с (всего ~6 с), если значение не изменилось

*   `hmi.wait_change` — подписка на WS → ожидание `SUB_ANSWER` → timeout

*   `WAIT(cycle)` — «слепое» ожидание: используется когда нужен полный цикл алгоритма (POLL). После `WAIT` всегда `hmi.get` для проверки

*   Порядок: `hmi.set` → `WAIT` → `hmi.get` (для POLL). `hmi.set` → `hmi.wait_change` (для EVENT/E2E)


**Заголовки (все REST запросы):**

```
X-USER-ALLOW-PATTERNS: ["MT1.."] X-USER-GET-ALLOW-PATTERNS: ["MT1.."] X-USER-FULLNAME: Test
```

**Заголовки (все WS кадры, в** `headers`**):**

```
"X-USER-ALLOW-PATTERNS": "["MT1\..*"]" "X-USER-FULLNAME": "Test"
```

## 3. СЦЕНАРИИ АВТОТЕСТОВ

### 3.1 Базовые расчёты: напор, несущая, контроль

* * *

#### 3.1.1 Расчётный напор

* * *

##### **HY-CALC-001 — Расчётный напор: номинальный режим**

**Требование: R-HYDR-001**
**Описание:** Базовый расчёт пьезометрического напора. Давление от СДКУ пересчитывается в высоту столба жидкости с учётом гидростатической составляющей (высоты датчика). Это главный визуальный инструмент: линия напора показывает энергию жидкости вдоль ТУ. Если напор ниже конфигурации — воздух, если выше несущей — риск разрушения.
**Формула:**

```
Head = (P / ρ) × 101970 + H
```

**Обоснование выбора значений:**

*   P = 5.0 МПа — типичное рабочее давление магистрального трубопровода (50 кгс/см²)

*   ρ = 850 кг/м³ — типичная плотность нефтепродукта (нефть, мазут)

*   H = 75 м — типичная высотная отметка для трубопровода в равнинной местности

*   Расчёт: `(5.0 / 850) × 101970 + 75 = 599.7 + 75 = 674.7 м`


**Предусловие:**

*   Конфигурация ТУ1 загружена: `LU_KM = [0, 50, 100, 150, 200]`, `LU_HEIGHT = [60, 62, 65, 68, 70]`

*   `KIP1_KM = 75` → `KIP1_HEIGHT = 63.5 м` (интерполяция между км 50 и 100)

*   `KIP1_MANUAL = false`

*   `KIP1_RO = 850` кг/м³

*   `KIP1_DISABLE = false`

*   `LU1_CONTROL = 0`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — записать давление

2.  `WAIT(event)` — KipHeadAlg срабатывает по событию на KIP_PRESS

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` — прочитать напор


**Ожидаемый результат:**

*   `KIP1_HEAD = (5.0 / 850) × 101970 + 63.5 = 599.7 + 63.5 = 663.2 м`

*   `KIP1_HEAD.invalid = false`

*   Тег присутствует в ответе `hmi.get`


**Teardown:** `RESET()`


##### **HY-CALC-002 — Расчётный напор: ручная корректировка высоты**

**Требование:** R-HYDR-001
**Описание:** Оператор вручную задаёт поправку к высоте (`HeightCorrection`) — это нужно, когда геометрическая высота датчика в конфигурации ТУ известна неточно. В ручном режиме расчёт напора использует `HeightCorrection` вместо интерполированной `Height`.
**Формула (режим ручной корректировки):**

```
При Manual = true:  Head = (P / ρ) × 101970 + HeightCorrection
При Manual = false: Head = (P / ρ) × 101970 + Height (из конфигурации ТУ)
```

**Обоснование:**

*   Height = 63.5 м (из конфигурации ТУ, как в HY-CALC-001)

*   HeightCorrection = 70.0 м — оператор знает, что датчик стоит на эстакаде, фактически выше

*   Расчёт при Manual=1: `(5.0 / 850) × 101970 + 70.0 = 599.7 + 70.0 = 669.7 м`

*   Расчёт при Manual=0: `(5.0 / 850) × 101970 + 63.5 = 599.7 + 63.5 = 663.2 м`


**Предусловие:**

*   `KIP1_HEIGHT = 63.5 м` (из конфигурации ТУ)

*   `KIP1_HEIGHTCORRECTION = 70.0 м` (уже задано оператором ранее)

*   `KIP1_MANUAL = false`

*   `KIP1_RO = 850`

*   `KIP1_PRESS = 5.0` МПа (стабильно)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.Manual", true)` — включить ручной режим

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` — проверить при Manual=1

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.Manual", false)` — выключить ручной режим

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` — проверить при Manual=0


**Ожидаемый результат:**

*   При Manual=1: `KIP1_HEAD = 669.7 м` (используется HeightCorrection = 70.0)

*   При Manual=0: `KIP1_HEAD = 663.2 м` (используется Height = 63.5 из конфигурации ТУ)


**Teardown:** `RESET()`


##### **HY-CALC-003 — Расчётный напор: аномальная плотность**

**Требование:** R-HYDR-001
**Описание:** Плотность может опуститься ниже 500 кг/м³. Если не заменить на 500 — деление на малое число даст завышенный напор, что может привести к ложному срабатыванию аларма о превышении несущей. Замена на 500 — защита от арифметического переполнения и ложной тревоги.
**Формула:**

```
ρ_расчёт = max(ρ_фактический, 500)
Head = (P / ρ_расчёт) × 101970 + H
```

**Обоснование выбора значения:**

*   Граничное значение: 500 кг/м³ — минимально допустимое (константа `MIN_DENSITY` в коде)

*   Тестируем **499** — на 1 единицу ниже порога (техническая техника граничных значений)

*   P = 5.0 МПа, H = 63.5 м (как в HY-CALC-001)

*   При ρ = 499: `ρ_расчёт = 500` → `Head = (5.0/500) × 101970 + 63.5 = 1019.7 + 63.5 = 1083.2 м`

*   Без замены (ρ = 499): `Head = (5.0/499) × 101970 + 63.5 = 1021.5 + 63.5 = 1085.0 м` (завышение на 1.8 м — небольшое, но принцип подтверждён)


**Предусловие:**

*   `KIP1_HEIGHT = 63.5 м`

*   `KIP1_RO = 499` кг/м³ (ниже порога 500)

*   `KIP1_MANUAL = false`

*   `KIP1_DISABLE = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)`

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")`


**Ожидаемый результат:**

*   `KIP1_HEAD = (5.0 / 500) × 101970 + 63.5 = 1083.2 м`

*   Плотность заменена на 500 (фактически 499)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-004 — Расчётный напор: невалидное давление**

**Требование:** R-HYDR-001
**Описание:** Давление от СДКУ помечено `invalid = true`. Невалидные данные не должны порождать расчётные значения — это может привести к ложным алармам. Расчётный движок обязан пометить результат `invalid = true`.
**Обоснование:** Проверяем, что цепочка invalid распространяется: Press.invalid → Head.invalid. Без валидного напора невозможны проверки несущей и самотеков
**Предусловие:**

*   `KIP1_HEIGHT = 63.5 м`, `KIP1_RO = 850`, `KIP1_MANUAL = false`

*   До теста — штатная работа: `KIP1_HEAD = 663.2 м`, `invalid = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=true)` — записать невалидное давление

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")`


**Ожидаемый результат:**

*   `KIP1_HEAD.invalid = true` (или тег отсутствует)

*   Числовое значение `KIP1_HEAD` не имеет значения (не используется)

*   Алармы по невалидным данным не генерируются


**Teardown:** `RESET()`

#### 3.1.2 Диапазон давления

* * *

##### **HY-CALC-005 — Расчёт диапазона давления при постановке на контроль**

**Требование:** R-HYDR-022 R-HYDR-006
**Описание:** Диспетчер фиксирует текущее состояние ТУ как базовое. После этого система сравнивает живые данные с базовыми и генерирует алармы при отклонениях. До постановки — пассивный мониторинг, после — активный контроль.
**Формулы:**

```
PressStation = фактическое давление в момент постановки
PressRangeMax = PressStation + PressDeltaRangeMax
PressRangeMin = PressStation − PressDeltaRangeMin
```

**Обоснование выбора значений:**

*   `PressDeltaRangeMax = 0.2 МПа` — типичное значение из ИМ для данного ТУ. Выбрано как демонстрационное: достаточно для визуализации на графике, но не настолько большое, чтобы пропустить реальную утечку

*   `PressDeltaRangeMin = 0.1 МПа` — асимметрия осознанная: давление ниже базового опаснее (кавитация, воздух), поэтому нижняя граница уже

*   P = 5.0 МПа — стабильное рабочее давление

*   Расчёт: `RangeMax = 5.0 + 0.2 = 5.2`, `RangeMin = 5.0 − 0.1 = 4.9`


**Полный список выходных параметров при постановке:**
| Тег | Описание | Ожидаемое |
| --- | --- | --- |
| `LU1_CONTROL` | Состояние контроля | 1 |
| `KIP1_PRESSSTATION` | Базовое давление | 5.0 МПа |
| `UR1_QVMOMSTATION` | Базовый расход | Зафиксировано (текущее значение UR1) |
| `LU1_GRAVITYSEGSREG` | Слепок самотеков | Копия текущего `LU1_GRAVITYSEGS` |
| `SGLU1_CONTROLON` | Сегмент на контроле | true |
| `KIP1_PRESSRANGEMAX` | Верхняя граница | 5.2 МПа |
| `KIP1_PRESSRANGEMIN` | Нижняя граница | 4.9 МПа |
| `LU1_TU_SETCONTROLON` | Команда сброшена | false |

**Предусловие:**

*   `LU1_CONTROL = 0`

*   `KIP1_PRESS = 5.0` МПа (стабильно)

*   `KIP1_PRESSDELTARANGEMAX = 0.2` (из ИМ)

*   `KIP1_PRESSDELTARANGEMIN = 0.1` (из ИМ)

*   `UR1_QVMOM = 120.0` м³/ч

*   `LU1_GRAVITYSEGS` заполнен (конфигурация ТУ рассчитана)

*   `SGLU1_CONTROLON = false`

*   `LU1_TU_SETCONTROLON = false`


**Действия:**

1.  `hmi.set("MT1.LU1.TU.SetControlOn", true)` — команда постановки на контроль

2.  `WAIT(event)` — LuControlSetAlg срабатывает

3.  `hmi.get(...)` — проверить все выходные теги


**Ожидаемый результат:**

1.  `LU1_CONTROL = 1`

2.  `KIP1_PRESSSTATION = 5.0` (зафиксировано)

3.  `UR1_QVMOMSTATION = 120.0` (зафиксировано)

4.  `LU1_GRAVITYSEGSREG = копия LU1_GRAVITYSEGS`

5.  `SGLU1_CONTROLON = true`

6.  `LU1_TU_SETCONTROLON = false` (сброшен)

7.  `KIP1_PRESSRANGEMAX = 5.2 МПа`

8.  `KIP1_PRESSRANGEMIN = 4.9 МПа`


**Teardown:** `hmi.set("MT1.LU1.TU.SetControlOff", true)` → `WAIT(event)` → `RESET()`

* * *

##### **HY-CALC-006 — Постановка на контроль: отключённый датчик не участвует**

**Требование:** R-HYDR-022
**Описание:** Отключённый датчик (`Disable = true`) не участвует в формировании базового состояния. Его `PressStation` помечается `invalid = true`. Это нужно, чтобы невалидное давление отключённого датчика не исказило диапазон для остальных.
**Сценарий (обоснование):**

*   Датчик A: `Press = 0.0` МПа (отключён, показывает 0 — типично для обрыва сигнала)

*   Датчик B: `Press = 5.0` МПа (норма)

*   Если бы A участвовал: `PressStation_A = 0.0` → `RangeMax_A = 0.0 + 0.2 = 0.2` → B мгновенно дал бы аларм (5.0 >> 0.2)

*   Если A исключён: `PressStation_A = invalid` → B работает штатно (RangeMax_B = 5.2)


**Предусловие:**

*   `LU1_CONTROL = 0`

*   `KIP_A_DISABLE = true`, `KIP_A_PRESS = 0.0`

*   `KIP_B_DISABLE = false`, `KIP_B_PRESS = 5.0`

*   `KIP_B_PRESSDELTARANGEMAX = 0.2`, `KIP_B_PRESSDELTARANGEMIN = 0.1`


**Действия:**

1.  `hmi.set("MT1.LU1.TU.SetControlOn", true)`

2.  `WAIT(event)`

3.  Проверить `KIP_A_PRESSSTATION` и `KIP_B_PRESSSTATION`


**Ожидаемый результат:**

*   `KIP_A_PRESSSTATION.invalid = true` (отключённый датчик не зафиксирован)

*   `KIP_B_PRESSSTATION = 5.0` (зафиксирован штатно)

*   `KIP_B_PRESSRANGEMAX = 5.2`, `KIP_B_PRESSRANGEMIN = 4.9`

*   Алармы по KIP_B не сгенерированы


**Teardown:** `RESET()`

* * *

##### **HY-CALC-007 — Снятие ТУ с контроля**

**Требование:** R-HYDR-023
**Описание:** Диспетчер останавливает мониторинг. Базовые значения аннулируются. Все алармы давления, расхода, дебаланса перестают генерироваться. Нужно при плановом/аварийном ремонте, смене режима.
**Что сбрасывается:**

```
PressStation → invalid
QVmomStation → invalid
GravitySegsReg → invalid/пусто
ControlOn → false (все сегменты)
LU_CONTROL → 0
```

**Предусловие:**

*   `LU1_CONTROL = 1` (на контроле)

*   `KIP1_PRESSSTATION = 5.0`, `UR1_QVMOMSTATION = 120.0` (зафиксированы)

*   `SGLU1_CONTROLON = true`

*   `LU1_GRAVITYSEGSREG` заполнен


**Действия:**

1.  `hmi.set("MT1.LU1.TU.SetControlOff", true)`

2.  `WAIT(event)` — LuControlUnsetAlg

3.  Проверить все теги


**Ожидаемый результат:**

1.  `LU1_CONTROL = 0`

2.  `LU1_GRAVITYSEGSREG.invalid = true`

3.  `KIP1_PRESSSTATION.invalid = true`

4.  `UR1_QVMOMSTATION.invalid = true`

5.  `SGLU1_CONTROLON = false`

6.  `LU1_TU_SETCONTROLOFF = false` (сброшен)

7.  `KIP1_ALMDEVMAXRANGE = false`, `KIP1_ALMDEVMINRANGE = false`

8.  `LU1_ALMDEVQMOM = false`

9.  `LU1_ALMPRESSDEV = false` (аларм по смежным тоже сброшен) — если бы остался, диспетчер видит красный индикатор при выключенном контроле

10.  `LU1_INDICATORCONTROL = 0` (сброшен до ControlOff) — не 1 (Norm)

11.  `LU1_INDICATORLINK` **не изменяется** (связь не зависит от режима контроля)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-008 — Режим контроля перехода (TransitionControlOn)**

**Требование:** R-HYDR-024
**Описание:** После остановки и перезапуска перекачки давления не стабилизируются сразу. Режим перехода (Control=2) фиксирует новую точку отсчёта, но подавляет большинство алармов. **Критическая особенность:** `AlmDevHeadCarrier` НЕ подавляется даже при Control=2 — это последний рубеж защиты.

> Тег `LU1_TU_TRANSITIONCONTROLON` — допущение. В коде механизм перехода в Control=2 реализован в `LuControlSetAlg` (при определённых условиях Control устанавливается в 2 вместо 1). Точный триггер уточняется. В сценарии используется абстрактная команда диспетчера.

**Что происходит при TransitionControlOn:**
| Параметр | Значение |
| --- | --- |
| `LU1_CONTROL` | 2 |
| `LU1_INDICATORCONTROL` | 5 |
| `KIP1_PRESSSTATION` | Зафиксировано |
| `UR1_QVMOMSTATION` | Зафиксировано |
| Алармы давления (AlmDevMax/MinRange) | **НЕ генерируются** |
| Алармы расхода (AlmQVmomRange) | **НЕ генерируются** |
| Аларм дебаланса (AlmDevQmom) | **НЕ генерируется** |
| Аларм скорости (AlmRateLimitPress) | **НЕ генерируется** |
| `LU1_ALMDEVHEADCARRIER` | **Генерируется** (не подавляется) |

**Предусловие:**

*   `LU1_CONTROL = 0`

*   Конфигурация ТУ загружена, давления нестабильны (переходный процесс)

*   `KIP1_PRESS = 5.0`, `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`

*   `LU1_CARRIERHEADDEF[km_75] = 793.6 м` (несущая для данного км)

*   `KIP1_HEAD = 663.2 м` (ниже несущей — штатно)


**Действия:**

1.  `hmi.set("MT1.LU1.TU.TransitionControlOn", true)`

2.  `WAIT(event)`

3.  Проверить `LU1_CONTROL`, `LU1_INDICATORCONTROL`

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 7.0)` — повысить давление (но ниже несущей)

5.  `WAIT(event)`

6.  Проверить: `KIP1_ALMDEVMAXRANGE` — должен быть false (подавлен)

7.  Проверить: `LU1_ALMDEVHEADCARRIER` — должен быть false (Head < несущей)


**Ожидаемый результат:**

1.  `LU1_CONTROL = 2`

2.  `LU1_INDICATORCONTROL = 5`

3.  `KIP1_PRESSSTATION`, `UR1_QVMOMSTATION` зафиксированы

4.  При Press = 7.0 (выше базового, вне диапазона): `KIP1_ALMDEVMAXRANGE = false` (подавлен)

5.  `LU1_ALMDEVHEADCARRIER = false` (напор 739.3 м < несущей 793.6 м)

6.  Алармы дебаланса, скорости — не генерируются


**Дополнительные проверки (переходы из Control=2):**
| # | Действие | Ожидаемое |
| --- | --- | --- |
| A | `hmi.set("MT1.LU1.TU.SetControlOff", true)` при Control=2 | `LU1_CONTROL = 0`. Базовые значения → invalid |
| B | `hmi.set("MT1.LU1.TU.SetControlOn", true)` при Control=2 | **Определить фактическое поведение**: Control=1 (повторная постановка) или игнор. Зафиксировать |
| C | `hmi.set("MT1.LU1.TU.TransitionControlOn", true)` повторно при Control=2 | Игнор (уже в режиме перехода) или сброс базовых. Зафиксировать |

**Примечание:** Точное поведение переходов из Control=2 определяется при первом прогоне и уточняется у коллег. Критерий: система не уходит в неопределённое состояние.
**Teardown:** `RESET()`

* * *

##### **HY-CALC-009 — Повторная постановка на контроль: базовое состояние не обнуляется**

**Требование:** R-HYDR-022
**Описание:** Повторная команда `SetControlOn` при уже активном контроле (Control=1) не перефиксирует базовое состояние. Иначе все алармы сработали бы заново, а старые отклонения «исчезли» — ложная стабилизация.
**Предусловие:**

*   `LU1_CONTROL = 1`

*   `KIP1_PRESSSTATION = 5.0` (зафиксировано давно)

*   `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9`

*   `LU1_TU_SETCONTROLON = false`


**Действия:**

1.  `hmi.set("MT1.LU1.TU.SetControlOn", true)` — повторная команда

2.  `WAIT(event)`

3.  Проверить теги


**Ожидаемый результат:**

*   `KIP1_PRESSSTATION` остаётся 5.0 (не перефиксируется)

*   `LU1_CONTROL` остаётся 1

*   `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9` (не изменяются)

*   `LU1_GRAVITYSEGSREG` **не перефиксируется** (остаётся как было при первой постановке) — если бы перефиксировался, потерялась бы информация о самотеках на момент первой постановки

*   `SGLU1_CONTROLON` остаётся `true` (не сбрасывается) — если бы сбрасывался, `KipPressRangeAlg` перестал бы срабатывать на этом сегменте

*   `LU1_TU_SETCONTROLON → false` (сброшен)


**Teardown:** `RESET()`

* * *

#### 3.1.3 Несущая давления и напора

* * *

##### **HY-CALC-010 — Несущая давления: заводские значения (PmaxDefault)**

**Требование:** R-HYDR-004, R-HYDR-003
**Описание:** Каждый км ТУ имеет паспортную характеристику — предельно допустимое давление `PmaxDefault`. Из этого массива рассчитывается несущая напора `CarrierHeadDef` — порог, за которым начинается разрушение. Это главный защитный барьер.
**Формулы:**

```
CarrierDef[km] = PmaxDefault[km]  (если PressManualLimit пуст)
CarrierHeadDef[km] = (CarrierDef[km] / ρ_def) × 101970 + H[km]
```

**Обоснование выбора значений:**

*   `PmaxDefault` задано в МПа (не в кгс/см²) — все давления в системе МПа

*   Конфигурация ТУ1: 5 точек по км, PmaxDefault = [6.0, 6.1, 6.2, 6.3, 6.4] МПа

*   `DensDef = 850` кг/м³ — типовая плотность

*   Высоты: [60, 62, 65, 68, 70] м


**Расчёт для км 50 (второй элемент):**

```
CarrierDef = 6.1 МПа
CarrierHeadDef = (6.1 / 850) × 101970 + 62 = 731.6 + 62 = 793.6 м
```

**Расчёт для км 100 (третий элемент):**

```
CarrierDef = 6.2 МПа
CarrierHeadDef = (6.2 / 850) × 101970 + 65 = 744.0 + 65 = 809.0 м
```

**Предусловие:**

*   Конфигурация ТУ1 загружена в data-manager:
    *   `LU1_KM = [0, 50, 100, 150, 200]` км

    *   `LU1_HEIGHT = [60, 62, 65, 68, 70]` м

    *   `LU1_PMAXDEFAULT = [6.0, 6.1, 6.2, 6.3, 6.4]` МПа

*   `LU1_PRESSMANUALLIMIT` — пуст (нет ручных ограничений)

*   `LU1_DENSDEF = 850` кг/м³


**Действия:**

1.  Убедиться, что конфигурация ТУ1 загружена (проверка через PostgreSQL/Redis)

2.  `WAIT(60c)` — LuMaxAllowablePAlg и LuCarrierHeadDefAlg выполняются по циклу

3.  `hmi.get("MT1.LU1.TI.CarrierDef")` — прочитать массив несущей

4.  `hmi.get("MT1.LU1.TI.CarrierHeadDef")` — прочитать массив несущей напора


**Ожидаемый результат:**

*   `LU1_CARRIERDEF = [6.0, 6.1, 6.2, 6.3, 6.4]` МПа (без изменений, PressManualLimit пуст)

*   `LU1_CARRIERHEADDEF ≈ [779.5, 793.6, 809.0, 824.0, 838.0]` м

    *   км 0: `(6.0/850)×101970 + 60 = 719.5 + 60 = 779.5` м

    *   км 50: `(6.1/850)×101970 + 62 = 731.6 + 62 = 793.6` м

    *   км 100: `(6.2/850)×101970 + 65 = 744.0 + 65 = 809.0` м

    *   км 150: `(6.3/850)×101970 + 68 = 756.0 + 68 = 824.0` м

    *   км 200: `(6.4/850)×101970 + 70 = 768.0 + 70 = 838.0` м

*   `LU1_ALMCARRIERONUSER = false`


**Teardown:** `RESET()`

* * *

##### **HY-CALC-011 — Несущая давления: пользователь занижает ограничение**

**Требование:** R-HYDR-004, R-HYDR-037
**Описание:** Оператор обнаружил дефект и занижает допустимое давление через `PressManualLimit`. Система берёт `min(PmaxDefault, PressManualLimit)` и генерирует аларм `AlmCarrierOnUser`.
**Формат PressManualLimit:**

```
"км_от,км_до,лимит_МПа;км_от,км_до,лимит_МПа;..."
```

**Обоснование:**

*   PmaxDefault на км 50 = 6.1 МПа

*   Ограничение: "50,100,5.5" — оператор снижает до 5.5 МПа на км 50–100 (обнаружена коррозия)

*   Результат: `CarrierDef[км 50..100] = min(6.1, 5.5) = 5.5` и `min(6.2, 5.5) = 5.5`


**Предусловие:**

*   Конфигурация ТУ1 как в HY-CALC-010

*   `LU1_PRESSMANUALLIMIT` — пуст

*   `LU1_CARRIERDEF` расчётан по PmaxDefault


**Действия:**

1.  `hmi.set("MT1.LU1.TI.PressManualLimit", "50,100,5.5")` — задать ограничение

2.  `WAIT(event)` — LuMaxAllowablePAlg срабатывает

3.  `hmi.get("MT1.LU1.TI.CarrierDef")`

4.  `hmi.get("MT1.LU1.Alm.AlmCarrierOnUser")`

5.  `hmi.wait_alarm("MT1.LU1.Alm.AlmCarrierOnUser")` — подтвердить доставку

6.  `hmi.history("MT1.LU1.Alm.AlmCarrierOnUser", from=ts_start, to=ts_now)` — проверить текст



**Ожидаемый результат:**

*   `LU1_CARRIERDEF[1]` (км 50) = 5.5 МПа (занижено с 6.1)

*   `LU1_CARRIERDEF[2]` (км 100) = 5.5 МПа (занижено с 6.2)

*   `LU1_CARRIERDEF[0]` (км 0) = 6.0 (без изменений)

*   `LU1_CARRIERDEF[3]` (км 150) = 6.3 (без изменений)

*   `LU1_ALMCARRIERONUSER = true`

*   `hmi.history` возвращает запись: value=true, text содержит «ограничение несущей задано пользователем», «км 50–100», «5.5 МПа»


**Teardown:** `hmi.set("MT1.LU1.TI.PressManualLimit", "")` → `WAIT(event)` → `RESET()`

##### **HY-CALC-081 — PressManualLimit: невалидные форматы [НИЗКИЙ ПРИОРИТЕТ]**

**Требование:** R-HYDR-004 **Описание:** Проверка устойчивости парсера `PressManualLimit` к некорректному вводу. Приоритет: низкий (альтернативные сценарии).
**Предусловие:**

*   Конфигурация ТУ1 как в HY-CALC-010

*   `LU1_PRESSMANUALLIMIT` — пуст


**Действия и ожидаемые результаты:**
| # | Значение | Ожидаемое |
| --- | --- | --- |
| 1 | `"100,50,5.5"` (обратный порядок км) | Ошибка / игнор / `CarrierDef` не изменился. Аларм `AlmCarrierOnUser` не генерируется |
| 2 | `"50,100,7.0"` (выше PmaxDefault=6.1) | `CarrierDef[1..2] = min(6.1, 7.0) = 6.1` (PmaxDefault в приоритете) |
| 3 | `"50,100,abc"` (не число) | Ошибка парсинга, `CarrierDef` не изменился |
| 4 | `"50,100,5.5;75,150,5.0"` (перекрывающиеся) | Определено правило разрешения (первый/последний/ошибка) |
| 5 | `""` (пустая строка) | Сброс к PmaxDefault (повтор HY-CALC-012) |

**Примечание:** Фактическое поведение фиксируется при первом прогоне. Не ожидаем конкретных кодов ошибок — фиксируем, что система не упала и `CarrierDef` не искажён. Тут в целом о целеообразности теста и когда его запускать нужно подумать.
**Teardown:** `hmi.set("MT1.LU1.TI.PressManualLimit", "")` → `WAIT(event)` → `RESET()`


##### **HY-CALC-082 — Фильтрация конфигурации: некорректные массивы**


**Требование:** R-HYDR-014 **Описание:** Проверка обработки некорректной конфигурации ТУ. Приоритет: средний.

**Предусловие:**


*   Hydro-calculation запущен



**Действия и ожидаемые результаты:**

| # | Настройка | Ожидаемое |
| --- | --- | --- |
| 1 | `LU_KM = [0, 50, 100]`, `LU_HEIGHT = [60, 62]` (разная длина) | `KipHeightAlg` → `KIP_HEIGHT.invalid = true`. Лог ошибка. Система не упала |
| 2 | `LU_KM = [0, 100, 50]`, `LU_HEIGHT = [60, 68, 65]` (не отсортирован) | `KipHeightAlg` → интерполяция не определена или по убыванию. `KIP_HEIGHT` корректен или invalid |
| 3 | `LU_HEIGHT = [60, NaN, 65]` (NaN) | `KipHeightAlg` → `KIP_HEIGHT.invalid = true` на интервалы с NaN |
| 4 | `LU_KM = []`, `LU_HEIGHT = []` (пустые) | `KipHeightAlg` → `KIP_HEIGHT` не рассчитывается (invalid) |
| 5 | `LU_PMAXDEFAULT = [6.0, 6.1, 6.2, 6.3, 6.4]`, `LU_KM = [0, 50, 100]` (несогласованные) | `LuMaxAllowablePAlg` → `CarrierDef` по минимальной длине или invalid |


**Примечание:** Фиксируем фактическое поведение (invalid / лог / graceful degradation). Критерий: **сервис не падает, не уходит в бесконечный цикл**.

**Teardown:** Восстановить корректную конфигурацию в data-manager → `WAIT(60c)` → `RESET()`


* * *

##### **HY-CALC-012 — Несущая давления: пользователь снимает ограничение**

**Требование:** R-HYDR-004, R-HYDR-037
**Описание:** Оператор устранил дефект и снимает ручное ограничение. Система возвращает заводское значение и генерирует аларм об удалении ограничения (аудит).
**Предусловие:**

*   `LU1_PRESSMANUALLIMIT = "50,100,5.5"` (установлено ранее)

*   `LU1_CARRIERDEF[1] = 5.5` (занижено)

*   `LU1_ALMCARRIERONUSER = true`


**Действия:**

1.  `hmi.set("MT1.LU1.TI.PressManualLimit", "")` — очистить (снять ограничение)

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.TI.CarrierDef")`

4.  `hmi.wait_alarm("MT1.LU1.Alm.AlmCarrierOnUser")` — подтвердить доставку

5.  `hmi.history("MT1.LU1.Alm.AlmCarrierOnUser", from=ts_start, to=ts_now)` — проверить текст


**Ожидаемый результат:**

*   `LU1_CARRIERDEF[1]` (км 50) = 6.1 МПа (возврат к PmaxDefault)

*   `LU1_CARRIERDEF[2]` (км 100) = 6.2 МПа (возврат)

*   `LU1_ALMCARRIERONUSER = true` (аларм о снятии — для аудита)

*   `hmi.history` возвращает запись: value=true, text содержит «ограничение несущей снято пользователем»


**Teardown:** `RESET()`

* * *

##### **HY-CALC-013 — Напор выше несущей: критический аларм AlmDevHeadCarrier**

**Требование:** R-HYDR-031 R-HYDR-003
**Описание:** Давление в трубе превышает допустимое для данного участка → напор превышает несущую. Аларм `AlmDevHeadCarrier` **не подавляется** даже при Control=2.
**Формула проверки:**

```
Если Head > CarrierHeadDef[km_датчика] → AlmDevHeadCarrier = true
```

**Обоснование выбора значений:**

*   `CarrierHeadDef[km 75]` — для датчика на км 75 (между км 50 и 100)

*   Интерполяция несущей: между 793.6 (км 50) и 809.0 (км 100) → `793.6 + (809.0−793.6)×(75−50)/(100−50) = 793.6 + 7.7 = 801.3 м`

*   Для срабатывания аларма: `Head > 801.3 м`

*   При ρ = 850, H = 63.5: `Head = (P/850)×101970 + 63.5 > 801.3` → `P > (801.3 − 63.5) × 850 / 101970 = 737.8 × 850 / 101970 = 6.15 МПа`

*   Тестируем: P = 6.5 МПа → `Head = (6.5/850)×101970 + 63.5 = 779.5 + 63.5 = 843.0 м > 801.3 м` → аларм

*   Контроль: P = 5.0 МПа → `Head = 663.2 м < 801.3 м` → без аларма


**Предусловие:**

*   `LU1_CONTROL = 1` (на контроле)

*   `KIP1_KM = 75`, `KIP1_HEIGHT = 63.5 м`, `KIP1_RO = 850`

*   `LU1_CARRIERHEADDEF` расчётан: значение для км 75 ≈ 801.3 м

*   `KIP1_PRESS = 5.0` МПа → `KIP1_HEAD = 663.2 м` (ниже несущей — штатно)

*   `LU1_ALMDEVHEADCARRIER = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 6.5)` — превысить несущую

2.  `WAIT(event)` — LuAlmDevHeadCarrierAlg

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")`

4.  `hmi.get("MT1.LU1.Alm.AlmDevHeadCarrier")`

5.  `hmi.wait_alarm("MT1.LU1.Alm.AlmDevHeadCarrier")` — подтвердить доставку

6.  `hmi.history("MT1.LU1.Alm.AlmDevHeadCarrier", from=ts_start, to=ts_now)` — проверить текст

7.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — вернуть в норму

8.  `WAIT(event)`

9.  `hmi.get("MT1.LU1.Alm.AlmDevHeadCarrier")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_HEAD = (6.5/850)×101970 + 63.5 = 843.0 м`

*   Шаг 4: `LU1_ALMDEVHEADCARRIER = true` (843.0 > 801.3)

*   Шаг 5: `hmi.history` возвращает запись: value=true, text содержит «напор превышает несущую»

*   Шаг 8: `LU1_ALMDEVHEADCARRIER = false` (663.2 < 801.3, сброшен)


**Примечание:** Аларм НЕ подавляется при Control=2. Для проверки — см. HY-CALC-008.
**Teardown:** `RESET()`

* * *

### 3.2 Дебаланс расходов

* * *

##### **HY-CALC-019 — Дебаланс расходов: штатная работа**

**Требование:** R-HYDR-012, R-HYDR-033
**Описание:** На ТУ без утечки расходы на входе и выходе совпадают (с точностью до погрешности СИКГ). Система считает мгновенный дебаланс `DiffQmom`. Если в пределах лимита — штатно.
**Формула:**

```
DiffQmom = QVmom_входной − QVmom_выходной
```

**Обоснование:**

*   Входной UR (на максимальном км ТУ1, т.е. км 200): `QVmom = 120.5` м³/ч

*   Выходной UR (на минимальном км ТУ1, т.е. км 0): `QVmom = 120.0` м³/ч

*   `DiffQmom = 120.5 − 120.0 = 0.5` м³/ч

*   Лимит: `DiffQmomLimitMax = 1.5`, `DiffQmomLimitMin = −1.5` (из ИМ, типовые значения для данного диаметра)

*   0.5 ∈ [−1.5, +1.5] → в пределах


**Важно:** «Входной» — UR с максимальным км (куда течёт жидкость), «выходной» — UR с минимальным км (откуда). Это определяется автоматически по `UR_KM`.
**Предусловие:**

*   `LU1_CONTROL = 1`

*   `UR1` (км 0, выходной): `Disable = false`, `Manual = false`, `QVmom = 120.0`

*   `UR2` (км 200, входной): `Disable = false`, `Manual = false`, `QVmom = 120.5`

*   `LU1_DIFFQMOMLIMITMAX = 1.5` (из ИМ)

*   `LU1_DIFFQMOMLIMITMIN = −1.5` (из ИМ)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 120.5)` — входной

2.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0)` — выходной

3.  `WAIT(60c)` — LuDiffQAlg по циклу

4.  `hmi.get("MT1.LU1.TI.DiffQmom")`

5.  `hmi.get("MT1.LU1.Alm.AlmDevQmom")`


**Ожидаемый результат:**

*   `LU1_DIFFQMOM = 0.5` м³/ч

*   `LU1_ALMDEVQMOM = false` (0.5 < 1.5)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-020 — Дебаланс расходов: превышение лимита (утечка)**

**Требование:** R-HYDR-012, R-HYDR-033
**Описание:** Дебаланс вышел за допустимые пределы — индикатор утечки или неисправности СИКГ. Аларм сбрасывается автоматически при возврате в норму.
**Обоснование:**

*   Входной: 122.0, выходной: 120.0 → `DiffQmom = 2.0` м³/ч

*   Лимит: 1.5 м³/ч

*   2.0 > 1.5 → аларм

*   Возврат: входной 120.3 → `DiffQmom = 0.3` → в пределах → сброс


**Предусловие:**

*   Как в HY-CALC-019, `LU1_CONTROL = 1`

*   `LU1_DIFFQMOMLIMITMAX = 1.5`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 122.0)` — входной (вырос)

2.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0)` — выходной (норма)

3.  `WAIT(60c)`

4.  `hmi.get("MT1.LU1.TI.DiffQmom")` → проверить значение

5.  `hmi.get("MT1.LU1.Alm.AlmDevQmom")` → проверить аларм

6.  `hmi.wait_alarm("MT1.LU1.Alm.AlmDevQmom")` — подтвердить доставку

7.  `hmi.history("MT1.LU1.Alm.AlmDevQmom", from=ts_start, to=ts_now)` — проверить текст

8.  `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 120.3)` — вернуть в норму

9.  `WAIT(60c)`

10.  `hmi.get("MT1.LU1.TI.DiffQmom")`

11.  `hmi.get("MT1.LU1.Alm.AlmDevQmom")`


**Ожидаемый результат:**

*   Шаг 4: `LU1_DIFFQMOM = 2.0` м³/ч

*   Шаг 5: `LU1_ALMDEVQMOM = true`

*   Шаг 6: `hmi.history` возвращает запись: value=true, text содержит «дебаланс расходов превышает допустимый: 2.0 м³/ч при лимите ±1.5 м³/ч»

*   Шаг 9: `LU1_DIFFQMOM = 0.3` м³/ч

*   Шаг 10: `LU1_ALMDEVQMOM = false` (сброшен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-021 — Дебаланс: исключение отключённого расходомера**

**Требование:** R-HYDR-012, R-HYDR-033
**Описание:** Если один из краевых расходомеров отключён — система исключает его из расчёта. Иначе дебаланс был бы завышен из-за отсутствия данных (0 вместо реального расхода), и система дала бы ложную тревогу.
**Обоснование:**

*   Входной UR отключён (`Disable = true`), показывает 0

*   Если бы не исключение: `DiffQmom = 0 − 120.0 = −120.0` → ложный аларм

*   С исключением: `DiffQmom` не рассчитывается (invalid) или рассчитывается по доступным данным → аларма нет


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `UR1` (км 0, выходной): `Disable = false`, `QVmom = 120.0`

*   `UR2` (км 200, входной): `Disable = false`, `QVmom = 120.5`

*   `LU1_ALMDEVQMOM = false` (штатно)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU2.UR2.State.Disable", true)` — отключить входной

2.  `WAIT(60c)`

3.  `hmi.get("MT1.LU1.TI.DiffQmom")`

4.  `hmi.get("MT1.LU1.Alm.AlmDevQmom")`

5.  `hmi.set("MT1.LU1.SGLU2.UR2.State.Disable", false)` — восстановить

6.  `WAIT(60c)`

7.  `hmi.get("MT1.LU1.TI.DiffQmom")`


**Ожидаемый результат:**

*   Шаг 3: `LU1_DIFFQMOM.invalid = true` (или 0, зависит от реализации) — расчёт исключён

*   Шаг 4: `LU1_ALMDEVQMOM = false` (нет ложного аларма)

*   Шаг 7: `LU1_DIFFQMOM = 0.5` м³/ч (расчёт возобновлён)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-022 — Дебаланс: ручной ввод расхода (QVmomManual)**

**Требование:** R-HYDR-012, R-HYDR-033
**Описание:** Если расходомер даёт сбой, оператор задаёт значение вручную через `QVmomManual`. Система использует его вместо потокового `QVmom` при `Manual = true`.
**Формула:**

```
QVmom_расчёт = QVmomManual (если Manual = true)
QVmom_расчёт = QVmom (если Manual = false)
```

**Обоснование:**

*   Реальный `QVmom = 120.0` (занижает, СИКГ неисправен)

*   Оператор вводит `QVmomManual = 122.5` (правильное значение по расчёту)

*   При Manual=1: в расчёт уходит 122.5, а не 120.0


**Предусловие:**

*   `UR1` (выходной): `Disable = false`, `Manual = false`, `QVmom = 120.0`

*   `UR2` (входной): `Disable = false`, `Manual = false`, `QVmom = 122.0`

*   `LU1_CONTROL = 1`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.UR1.State.Manual", true)` — включить ручной режим

2.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmomManual", 122.5)`

3.  `WAIT(60c)`

4.  `hmi.get("MT1.LU1.TI.DiffQmom")`

5.  `hmi.set("MT1.LU1.SGLU1.UR1.State.Manual", false)` — выключить

6.  `WAIT(60c)`

7.  `hmi.get("MT1.LU1.TI.DiffQmom")`


**Ожидаемый результат:**

*   Шаг 4: `LU1_DIFFQMOM = 122.0 − 122.5 = −0.5` м³/ч (использован QVmomManual)

*   Шаг 7: `LU1_DIFFQMOM = 122.0 − 120.0 = 2.0` м³/ч (использован QVmom, Manual=false)


**Teardown:** `RESET()`

* * *

### 3.3 Стационарность и автопостановка

* * *

##### **HY-CALC-023 — KIP переходит в стационарный режим**

**Требование:** R-HYDR-016, R-HYDR-017
**Описание:** Датчик считается стационарным, если:

1.  `|Press − PressStationaryMode| ≤ DevMaxStation` (давление не скачет)

2.  Время с последнего скачка > `TimeIntSetStation` (120 с)


Стационарность — необходимое условие для автопостановки.
**Обоснование:**

*   `DevMaxStation = 0.5` МПа (из ИМ) — допустимое отклонение

*   `TimeIntSetStation = 120` с (из ИМ) — минимальное время стабильности

*   P = 5.0 МПа стабилен ±0.05 → отклонение 0.05 < 0.5 → условие 1 выполнено

*   После 120 с стабильности → условие 2 выполнено → Station = true


**Предусловие:**

*   `KIP1_PRESS = 5.0` МПа (стабилен)

*   `KIP1_PRESSSTATIONARYMODE = 5.0`

*   `KIP1_STATION = false` (ещё не перешёл)

*   `KIP1_DEVMAXSTATION = 0.5` (из ИМ)

*   `LU1_TIMEINTSETSTATION = 120` с (из ИМ)


**Действия:**

1.  Поддерживать `KIP1_PRESS = 5.0 ± 0.05` в течение 130 секунд (записи каждые 10 с через hmi-backend, имитация потока СДКУ)

2.  `WAIT(130c)` — 120 с стабильности + 10 с margin

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")`


**Ожидаемый результат:**

*   `KIP1_STATION = true`

*   `KIP1_PRESSSTATIONARYMODE` остаётся 5.0 (не обновляется, т.к. скачка не было)


**Примечание:** Для ускорения теста можно временно уменьшить `TimeIntSetStation` до 15 с через Redis (если допустимо изменять ИМ в тестовом стенде). В этом случае ожидание — 20 с.
**Teardown:** `RESET()`

* * *

##### **HY-CALC-024 — KIP выходит из стационарного режима (скачок)**

**Требование:** R-HYDR-016
**Описание:** Давление скакнуло и превысило `DevMaxStation` → датчик нестационарен. Система фиксирует новое эталонное давление (`PressStationaryMode`), обнуляя счётчик времени.
**Обоснование:**

*   `PressStationaryMode = 5.0`, `DevMaxStation = 0.5`

*   Скачок: P = 5.7 → `|5.7 − 5.0| = 0.7 > 0.5` → выход из стационарности

*   Новый `PressStationaryMode = 5.7`


**Предусловие:**

*   `KIP1_STATION = true`

*   `KIP1_PRESS = 5.0`, `KIP1_PRESSSTATIONARYMODE = 5.0`

*   `KIP1_DEVMAXSTATION = 0.5`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.7)` — скачок

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")`

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressStationaryMode")`


**Ожидаемый результат:**

*   `KIP1_STATION = false`

*   `KIP1_PRESSSTATIONARYMODE = 5.7` (обновлено на новое значение)

*   Для восстановления Station=true нужно 120 с стабильности на 5.7


**Teardown:** `RESET()`

* * *

##### **HY-CALC-025 — KIP нестационарен при невалидных данных**

**Требование:** R-HYDR-016
**Описание:** `invalid = true` → датчик автоматически нестационарен. При восстановлении — Station=false сохраняется, нужен новый период стабильности.
**Предусловие:**

*   `KIP1_STATION = true` до этого

*   Данные были валидны


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=true)`

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")`

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=false)` — восстановить

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_STATION = false`

*   Шаг 6: `KIP1_STATION = false` (не восстанавливается мгновенно — нужен новый 120-с период)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-026 — LU стационарен: все датчики стабильны**

**Требование:** R-HYDR-017
**Описание:** ТУ стационарен, если нестационарных < `CountKIPNoStation` и стационарных ≥ `LimitKIP`. Три зоны:
| Зона | Условие | Результат |
| --- | --- | --- |
| Достоверно стационарный | Нестационарных < CountKIPNoStation AND стационарных ≥ LimitKIP | true |
| Достоверно нестационарный | Нестационарных ≥ CountKIPNoStation | false |
| Недостаточно данных | Стационарных < LimitKIP (и нестационарных < порог) | false |

**Обоснование:**

*   5 KIP на ТУ1: все Station=true

*   `CountKIPNoStation = 2` (из ИМ): допустимо до 2 нестационарных

*   `LimitKIP = 2` (из ИМ): минимум 2 стационарных для уверенности

*   Нестационарных = 0 < 2, стационарных = 5 ≥ 2 → true


**Предусловие:**

*   Все 5 KIP: `Station = true`

*   `LU1_COUNTKIPNOSTATION = 2`

*   `LU1_LIMITKIP = 2`

*   `LU1_CONTROL = 0`, `LU1_AUTOCONTROLON = false`


**Действия:**

1.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Station")` — убедиться все true

2.  `WAIT(event)` — LuStationAlg

3.  `hmi.get("MT1.LU1.State.Station")`


**Ожидаемый результат:**

*   `LU1_STATION = true`

*   Если бы `AutoControlOn = true` и `Control = 0` → `LU1_CONTROLAUTOTIMELEFT` запустился бы отсчёт


**Teardown:** `RESET()`

* * *

##### **HY-CALC-027 — LU нестационарен: слишком много скачущих**

**Требование:** R-HYDR-017
**Описание:** Нестационарных ≥ `CountKIPNoStation` → ТУ достоверно нестационарен. Автопостановка блокируется.
**Обоснование:**

*   5 KIP: 3 нестационарны (KIP_A, B, C), 2 стационарны (D, E)

*   `CountKIPNoStation = 2`

*   3 ≥ 2 → false

*   Если `ControlAutoTimeLeft > 0` → сбрасывается на −1


**Предусловие:**

*   `KIP_A_STATION = false`, `KIP_B_STATION = false`, `KIP_C_STATION = false`

*   `KIP_D_STATION = true`, `KIP_E_STATION = true`

*   `LU1_COUNTKIPNOSTATION = 2`


**Действия:**

1.  Симулировать: на KIP_A/B/C `Press` прыгает ±0.6 МПа (превышает DevMaxStation = 0.5)

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.State.Station")`

4.  `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")` — если автопостановка была активна


**Ожидаемый результат:**

*   `LU1_STATION = false` (3 нестационарных ≥ 2)

*   Если `ControlAutoTimeLeft` было > 0 → теперь `−1`


**Teardown:** `RESET()`

* * *

##### **HY-CALC-028 — Автопостановка: полный цикл**

**Требование:** R-HYDR-025
**Описание:** Полный цикл автопостановки: включение → ожидание стационарности → отсчёт → автоматическая постановка на контроль.
**Последовательность:**

```
1. SetAutoControlOn = true → AutoControlOn = true
2. LU_STATION = false (нестабильно) → TimeLeft = −1
3. Давления стабилизируются → LU_STATION = true
4. TimeLeft = ControlAutoTimeOut (180 с)
5. Отсчёт: 180 → 179 → ... → 0 (каждый цикл 60с, т.е. 3 цикла)
6. TimeLeft = 0 → LuControlSetAlg → LU_CONTROL = 1
```

**Обоснование:**

*   `ControlAutoTimeOut = 180` с (из ИМ)

*   LuAutoControlTimeLeftAlg работает по POLL(60с): каждый цикл decrements на 60

*   Цикл 1: TimeLeft = 180 → 120

*   Цикл 2: TimeLeft = 120 → 60

*   Цикл 3: TimeLeft = 60 → 0 → срабатывание

*   Итого: ~180–240 секунд от стационарности до постановки


**Предусловие:**

*   `LU1_CONTROL = 0`

*   `LU1_STATION = false` (сначала нестабильно)

*   `LU1_AUTOCONTROLON = false`

*   `LU1_CONTROLAUTOTIMEOUT = 180` с


**Действия:**

1.  `hmi.set("MT1.LU1.TU.SetAutoControlOn", true)`

2.  `WAIT(event)` → проверить `AutoControlOn = true`

3.  Убедиться, что все KIP стабильны → `LU1_STATION = true`

4.  `WAIT(60c)` → цикл 1: TimeLeft = 180

5.  `WAIT(60c)` → цикл 2: TimeLeft = 120

6.  `WAIT(60c)` → цикл 3: TimeLeft = 60

7.  `WAIT(60c)` → цикл 4: TimeLeft = 0 → срабатывание

8.  `hmi.get("MT1.LU1.State.Control")`


**Ожидаемый результат:**

*   Шаг 2: `LU1_AUTOCONTROLON = true`

*   Шаг 4: `LU1_CONTROLAUTOTIMELEFT = 180` (или 120, зависит от момента)

*   Шаг 8: `LU1_CONTROL = 1` (автоматическая постановка)

*   `KIP1_PRESSSTATION` зафиксировано


**Примечание:** Для ускорения теста можно временно установить `ControlAutoTimeOut = 30` с через Redis. Тогда отсчёт: 30 → 0 за 1 цикл (60с).
**Teardown:** `RESET()`

* * *

##### **HY-CALC-029 — Отмена автопостановки**

**Требование:** R-HYDR-025
**Описание:** Диспетчер отменяет автопостановку во время отсчёта. TimeLeft = −2. При следующем Station=true → −1 (не выполняется).
**Предусловие:**

*   `LU1_AUTOCONTROLON = true`

*   `LU1_CONTROLAUTOTIMELEFT = 120` (идёт отсчёт)

*   `LU1_STATION = true`


**Действия:**

1.  `hmi.set("MT1.LU1.TU.SetAutoControlCancel", true)`

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`

4.  `hmi.get("MT1.LU1.TU.SetAutoControlCancel")`


**Ожидаемый результат:**

*   `LU1_CONTROLAUTOTIMELEFT = −2` (отменено)

*   `LU1_TU_SETAUTOCONTROLCANCEL = false` (сброшен)

*   При следующем Station=true → TimeLeft = −1 (автопостановка не выполняется)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-030 — Перезапуск таймера автопостановки** **[ИСПР]**

**Требование:** R-HYDR-025 (HYDRO-234)
**Описание:** Диспетчер сбрасывает таймер — система получает дополнительное время на стабилизацию.
**Предусловие:**

*   `LU1_AUTOCONTROLON = true`

*   `LU1_CONTROLAUTOTIMELEFT = 100` (осталось 100 с)

*   `LU1_CONTROLAUTOTIMEOUT = 180`


**Действия:**

1.  `hmi.set("MT1.LU1.TU.SetAutoControlReset", true)`

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`


**Ожидаемый результат:**

*   `LU1_CONTROLAUTOTIMELEFT = 180` (полный сброс, отсчёт заново)

*   `LU1_TU_SETAUTOCONTROLRESET = false` (сброшен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-031 — Снятие режима автопостановки**

**Требование:** R-HYDR-025
**Описание:** Полное отключение автопостановки. Таймер сбрасывается, флаг снимается. Control не изменяется.
**Предусловие:**

*   `LU1_AUTOCONTROLON = true`

*   `LU1_CONTROLAUTOTIMELEFT = 50` (идёт отсчёт)

*   `LU1_CONTROL = 0`


**Действия:**

1.  `hmi.set("MT1.LU1.TU.SetAutoControlOff", true)`

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.State.AutoControlOn")`

4.  `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`

5.  `hmi.get("MT1.LU1.State.Control")`


**Ожидаемый результат:**

*   `LU1_AUTOCONTROLON = false`

*   `LU1_CONTROLAUTOTIMELEFT = −1`

*   `LU1_CONTROL = 0` (без изменений)

*   `LU1_TU_SETAUTOCONTROLOFF = false` (сброшен)


**Teardown:** `RESET()`

* * *

### 3.4 Алармы давления

* * *

##### **HY-CALC-014 — Аларм выхода давления за верхнюю границу**

**Требование:** R-HYDR-028
**Описание:** На контроле система следит за давлением. Превышение верхней границы диапазона → аларм `AlmDevMaxRange`. Условие строгое (`>`), ровно на границе — аларма нет. Аларм генерируется при `Control=1 AND Disable=false`.
**Формула:**

```
Если Press > PressRangeMax → AlmDevMaxRange = true
```

**Обоснование значений:**

*   `PressStation = 5.0` МПа (зафиксировано при постановке)

*   `PressDeltaRangeMax = 0.2` МПа (из ИМ для данного KIP)

*   `PressRangeMax = 5.0 + 0.2 = 5.2` МПа

*   Тестируем: P = 5.3 → 5.3 > 5.2 → аларм

*   Возврат: P = 5.15 → 5.15 < 5.2 → сброс


**Предусловие:**

*   `LU1_CONTROL = 1` (на контроле)

*   `SGLU1_CONTROLON = true`

*   `KIP1_DISABLE = false`

*   `KIP1_PRESSSTATION = 5.0`

*   `KIP1_PRESSDELTARANGEMAX = 0.2` → `KIP1_PRESSRANGEMAX = 5.2`

*   `KIP1_PRESS = 5.0` (в диапазоне)

*   `KIP1_ALMDEVMAXRANGE = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)` — выше границы

2.  `WAIT(event)` — KipAlmDevRangeMaxMinAlg

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`

4.  `hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")` — подтвердить доставку

5.  `hmi.history("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange", from=ts_start, to=ts_now)` — проверить текст

6.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.15)` — вернуть в диапазон

7.  `WAIT(event)`

8.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_ALMDEVMAXRANGE = true` (5.3 > 5.2)

*   Шаг 4: `hmi.history` возвращает запись: value=true, text содержит «превышает максимальную границу», «5.2 МПа», «5.3 МПа»

*   Шаг 7: `KIP1_ALMDEVMAXRANGE = false` (5.15 < 5.2, сброшен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-015 — Аларм выхода давления за нижнюю границу**

**Требование:** R-HYDR-028
**Описание:** Давление упало ниже нижней границы диапазона. Риск кавитации, воздухонакопления. Условие строгое (`<`).
**Формула:**

```
Если Press < PressRangeMin → AlmDevMinRange = true
```

**Обоснование:**

*   `PressStation = 5.0`, `PressDeltaRangeMin = 0.1` → `PressRangeMin = 4.9`

*   Tестируем: P = 4.8 → 4.8 < 4.9 → аларм

*   Возврат: P = 4.92 → 4.92 > 4.9 → сброс


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `SGLU1_CONTROLON = true`

*   `KIP1_DISABLE = false`

*   `KIP1_PRESSSTATION = 5.0`

*   `KIP1_PRESSDELTARANGEMIN = 0.1` → `KIP1_PRESSRANGEMIN = 4.9`

*   `KIP1_PRESS = 5.0` (в диапазоне)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.8)` — ниже границы

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")`

4.  `hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")` — подтвердить доставку

5.  `hmi.history("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange", from=ts_start, to=ts_now)` — проверить текст

6.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.92)` — вернуть

7.  `WAIT(event)`

8.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_ALMDEVMINRANGE = true` (4.8 < 4.9)

*   Шаг 4: `hmi.history` возвращает запись: value=true, text содержит «ниже минимальной границы диапазона 4.9 МПа, текущее 4.8 МПа»

*   Шаг 7: `KIP1_ALMDEVMINRANGE = false` (сброшен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-016 — Давление ровно на границе диапазона: аларм не генерируется**

**Требование:** R-HYDR-028
**Описание:** Граничный случай: давление ровно на границе. Условие строгое (`>` / `<`). Это похоже защита от шума алармов при колебаниях вокруг границы.
**Предусловие:**

*   `LU1_CONTROL = 1`

*   `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9`

*   `KIP1_DISABLE = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.2)` — ровно верхняя

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.9)` — ровно нижняя

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_ALMDEVMAXRANGE = false` (5.2 = 5.2, условие `>` не выполнено)

*   Шаг 6: `KIP1_ALMDEVMINRANGE = false` (4.9 = 4.9, условие `<` не выполнено)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-017 — Аларм давления не генерируется без контроля (Control = 0)**

**Требование:** R-HYDR-028
**Описание:** Без контроля (Control=0) давление может быть каким угодно — алармы не генерируются. Нет базового состояния → нечего сравнивать.
**Предусловие:**

*   `LU1_CONTROL = 0`

*   `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9` (рассчитаны ранее, но неактивны)

*   `KIP1_PRESS = 5.5` (высоко, но без контроля не важно)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.5)`

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMinRange")`


**Ожидаемый результат:**

*   `KIP1_ALMDEVMAXRANGE = false`

*   `KIP1_ALMDEVMINRANGE = false`

*   Без контроля алармы не генерируются, даже при значительном отклонении


**Teardown:** `RESET()`

* * *

##### **HY-CALC-018 — Аларм давления не генерируется при отключённом датчике**

**Требование:** R-HYDR-028, R-HYDR-043
**Описание:** Отключённый датчик (`Disable = true`) не участвует в генерации алармов давления. Дополнительно: `KipAlarmsAlg` проверяет противоречие Disable/invalid → `AlmFailOn`.
**Два варианта AlmFailOn:**
| Disable | invalid | AlmFailOn | Пояснение |
| --- | --- | --- | --- |
| true | false | **true** | Противоречие: отключён, но получает валидные данные (ошибка конфигурации) |
| true | true | **false** | Штатно: отключён и данных нет |
| false | true | **true** | Сигнал пропал (обрыв, ошибка АЦП) |
| false | false | **false** | Штатная работа |

**Предусловие:**

*   `LU1_CONTROL = 1`

*   `SGLU1_CONTROLON = true`

*   `KIP1_DISABLE = true` (отключён)

*   `KIP1_PRESS = 5.5` (приходит, валидный — противоречие)


**Действия:**

1.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")` — проверить, что аларма давления нет

2.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")` — проверить диагностический

3.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", false)` — восстановить

4.  `WAIT(event)`

5.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")` — теперь должен быть (5.5 > 5.2)

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`


**Ожидаемый результат:**

*   Шаг 1: `KIP1_ALMDEVMAXRANGE = false` (датчик отключён, не участвует)

*   Шаг 2: `KIP1_ALMFAILON = true` (Disable=true, invalid=false → противоречие)

*   Шаг 5: `KIP1_ALMDEVMAXRANGE = true` (датчик активен, 5.5 > 5.2)

*   Шаг 6: `KIP1_ALMFAILON = false` (противоречие устраниено)


**Teardown:** `RESET()`


##### **HY-CALC-073 — Комбинированный аларм диапазона (KipPressRangeAlg)**

**Требование:** R-HYDR-028
**Описание:** `KipPressRangeAlg` (#9) генерирует комбинированный флаг `KIP_PRESSRANGEALARM` — `true` если давление вне диапазона (с любой стороны). В отличие от `KipAlmDevRangeMaxMinAlg` (#5), требует дополнительно `SGLU_CONTROLON = true`.
**Формула:**

```
Если (Control=1 AND Disable=0 AND SGLU_CONTROLON=true)
AND (Press > PressRangeMax OR Press < PressRangeMin)
→ KIP_PRESSRANGEALARM = true
```

**Предусловие:**

*   `LU1_CONTROL = 1`

*   `SGLU1_CONTROLON = true`

*   `KIP1_DISABLE = false`

*   `KIP1_PRESSSTATION = 5.0`, `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9`

*   `KIP1_PRESSRANGEALARM = false`


**Действия (часть 1: штатное срабатывание):**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)` — выше границы

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.8)` — ниже границы

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`

7.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — вернуть

8.  `WAIT(event)`

9.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`


**Действия (часть 2: SGLU_CONTROLON=false → аларм не генерируется):**

1.  `hmi.set("MT1.LU1.SGLU1.State.ControlOn", false)`

2.  `WAIT(event)`

3.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)`

4.  `WAIT(event)`

5.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`

6.  `hmi.set("MT1.LU1.SGLU1.State.ControlOn", true)` — восстановить


**Ожидаемый результат:**

*   Шаг 3: `KIP1_PRESSRANGEALARM = true` (5.3 > 5.2)

*   Шаг 6: `KIP1_PRESSRANGEALARM = true` (4.8 < 4.9)

*   Шаг 9: `KIP1_PRESSRANGEALARM = false` (5.0 в диапазоне)

*   Шаг 14: `KIP1_PRESSRANGEALARM = false` (SGLU_CONTROLON=false, хотя Press вне диапазона)


**Teardown:** `RESET()`

##### **HY-CALC-074 — Отклонение расхода (UrQVmomDeltaAlg)**

**Требование:** R-HYDR-029
**Описание:** Расчёт отклонения текущего расхода от базового. При `Manual=true` используется `QVmomManual` вместо потокового `QVmom`.
**Формула:**

```
QVmom_for_calc = Manual ? QVmomManual : QVmom
QVmomDelta = QVmom_for_calc − QVmomStation
```

**Предусловие:**

*   `LU1_CONTROL = 1`

*   `UR1_DISABLE = false`, `UR1_MANUAL = false`

*   `UR1_QVMOMSTATION = 120.0` (зафиксировано при Control=1)

*   `UR1_QVMOM = 120.0` (штатно, Delta = 0)

*   `UR1_QVMOMDELTA = 0.0`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 125.0)` — расход вырос

2.  `WAIT(event)` — UrQVmomDeltaAlg

3.  `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`

4.  `hmi.set("MT1.LU1.SGLU1.UR1.State.Manual", true)` — ручной режим

5.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmomManual", 123.0)`

6.  `WAIT(event)`

7.  `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`

8.  `hmi.set("MT1.LU1.SGLU1.UR1.State.Manual", false)` — выключить

9.  `WAIT(event)`

10.  `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`

11.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 118.0)` — расход упал

12.  `WAIT(event)`

13.  `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`

14.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0)` — вернуть

15.  `WAIT(event)`

16.  `hmi.get("MT1.LU1.SGLU1.UR1.TI.QVmomDelta")`


**Ожидаемый результат:**

*   Шаг 3: `UR1_QVMOMDELTA = 5.0` м³/ч (125.0 − 120.0)

*   Шаг 7: `UR1_QVMOMDELTA = 3.0` м³/ч (123.0 − 120.0, используется QVmomManual)

*   Шаг 10: `UR1_QVMOMDELTA = 5.0` м³/ч (125.0 − 120.0, Manual=false)

*   Шаг 13: `UR1_QVMOMDELTA = −2.0` м³/ч (118.0 − 120.0)

*   Шаг 16: `UR1_QVMOMDELTA = 0.0` м³/ч


**Teardown:** `RESET()`

##### **HY-CALC-075 — Дебаланс: реакция на 2-секундном цикле**

**Требование:** R-HYDR-033 **Описание:** `LuDiffQAlg` имеет два цикла: POLL(60с) для `DiffQavg` и POLL(2с) для `DiffQmom`. Проверяем что мгновенный дебаланс реагирует быстрее 60с.
**Предусловие:**

*   `LU1_CONTROL = 1`

*   `UR1` (выходной, км 0): `QVmom = 120.0`

*   `UR2` (входной, км 200): `QVmom = 120.5`

*   `LU1_DIFFQMOM = 0.5` (штатно)

*   `LU1_DIFFQMOMLIMITMAX = 1.5`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 125.0)` — резкий рост

2.  `WAIT(2c)` — максимум 7с (2с цикл + margin)

3.  `hmi.get("MT1.LU1.TI.DiffQmom")`

4.  `hmi.get("MT1.LU1.Alm.AlmDevQmom")`

5.  `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 120.5)` — вернуть

6.  `WAIT(2c)`

7.  `hmi.get("MT1.LU1.TI.DiffQmom")`

8.  `hmi.get("MT1.LU1.Alm.AlmDevQmom")`


**Ожидаемый результат:**

*   Шаг 3: `LU1_DIFFQMOM = 5.0` м³/ч (125.0 − 120.0)

*   Шаг 4: `LU1_ALMDEVQMOM = true` (5.0 > 1.5)

*   Шаг 7: `LU1_DIFFQMOM = 0.5` м³/ч

*   Шаг 8: `LU1_ALMDEVQMOM = false`


**Примечание:** Если `DiffQmom` обновляется только на 60с цикле (а не на 2с) — это несоответствие заявленному POLL(2с). Тест зафиксирует фактическое поведение.
**Teardown:** `RESET()`


##### **HY-CALC-076 — KIP_HEADSTATION: фиксация базового напора**


**Требование:** R-HYDR-022
**Описание:** При постановке на контроль (`Control=1`) фиксируется `KIP_HEADSTATION` — базовый напор. Он используется для расчёта `HeadDelta`. При снятии с контроля → `invalid`.

**Предусловие:**


*   `LU1_CONTROL = 0`

*   `KIP1_PRESS = 5.0`, `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`

*   `KIP1_HEAD = 663.2` (рассчитан)



**Действия:**


1.  `hmi.set("MT1.LU1.TU.SetControlOn", true)`

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadStation")`

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)` — изменить давление

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadStation")` — не должно измениться

7.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadDelta")` — должно быть ≠ 0

8.  `hmi.set("MT1.LU1.TU.SetControlOff", true)`

9.  `WAIT(event)`

10.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadStation")` — invalid



**Ожидаемый результат:**


*   Шаг 3: `KIP1_HEADSTATION = 663.2` м (зафиксировано)

*   Шаг 6: `KIP1_HEADSTATION = 663.2` м (не обновляется при изменении Press)

*   Шаг 7: `KIP1_HEADDELTA = 36.1` м (699.3 − 663.2)

*   Шаг 10: `KIP1_HEADSTATION.invalid = true`



**Teardown:** `RESET()`



##### **HY-CALC-077 — KIP_ALMGRAVITYPOSSIBLE: напор близок к высоте в конфигурации**


**Требование:** R-HYDR-035
**Описание:** На уровне высоты конкретного датчика: если `Head_KIP − GravityPossible < H_конфигурации` на этом км → аларм на датчике. Это более точечное предупреждение, чем `LU_ALMGRAVITYPOSSIBLE`.

**Предусловие:**


*   Конфигурация ТУ1: пик км 65, H = 400 м

*   KIP2 (км 80): `H = 300 м`, `Ro = 850`

*   `LU1_GRAVITYPOSSIBLE = 50` м

*   KIP2: `Press = 0.85` → `Head = 402.0 м`

*   `Head − GravityPossible = 402.0 − 50 = 352.0 < 400` → риск



**Действия:**


1.  `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.85)`

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU2.KIP2.Alm.AlmGravityPossible")`

4.  `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 2.0)` — поднять

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU2.KIP2.Alm.AlmGravityPossible")`



**Ожидаемый результат:**


*   Шаг 3: `KIP2_ALMGRAVITYPOSSIBLE = true` (352 < 400)

*   Шаг 6: `KIP2_ALMGRAVITYPOSSIBLE = false` (Head = 539.9, 539.9 − 50 = 489.9 > 400)



**Teardown:** `RESET()`

##### **HY-CALC-078 — PLTM_ALMROINVALID: невалидная плотность**

**Требование:** R-HYDR-043
**Описание:** Если `PLTM_RO.invalid = true` при `PLTM_DISABLE = false` → аларм достоверности `AlmRoInvalid`. Аналог `KIP_ALMFAILON` для плотномера.
**Предусловие:**

*   `PLTM1_DISABLE = false`

*   `PLTM1_RO = 850` (валидный)

*   `PLTM1_ALMROINVALID = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.PLT1.TI.Ro", 850, invalid=true)`

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.PLT1.Alm.AlmRoInvalid")`

4.  `hmi.set("MT1.LU1.SGLU1.PLT1.TI.Ro", 850, invalid=false)`

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.PLT1.Alm.AlmRoInvalid")`


**Ожидаемый результат:**

*   Шаг 3: `PLTM1_ALMROINVALID = true`

*   Шаг 6: `PLTM1_ALMROINVALID = false`


**Teardown:** `RESET()`

##### **HY-CALC-079 — UR_ALMQVMOMINVALID: невалидный расход**

**Требование:** R-HYDR-043 **Описание:** Если `UR_QVMOM.invalid = true` при `UR_DISABLE = false` → флаг `AlmQVmomInvalid`. Невалидный расход исключается из расчёта дебаланса.
**Предусловие:**

*   `UR1_DISABLE = false`

*   `UR1_QVMOM = 120.0` (валидный)

*   `UR1_ALMQVMOMINVALID = false`

*   `LU1_CONTROL = 1`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0, invalid=true)`

2.  `WAIT(2c)`

3.  `hmi.get("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomInvalid")`

4.  `hmi.get("MT1.LU1.TI.DiffQmom")` — должен стать invalid (нет выходного расхода)

5.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 120.0, invalid=false)`

6.  `WAIT(2c)`

7.  `hmi.get("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomInvalid")`

8.  `hmi.get("MT1.LU1.TI.DiffQmom")` — восстановлен


**Ожидаемый результат:**

*   Шаг 3: `UR1_ALMQVMOMINVALID = true`

*   Шаг 4: `LU1_DIFFQMOM.invalid = true` (нет данных)

*   Шаг 7: `UR1_ALMQVMOMINVALID = false`

*   Шаг 8: `LU1_DIFFQMOM` восстановлен (0.5)


**Teardown:** `RESET()`

##### **HY-CALC-080 — KIP_ROSCHEDULE: плановая плотность**

**Требование:** R-HYDR-009
**Описание:** В контексте плана перекачки система рассчитывает плановую плотность для каждого KIP. `KIP_ROSCHEDULE` используется для прогноза напора в плановом режиме.
**Предусловие:**

*   `LU1_TI.ARMTPumpPlan` содержит JSON плана с плотностью

*   Текущий режим: «Нормальный», `RoSchedule = 850`

*   `KIP1_ROSCHEDULE` — пуст или устаревшее


**Действия:**

1.  `WAIT(60c)` — скан планера

2.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.RoSchedule")`

3.  Сменить режим на «Ночной» (где `RoSchedule = 860`)

4.  `WAIT(60c)`

5.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.RoSchedule")`


**Ожидаемый результат:**

*   Шаг 2: `KIP1_ROSCHEDULE = 850` кг/м³

*   Шаг 5: `KIP1_ROSCHEDULE = 860` кг/м³


**Teardown:** `RESET()`


* * *

### 3.5 Алармы расхода, связи и индикаторы

* * *

##### **HY-CALC-032 — Отклонение по двум и более смежным датчикам**

**Требование:** R-HYDR-030, R-HYDR-021 (HYDRO-232, HYDRO-91)
**Описание:** Если 2+ датчика на одном SGLU одновременно имеют `AlmDevMaxRange` или `AlmDevMinRange` → аларм на уровне ТУ `AlmPressDev`. Это более надёжный признак, чем одиночный.
**Связь с индикатором:**

*   Одиночное отклонение (1 KIP) → `IndicatorControl = 2` (жёлтый)

*   Смежное (2+ KIP) → `IndicatorControl = 3` (красный)


**Обоснование:**

*   3 KIP на SGLU1: KIP1, KIP2, KIP3

*   Все на контроле, PressStation = 5.0, RangeMax = 5.2

*   KIP1: Press = 5.3 → AlmDevMaxRange = true (одиночное)

*   KIP2: Press = 5.35 → AlmDevMaxRange = true (второй на том же SGLU)

*   2 ≥ 2 → AlmPressDev = true


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `SGLU1_CONTROLON = true`

*   KIP1, KIP2, KIP3 на SGLU1: `Disable = false`, `PressStation = 5.0`, `PressRangeMax = 5.2`

*   KIP1: `Press = 5.3` → `AlmDevMaxRange = true`

*   KIP2: `Press = 5.0` (штатно)

*   KIP3: `Press = 5.0` (штатно)

*   `LU1_ALMPRESSDEV = false`

*   `LU1_INDICATORCONTROL = 2` (одиночное отклонение)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.35)` — второй датчик выходит

2.  `WAIT(event)` — LuAlmPressDevAlg

3.  `hmi.get("MT1.LU1.Alm.AlmPressDev")`

4.  `hmi.get("MT1.LU1.State.IndicatorControl")`

5.  `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.0)` — вернуть

6.  `WAIT(event)`

7.  `hmi.get("MT1.LU1.Alm.AlmPressDev")`

8.  `hmi.get("MT1.LU1.State.IndicatorControl")`


**Ожидаемый результат:**

*   Шаг 3: `LU1_ALMPRESSDEV = true` (2 смежных с отклонением)

*   Шаг 4: `LU1_INDICATORCONTROL = 3` (красный)

*   Шаг 7: `LU1_ALMPRESSDEV = false`

*   Шаг 8: `LU1_INDICATORCONTROL = 2` (вернулся к одиночному)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-033 — Превышение скорости изменения давления (гидроудар)**

**Требование:** R-HYDR-034 R-HYDR-005
**Описание:** Гидроудар — резкий рост давления. Система следит за скоростью: если количество KIP с `V > PressRateLimit` ≥ `PressRateKiplimit` → аларм на ТУ.
**Формула (алгоритм 1):**

```
V = (P_кон − P_нач) / T
```

**Обоснование:**

*   `PressRateLimit = 0.05` МПа/мин (из ИМ) — порог

*   `PressRateKiplimit = 1` (из ИМ) — минимум 1 датчик с превышением

*   KIP1: P растёт с 5.0 до 5.4 за 30 с = 0.5 мин → V = 0.4/0.5 = **0.8 МПа/мин** >> 0.05

*   KIP2: аналогично → V = 0.8 МПа/мин

*   Count = 2 ≥ 1 → аларм


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `LU1_PRESSRATELIMIT = 0.05` МПа/мин (из ИМ)

*   `LU1_PRESSRATEKIPLIMIT = 1` (из ИМ)

*   `LU1_PRESSRATEALGORITHM = 1` (двухточечный)

*   KIP1, KIP2: `Press = 5.0` (стабильно, история накоплена)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.4)` — резкий рост KIP1

2.  `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.4)` — резкий рост KIP2

3.  `WAIT(60c)` — KipPressRateAlg по циклу рассчитывает скорость

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressRate")`

5.  `hmi.get("MT1.LU1.SGLU1.KIP2.TI.PressRate")`

6.  `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")`

7.  `hmi.wait_alarm("MT1.LU1.Alm.AlmRateLimitPress")` — подтвердить доставку

8.  `hmi.history("MT1.LU1.Alm.AlmRateLimitPress", from=ts_start, to=ts_now)` — проверить текст

9.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — стабилизировать

10.  `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.0)`

11.  `WAIT(60c)`

12.  `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")`


**Ожидаемый результат:**

*   Шаг 4: `KIP1_PRESSRATE ≈ 0.8` МПа/мин (> 0.05)

*   Шаг 5: `KIP2_PRESSRATE ≈ 0.8` МПа/мин

*   Шаг 6: `LU1_ALMPRESSRATELIMIT = true` (2 ≥ 1)

*   Шаг 7: `hmi.history` возвращает запись: value=true, text содержит «скорость нарастания давления превышает допустимую (0.05 МПа/мин) на 2 датчиках»

*   Шаг 11: `LU1_ALMPRESSRATELIMIT = false` (сброшен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-034 — Аларм расхода: выход за границы коридора**

**Требование:** R-HYDR-029
**Описание:** Расходомер проверяет: не отклоняется ли расход от базового значения более чем на дельту. В отличие от дебаланса — здесь сравнивается один расходомер со своим базовым значением.
**Формула:**

```
Если QVmom > QVmomStation + QVmomDeltaRangeMax → AlmQVmomRangeMax = true
Если QVmom < QVmomStation + QVmomDeltaRangeMin → AlmQVmomRangeMin = true
```

**Обоснование:**

*   `QVmomStation = 120.0` м³/ч (зафиксировано при Control=1)

*   `QVmomDeltaRangeMax = 5.0` м³/ч (из ИМ) → верхняя граница = 125.0

*   `QVmomDeltaRangeMin = −5.0` м³/ч (из ИМ) → нижняя граница = 115.0

*   Tестируем: QVmom = 127.0 > 125.0 → аларм Max

*   Возврат: QVmom = 124.0 < 125.0 → сброс


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `SGLU1_CONTROLON = true`

*   `UR1_DISABLE = false`

*   `UR1_QVMOMSTATION = 120.0`

*   `UR1_QVMOMDELTARANGEMAX = 5.0` (из ИМ)

*   `UR1_QVMOMDELTARANGEMIN = −5.0` (из ИМ)

*   `UR1_QVMOM = 120.0` (норма)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 127.0)` — выше границы

2.  `WAIT(event)` — UrAlmDevRangeMaxMinAlg

3.  `hmi.get("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomRangeMax")`

4.  `hmi.wait_alarm("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomRangeMax")` — подтвердить доставку

5.  `hmi.history("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomRangeMax", from=ts_start, to=ts_now)` — проверить текст

6.  `hmi.set("MT1.LU1.SGLU1.UR1.TI.QVmom", 124.0)` — вернуть

7.  `WAIT(event)`

8.  `hmi.get("MT1.LU1.SGLU1.UR1.Alm.AlmQVmomRangeMax")`


**Ожидаемый результат:**

*   Шаг 3: `UR1_ALMQVMOMRANGEMAX = true` (127 > 125)

*   Шаг 4:
    `hmi.history` возвращает запись: value=true, text содержит «расход превышает верхнюю границу 125.0 м³/ч, текущий 127.0 м³/ч»

*   Шаг 7: `UR1_ALMQVMOMRANGEMAX = false` (сброшен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-035 — Потеря связи со всеми датчиками**

**Требование:** R-HYDR-038, R-HYDR-020
**Описание:** Все датчики теряют связь → `CounterKIP = 0` → аларм `AlmKIPAllLink`, индикатор связи = 2.

> **Важно:** `LuCounterKipAlg` считает датчики по **валидности** `KIP_PRESS` (не invalid, не NaN, не Infinity). «Потеря связи» = `KIP_PRESS.invalid = true`.

**Предусловие:**

*   5 KIP на ТУ1: KIP1–KIP5, все `Press` валидны

*   `LU1_COUNTERKIP = 5`

*   `LU1_LIMITKIP = 3` (из ИМ)

*   `LU1_INDICATORLINK = 0`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=true)`

2.  `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.0, invalid=true)`

3.  `hmi.set("MT1.LU1.SGLU1.KIP3.TI.Press", 5.0, invalid=true)`

4.  `hmi.set("MT1.LU1.SGLU2.KIP4.TI.Press", 5.0, invalid=true)`

5.  `hmi.set("MT1.LU1.SGLU2.KIP5.TI.Press", 5.0, invalid=true)`

6.  `WAIT(2c)` — LuCounterKipAlg (каждые 2 с)

7.  `hmi.get("MT1.LU1.State.CounterKIP")`

8.  `hmi.get("MT1.LU1.Alm.AlmKIPAllLink")`

9.  `hmi.get("MT1.LU1.State.IndicatorLink")`

10.  Восстановить все: `invalid=false` для всех 5

11.  `WAIT(2c)`

12.  `hmi.get("MT1.LU1.State.CounterKIP")`

13.  `hmi.get("MT1.LU1.State.IndicatorLink")`


**Ожидаемый результат:**

*   Шаг 7: `LU1_COUNTERKIP = 0`

*   Шаг 8: `LU1_ALMKIPALLLINK = true`

*   Шаг 9: `LU1_INDICATORLINK = 2` (красный)

*   Алармы давления не генерируются (нет валидных данных)

*   Шаг 12: `LU1_COUNTERKIP = 5`

*   Шаг 13: `LU1_INDICATORLINK = 0` (норма)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-036 — Датчиков на связи меньше нормы**

**Требование:** R-HYDR-038, R-HYDR-020
**Описание:** `0 < CounterKIP < LimitKIP` → аларм `AlmKIPCountLink`, индикатор = 1 (жёлтый).
**Обоснование:**

*   5 KIP, `LimitKIP = 3`

*   Теряем 3 → `CounterKIP = 2 < 3` → аларм

*   Но > 0 → не критический (не AllLink)


**Предусловие:**

*   5 KIP, все валидны, `CounterKIP = 5`, `LimitKIP = 3`


**Действия:**

1.  Установить `invalid=true` на 3 KIP (KIP1, KIP2, KIP3)

2.  `WAIT(2c)`

3.  `hmi.get("MT1.LU1.State.CounterKIP")`

4.  `hmi.get("MT1.LU1.Alm.AlmKIPCountLink")`

5.  `hmi.get("MT1.LU1.State.IndicatorLink")`

6.  Восстановить 2 KIP (KIP1, KIP2) → `CounterKIP = 4 ≥ 3`

7.  `WAIT(2c)`

8.  `hmi.get("MT1.LU1.State.IndicatorLink")`


**Ожидаемый результат:**

*   Шаг 3: `LU1_COUNTERKIP = 2`

*   Шаг 4: `LU1_ALMKIPCOUNTLINK = true`

*   Шаг 5: `LU1_INDICATORLINK = 1` (жёлтый)

*   Шаг 8: `LU1_INDICATORLINK = 0` (4 ≥ 3, норма)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-037 — Индикатор контроля: все значения (0–5)**

**Требование:** R-HYDR-021 (HYDRO-91)
**Описание:** Индикатор контроля — одно число (0–5), однозначно описывающее ситуацию. Проверяем все 6 значений последовательно.
**Таблица:**
| Значение | Имя | Цвет | Условие |
| --- | --- | --- | --- |
| 0 | ControlOn | Зелёный | Control = 0 |
| 1 | Norm | Зелёный | Control = 1, всё штатно |
| 2 | LonesomeKipAlarmed | Жёлтый | Control = 1, AlmDevMax/Min = true, AlmPressDev = false |
| 3 | RangedKipAlarmed | Красный | Control = 1, AlmPressDev = true |
| 4 | ControlAutoTimeLeft | Оранжевый | ControlAutoTimeLeft > 0 |
| 5 | TransitionOn | Красный | Control = 2 |

**Приоритет (высший → низший):** 5 > 4 > 3 > 2 > 1 > 0
**Предусловие:**

*   ТУ1 с 3 KIP, конфигурация загружена


**Действия (последовательная проверка всех 6 состояний):**
| Шаг | Действие | Ожидаемый IndicatorControl |
| --- | --- | --- |
| 1 | `Control = 0`, `AutoControlOn = false`, `TimeLeft = −1` | **0** |
| 2 | `AutoControlOn = true`, `Station = true`, `Control = 0` → TimeLeft = 180 | **4** |
| 3 | `SetAutoControlOff` → TimeLeft = −1. `Control = 1`, KIP2 Press = 5.35 (AlmPressDev = true) | **3** |
| 4 | KIP2 Press = 5.0 (AlmPressDev = false), KIP1 Press = 5.3 (AlmDevMax = true) | **2** |
| 5 | KIP1 Press = 5.0 (всё штатно) | **1** |
| 6 | `SetControlOff` → Control = 0. `TransitionControlOn = true` → Control = 2 | **5** |

**Ожидаемый результат:**

*   Каждый шаг даёт соответствующее значение `LU1_INDICATORCONTROL`

*   Приоритет соблюдается: если одновременно Control=2 и TimeLeft>0 → 5 (не 4)


**Teardown:** `RESET()`

* * *

### 3.6 Самотеки и достоверность

* * *

##### **HY-CALC-038 — Самотечный участок обнаружен**

**Требование:** R-HYDR-018, R-HYDR-035
**Описание:** На горном участке ТУ жидкость не преодолевает перевал за счёт напора — сегмент ниже перевала работает в самотёчном режиме. Система обнаруживает самотеки: находит перевальные точки (пики конфигурации ТУ) и проверяет, не опускается ли линия напора ниже конфигурации.
**Логика алгоритма:**

```
1. Найти пики конфигурации ТУ (максимальные высоты локально)
2. Для каждого сегмента между KIP:
   Если Head_KIP < H_peak_сегмента → сегмент самотечный
3. Записать в GravitySegs (пары км), PassPoints (координаты перевалов)
4. Сгенерировать аларм AlmGravity
```

**Обоснование значений (горный участок):**

*   Конфигурация ТУ1: пик на км 65, **H_peak = 400 м** (горный хребет)

*   KIP1 (км 50): H = 350 м

*   KIP2 (км 80): H = 300 м

*   Для самотека: `Head_KIP2 < H_peak = 400 м`

*   При P = 0.5 МПа, Ro = 850: `Head = (0.5/850)×101970 + 300 = 59.9 + 300 = 359.9 м < 400` → **самотек**

*   При P = 2.0 МПа: `Head = (2.0/850)×101970 + 300 = 239.9 + 300 = 539.9 м > 400` → **не самотек**


**Предусловие:**

*   Конфигурация ТУ1: `LU_KM = [0, 50, 65, 80, 100, 200]`, `LU_HEIGHT = [300, 350, 400, 300, 280, 250]`

*   Пик: км 65, H = 400 м

*   KIP1 (км 50): `Ro = 850`, `H = 350 м`

*   KIP2 (км 80): `Ro = 850`, `H = 300 м`

*   `LU1_ALMGRAVITY = false` (до начала теста)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 3.0)` — KIP1 высоко (Head = 709.5 > 400)

2.  `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.5)` — KIP2 низко (Head = 359.9 < 400)

3.  `WAIT(event)` — LuGravitySegsAlg

4.  `hmi.get("MT1.LU1.Alm.AlmGravity")`

5.  `hmi.get("MT1.LU1.TI.GravitySegs")`

6.  `hmi.get("MT1.LU1.TI.PassPoints")`

7.  `hmi.wait_alarm("MT1.LU1.Alm.AlmGravity")` — подтвердить доставку

8.  `hmi.history("MT1.LU1.Alm.AlmGravity", from=ts_start, to=ts_now)` — проверить текст

9.  `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 2.0)` — поднять напор (Head = 539.9 > 400)

10.  `WAIT(event)`

11.  `hmi.get("MT1.LU1.Alm.AlmGravity")`


**Ожидаемый результат:**

*   Шаг 4: `LU1_ALMGRAVITY = true`

*   Шаг 5: `LU1_GRAVITYSEGS = ["50,80"]` (сегмент км 50–80 самотечный)

*   Шаг 6: `LU1_PASSPOINTS = [65]` (перевал на км 65)

*   Шаг 7: `hmi.history` возвращает запись: value=true, text содержит «самотечный участок км 50–80, перевальная точка на км 65»

*   Шаг 10: `LU1_ALMGRAVITY = false` (напор восстановлен, самотек устранён)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-039 — Возможность самотека: прогнозируемый риск**

**Требование:** R-HYDR-019, R-HYDR-035
**Описание:** Система предупреждает заранее — до того, как самотек станет реальностью. `GravityPossible` — запас (в метрах), определяющий «насколько близко напор к конфигурации ТУ». Если `Head − GravityPossible < H_peak` → предупреждение.
**Формула:**

```
Head_possible = Head − GravityPossible
Если Head_possible < H_peak_сегмента → AlmGravityPossible = true
```

**Обоснование:**

*   При Head = 420, H_peak = 400, GravityPossible = 50:

*   Head = 420 > 400 → **не самотек** (реального перевала нет)

*   Head_possible = 420 − 50 = 370 < 400 → **риск** (если напор упадёт на 50 м — будет самотек)


**Обоснование расчетов:**

*   KIP2: P = 0.85 МПа, Ro = 850, H = 300 → `Head = (0.85/850)×101970 + 300 = 102.0 + 300 = 402.0 м`

*   H_peak = 400 → Head = 402 > 400 (чуть выше, самотека нет)

*   GravityPossible = 50 → `Head_possible = 402 − 50 = 352 < 400` → риск


**Предусловие:**

*   Конфигурация как в HY-CALC-038 (пик км 65, H = 400 м)

*   `LU1_GRAVITYPOSSIBLE = 50` м (из ИМ)

*   KIP1 (км 50): `Press = 3.0` (Head = 709.5, высоко)

*   KIP2 (км 80): `Press = 0.85` (Head = 402.0, чуть выше пика)

*   `LU1_ALMGRAVITY = false` (реального самотека нет)

*   `LU1_ALMGRAVITYPOSSIBLE = false` (до начала)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 3.0)`

2.  `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.85)`

3.  `WAIT(event)`

4.  `hmi.get("MT1.LU1.Alm.AlmGravity")`

5.  `hmi.get("MT1.LU1.Alm.AlmGravityPossible")`

6.  `hmi.get("MT1.LU1.TI.PassPointsPossible")`

7.  `hmi.wait_alarm("MT1.LU1.Alm.AlmGravityPossible")` — подтвердить доставку

8.  `hmi.history("MT1.LU1.Alm.AlmGravityPossible", from=ts_start, to=ts_now)` — проверить текст

9.  `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 2.0)` — поднять (Head = 539.9 >> 400)

10.  `WAIT(event)`

11.  `hmi.get("MT1.LU1.Alm.AlmGravityPossible")`


**Ожидаемый результат:**

*   Шаг 4: `LU1_ALMGRAVITY = false` (Head = 402 > 400, реального самотека нет)

*   Шаг 5: `LU1_ALMGRAVITYPOSSIBLE = true` (Head − 50 = 352 < 400, риск)

*   Шаг 6: `LU1_PASSPOINTSPOSSIBLE = [65]`

*   Шаг 7: `hmi.history` возвращает запись: value=true, text содержит «риск перехода в самотечный режим, перевальная точка на км 65»

*   Шаг 10: `LU1_ALMGRAVITYPOSSIBLE = false` (риск устранён)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-040 — Аларм достоверности: пропал сигнал (invalid)**

**Требование:** R-HYDR-043
**Описание:** Датчик выдаёт невалидные данные (`invalid = true`) при `Disable = false` — сигнал пропал. `KipAlarmsAlg` генерирует `AlmFailOn`. Невалидные данные не используются для расчёта напора и алармов давления.
**Предусловие:**

*   `KIP1_DISABLE = false`

*   `KIP1_PRESS = 5.0` (валидный)

*   `KIP1_ALMFAILON = false`

*   `KIP1_HEAD = 663.2` (рассчитан)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=true)` — пропал сигнал

2.  `WAIT(event)` — KipAlarmsAlg

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` — проверить invalid

5.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0, invalid=false)` — восстановить

6.  `WAIT(event)`

7.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_ALMFAILON = true` (Disable=false, invalid=true → сигнал пропал)

*   Шаг 4: `KIP1_HEAD.invalid = true` (напор не рассчитывается по невалидным данным)

*   Шаг 7: `KIP1_ALMFAILON = false` (сброшен при восстановлении)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-041 — Аларм достоверности: отключён, но данные валидны**

**Требование:** R-HYDR-043
**Описание:** Датчик отключён (`Disable = true`), но данные всё ещё приходят и помечены валидными (`invalid = false`). Противоречие — ошибка конфигурации или оператор забыл остановить поток. `AlmFailOn = true`.
**Предусловие:**

*   `KIP1_DISABLE = true` (отключён)

*   `KIP1_PRESS = 5.0` (приходит, валидный)

*   `KIP1_ALMFAILON = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", true)` — отключить

2.  `WAIT(event)` — KipAlarmsAlg

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", false)` — восстановить

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_ALMFAILON = true` (Disable=true, invalid=false → противоречие)

*   Шаг 6: `KIP1_ALMFAILON = false` (сброшен)


**Teardown:** `RESET()`

* * *

### 3.7 Дополнительные расчёты

* * *

##### **HY-CALC-042 — Скорость изменения давления: алгоритм 1 (двухточечный)**

**Требование:** R-HYDR-005
**Описание:** Берутся два последних значения давления, разница делится на разницу времени. Работает мгновенно, но чувствителен к единичным выбросам.
**Формула:**

```
V = (P_кон − P_нач) / T_мин
```

**Обоснование:**

*   P_нач = 5.0 МПа (t = 0)

*   P_кон = 5.5 МПа (t = 60 с = 1 мин)

*   V = (5.5 − 5.0) / 1 = **0.5 МПа/мин**

*   Порог: 0.05 МПа/мин → 0.5 >> 0.05 → превышение

*   Граничный: менее 2 точек → invalid


**Предусловие:**

*   `LU1_PRESSRATEALGORITHM = 1` (двухточечный, из ИМ)

*   `LU1_PRESSRATEKIPINTERVAL = 60` с

*   `KIP1_PRESS = 5.0` (стабильно, история ≥ 2 точек)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.5)` — скачок за 1 цикл

2.  `WAIT(60c)` — KipPressRateAlg по циклу

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressRate")`

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — стабилизировать

5.  `WAIT(60c)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressRate")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_PRESSRATE ≈ 0.5` МПа/мин

*   Шаг 6: `KIP1_PRESSRATE ≈ 0.0` МПа/мин (стабильно)


**Граничные случаи [НИЗКИЙ ПРИОРИТЕТ]:**
| # | Сценарий | Ожидаемое |
| --- | --- | --- |
| 1 | Первая запись Press (0 точек истории) | `KIP1_PRESSRATE.invalid = true` |
| 2 | Одна точка (не хватает пары) | `KIP1_PRESSRATE.invalid = true` |
| 3 | Два значения с одинаковым timestamp (t1 = t2) | `KIP1_PRESSRATE = 0` или `invalid` (не NaN/Inf). Зафиксировать |
| 4 | `PressRateKIPInterval = 0` (через Redis) | `KIP1_PRESSRATE.invalid = true` или лог ошибка. Система не упала |

**Teardown:** `RESET()`

* * *

##### **HY-CALC-043 — Скорость изменения давления: алгоритм 2 (МНК)**

**Требование:** R-HYDR-005 (HYDRO-206)
**Описание:** МНК-аппроксимация серии значений. Устойчивее к выбросам: одиночный сбой датчика не искажает результат.
**Формула (МНК, наклон a):**

```
a = (N·Σ(Pi·ti) − ΣPi·Σti) / (N·Σti² − (Σti)²)
```

**Обоснование (линейный рост):**

*   Серия: P(0)=5.0, P(15)=5.1, P(30)=5.2, P(45)=5.3, P(60)=5.4

*   N = 5

*   Σti = 0+15+30+45+60 = 150

*   Σti² = 0+225+900+2025+3600 = 6750

*   ΣPi = 5.0+5.1+5.2+5.3+5.4 = 26.0

*   Σ(Pi·ti) = 0+76.5+156+238.5+324 = 795

*   a = (5×795 − 26.0×150) / (5×6750 − 150²) = (3975 − 3900) / (33750 − 22500) = 75 / 11250 = **0.00667 МПа/с** = **0.4 МПа/мин**


**Сравнение с выбросом (P(30) = 5.7 вместо 5.2):**

*   ΣPi = 5.0+5.1+5.7+5.3+5.4 = 26.5

*   Σ(Pi·ti) = 0+76.5+171+238.5+324 = 810

*   a = (5×810 − 26.5×150) / (5×6750 − 22500) = (4050 − 3975) / 11250 = 75/11250 = **0.4 МПа/мин**

*   Алгоритм 1 дал бы: (5.7−5.1)/15×60 = 2.4 МПа/мин → МНК сгладил выброс


**Предусловие:**

*   `LU1_PRESSRATEALGORITHM = 2` (МНК, из ИМ)

*   `LU1_PRESSRATEKIPINTERVAL = 60` с

*   `LU1_PRESSRATEHISTORYMAXCOUNT = 50` (из ИМ)


**Действия:**

1.  Записать серию: P(0)=5.0, P(15)=5.1, P(30)=5.2, P(45)=5.3, P(60)=5.4 (записи с интервалом 15 с)

2.  `WAIT(60c)` — KipPressRateAlg по циклу

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressRate")`

4.  Записать выброс: P(75)=5.7, затем P(90)=5.4, P(105)=5.5, P(120)=5.6

5.  `WAIT(60c)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressRate")` — должен остаться ~0.4


**Ожидаемый результат:**

*   Шаг 3: `KIP1_PRESSRATE ≈ 0.4` МПа/мин (линейный рост)

*   Шаг 6: `KIP1_PRESSRATE ≈ 0.4` МПа/мин (выброс сглажен МНК)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-044 — Фильтрация конфигурации ТУ: удаление артефактов**

**Требование:** R-HYDR-014
**Описание:** При загрузке конфигурации ТУ система очищает массивы от артефактов:

1.  **Дубли** — одинаковые km → удалить одну точку

2.  **Шум** — отклонение от линейной интерполяции соседей < 0.001 м → удалить

3.  **Частота** — расстояние < 1/3000 от длины ТУ → удалить


Крайние точки (первая и последняя) **всегда сохраняются**.
**Обоснование:**

*   Длина ТУ = 25 км → порог частоты: 25/3000 = 0.00833 км

*   Точка (10.0001, 62.0005): расстояние до (10, 62) = 0.0001 км < 0.00833 → удалить

*   Точка (10.0002, 62.0008): отклонение от линии (10,62)→(15,63): ожидаемое H = 62 + (63−62)×(10.0002−10)/(15−10) = 62 + 0.00004 ≈ 62.00004. Факт = 62.0008. Отклонение = 0.00076 < 0.001 → удалить (шум)


**Предусловие:**

*   `LU1_KM = [0, 10, 10.0001, 10.0002, 15, 20, 20, 25]` км (с артефактами)

*   `LU1_HEIGHT = [60, 62, 62.0005, 62.0008, 63, 65, 65, 68]` м

*   `LU1_PMAXDEFAULT = [6.0, 6.1, 6.1, 6.1, 6.2, 6.3, 6.3, 6.4]` МПа


**Действия:**

1.  Загрузить конфигурацию ТУ1 в data-manager (PostgreSQL/Redis)

2.  `WAIT(60c)` — LuDataThinningAlg по циклу

3.  `hmi.get("MT1.LU1.TI.KM")`

4.  `hmi.get("MT1.LU1.TI.Height")`

5.  `hmi.get("MT1.LU1.TI.PmaxDefault")`


**Ожидаемый результат:**

*   Удалены:
    *   (10.0001, 62.0005) — дубль/частота (расстояние < 0.00833 км)

    *   (10.0002, 62.0008) — шум (отклонение < 0.001 м)

    *   (20, 65) дубль — вторая точка с км 20 удалена

*   Результат:
    *   `LU1_KM = [0, 10, 15, 20, 25]`

    *   `LU1_HEIGHT = [60, 62, 63, 65, 68]`

    *   `LU1_PMAXDEFAULT = [6.0, 6.1, 6.2, 6.3, 6.4]`

*   Все три массива согласованной длины (5 элементов)

*   Краевые точки (0, 60) и (25, 68) сохранены


**Teardown:** `RESET()`

* * *

##### **HY-CALC-045 — Активность сегмента: группа задвижек**

**Требование:** R-HYDR-039 R-HYDR-042
**Описание:** Сегмент активен, если его группа задвижек открыта. Если задвижек нет — всегда активен.
**Логика (GrzdvStateAlg → SgluPartGrzdvActivityAlg):**

```
GrzdvStateAlg:
  Type 1 (OR): GRZDV_STATUS = 1, если хотя бы одна ZDV_STATUS = 2
  Type 2 (AND): GRZDV_STATUS = 1, только если все ZDV_STATUS = 2
  Без ZDV: GRZDV_STATUS = 1

SgluPartGrzdvActivityAlg:
  PartGRZDV пуст → SGLU_ACTIVITY = true
  GRZDV_STATUS = 1 → SGLU_ACTIVITY = true
  GRZDV_STATUS = 0 → SGLU_ACTIVITY = false
```

> **Важно:** `GRZDV_STATUS` принимает только 0 и 1. `ZDV_STATUS` принимает 0 (закрыта), 2 (открыта), 3 (ремонт).

**Обоснование:**

*   GRZDV1: Type=1 (OR), содержит ZDV1 и ZDV2

*   ZDV1_STATUS = 0, ZDV2_STATUS = 0 → GRZDV_STATUS = 0 → Activity = false

*   ZDV1_STATUS = 2, ZDV2_STATUS = 0 → GRZDV_STATUS = 1 (OR) → Activity = true


**Предусловие:**

*   `SGLU1_PARTGRZDV = ["GRZDV1"]`

*   `GRZDV1_TYPE = 1` (OR)

*   `GRZDV1_PART = ["ZDV1", "ZDV2"]`

*   `ZDV1_STATUS = 0`, `ZDV2_STATUS = 0`

*   `GRZDV1_STATUS = 0`

*   `SGLU1_ACTIVITY = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.GRZDV1.ZDV1.Status", 2)` — открыть ZDV1

2.  `WAIT(event)` — GrzdvStateAlg → SgluPartGrzdvActivityAlg

3.  `hmi.get("MT1.LU1.SGLU1.GRZDV1.Status")`

4.  `hmi.get("MT1.LU1.SGLU1.State.Activity")`

5.  `hmi.set("MT1.LU1.SGLU1.GRZDV1.ZDV1.Status", 0)` — закрыть ZDV1

6.  `WAIT(event)`

7.  `hmi.get("MT1.LU1.SGLU1.State.Activity")`


**Ожидаемый результат:**

*   Шаг 3: `GRZDV1_STATUS = 1` (OR: хотя бы одна открыта)

*   Шаг 4: `SGLU1_ACTIVITY = true`

*   Шаг 7: `SGLU1_ACTIVITY = false` (все закрыты)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-046 — Активность сегмента: без группы задвижек**

**Требование:** R-HYDR-039
**Описание:** Сегмент без задвижек (прямой перегон) всегда активен — его нельзя «закрыть».
**Предусловие:**

*   `SGLU2_PARTGRZDV` — пуст (сегмент не привязан к задвижкам)


**Действия:**

1.  `hmi.get("MT1.LU1.SGLU2.State.Activity")`


**Ожидаемый результат:**

*   `SGLU2_ACTIVITY = true` (всегда, без задвижек)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-047 — Видимость сегмента**

**Требование:** R-HYDR-040
**Описание:** На участках с лупингом (две параллельные нитки) отображается только приоритетный сегмент. Priority=0 (подкачка) всегда скрыт.
**Формула:**

```
Priority = 0 → Visible = false (всегда)
Priority > 0:
  Visible = (ControlOn = false AND Activity = true) OR (ControlOn = true AND Priority = 1)
```

**Таблица всех комбинаций:**
| Priority | ControlOn | Activity | Visible | Пояснение |
| --- | --- | --- | --- | --- |
| 0 | любое | любое | **false** | Подкачка всегда скрыта |
| 1 | true | любое | **true** | Лупинг на контроле — виден |
| 1 | false | true | **true** | Лупинг без контроля, но активен — виден |
| 1 | false | false | **false** | Неактивен и без контроля — скрыт |
| 2 | true | любое | **false** | Приоритет ≠ 1 и на контроле — скрыт |

**Предусловие:**

*   `SGLU1_PRIORITY = 1` (лупинг)

*   `SGLU2_PRIORITY = 0` (подкачка)


**Действия (проверка всех строк таблицы):**
| Шаг | Настройка | Ожидаемый Visible |
| --- | --- | --- |
| 1 | SGLU1: Priority=1, ControlOn=true, Activity=true | **true** |
| 2 | SGLU1: Priority=1, ControlOn=false, Activity=true | **true** |
| 3 | SGLU1: Priority=1, ControlOn=false, Activity=false | **false** |
| 4 | SGLU2: Priority=0, ControlOn=true, Activity=true | **false** |

**Ожидаемый результат:**

*   Каждый шаг даёт соответствующее `SGLU_VISIBLE`


**Teardown:** `RESET()`

* * *

##### **HY-CALC-048 — Состояние группы задвижек: OR и AND**

**Требование:** R-HYDR-042
**Описание:** Группа задвижек — логическая сущность. Type 1 (OR): открыта если хотя бы одна открыта. Type 2 (AND): открыта только если все открыты.
**Таблица:**
| Type | ZDV1 | ZDV2 | GRZDV_STATUS |
| --- | --- | --- | --- |
| 1 (OR) | 2 (открыта) | 0 (закрыта) | 1 (открыта) |
| 1 (OR) | 0 | 0 | 0 (закрыта) |
| 2 (AND) | 2 | 2 | 1 (открыта) |
| 2 (AND) | 2 | 0 | 0 (закрыта) |
| любой | без ZDV | — | 1 (открыта) |

**Предусловие:**

*   `GRZDV1_TYPE = 1` (OR)

*   `GRZDV1_PART = ["ZDV1", "ZDV2"]`

*   `ZDV1_STATUS = 0`, `ZDV2_STATUS = 0`

*   `GRZDV1_STATUS = 0`


**Действия:**

1.  `hmi.set("ZDV1.Status", 2)` → OR: одна открыта

2.  `WAIT(event)` → проверить GRZDV_STATUS = 1

3.  `hmi.set("ZDV2.Status", 2)` → OR: обе открыты

4.  `WAIT(event)` → GRZDV_STATUS = 1

5.  `hmi.set("ZDV1.Status", 0)` → OR: одна закрыта

6.  `WAIT(event)` → GRZDV_STATUS = 1 (вторая открыта)

7.  `hmi.set("ZDV2.Status", 0)` → OR: все закрыты

8.  `WAIT(event)` → GRZDV_STATUS = 0


**Для AND (Type=2):** 9. `hmi.set("GRZDV1.Type", 2)` — переключить на AND 10. `hmi.set("ZDV1.Status", 2)` → AND: одна открыта 11. `WAIT(event)` → GRZDV_STATUS = 0 (не все открыты) 12. `hmi.set("ZDV2.Status", 2)` → AND: обе открыты 13. `WAIT(event)` → GRZDV_STATUS = 1
**Ожидаемый результат:**

*   OR: шаги 2,4,6 → 1; шаг 8 → 0

*   AND: шаг 11 → 0; шаг 13 → 1


**Teardown:** `RESET()`

* * *

##### **HY-CALC-049 — Трассировка: включение и накопление**

**Требование:** R-HYDR-027
**Описание:** По команде `TracesOn` система накапливает историю параметров в оперативном буфере. Каждые `TraceInterval` записывается пара `[value, timestamp]`.
**Предусловие:**

*   `LU1_TRACEINTERVAL = 10` с (из ИМ)

*   `LU1_TRACETTL = 60` с (из ИМ)

*   `LU1_TRACESAVE = false`

*   `LU1_TU_TRACESON = false`

*   `KIP1_PRESS = 5.0` (стабилен)


**Действия:**

1.  `hmi.set("MT1.LU1.TU.TracesOn", true)`

2.  `WAIT(1c)` — LuTracingAlg (event-driven на команду)

3.  `WAIT(10c)` — первая итерация трассировки

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")`

5.  `WAIT(10c)` — вторая итерация

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")`

7.  `hmi.set("MT1.LU1.TU.TracesOff", true)`

8.  `WAIT(event)`

9.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")`


**Ожидаемый результат:**

*   Шаг 4: `KIP1_TRACESPRESS = [[5.0, ts1]]` (одна запись)

*   Шаг 6: `KIP1_TRACESPRESS = [[5.0, ts1], [5.0, ts2]]` (две записи)

*   Шаг 9: `KIP1_TRACESPRESS = []` (очищен при TracesOff)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-050 — Трассировка: TTL и сохранение**

**Требование:** R-HYDR-027
**Описание:** При `TracesSave = false`: записи старше TTL удаляются. При `TracesSave = true`: вся история сохраняется.
**Предусловие:**

*   `LU1_TRACESAVE = false`

*   `LU1_TRACETTL = 60` с

*   `LU1_TRACEINTERVAL = 10` с

*   Трассировка активна (`TracesOn = true`)


**Действия:**

1.  Включить трассировку

2.  Накопить 90 с (9 итераций по 10 с)

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")` — проверить TTL

4.  `hmi.set("MT1.LU1.State.TracesSave", true)` — включить сохранение

5.  Ещё 90 с

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")` — проверить, что всё сохранено


**Ожидаемый результат:**

*   Шаг 3: В массиве ~6 записей (90с / 10с = 9, минус старше 60с = 3 удалены → 6 осталось)

*   Шаг 6: В массиве ~18 записей (9 + 9, ничего не удалено, TracesSave=true)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-051 — Распределение плотности: ручное задание**

**Требование:** R-HYDR-013 (HYDRO-224)
**Описание:** Оператор задаёт карту плотности вручную. Если `RoDistribManual` непуст — используется вместо автоматического расчёта.
**Формат:**

```
"км_от,км_до,ρ;км_от,км_до,ρ;..."
Пример: "0,50,845;50,100,860;100,150,850"
```

**Предусловие:**

*   `LU1_RODISTRIBMANUAL` — пуст

*   `LU1_RODISTRIB` — расчётан автоматически

*   `PLTM1_RO = 850`, `UR1_QVMOM = 120`


**Действия:**

1.  `hmi.set("MT1.LU1.TI.RoDistribManual", "0,50,845;50,100,860;100,150,850")`

2.  `WAIT(1c)` — LuRoDistribAlg (каждую секунду)

3.  `hmi.get("MT1.LU1.TI.RoDistrib")`

4.  `hmi.set("MT1.LU1.TI.RoDistribManual", "")` — очистить

5.  `WAIT(1c)`

6.  `hmi.get("MT1.LU1.TI.RoDistrib")`


**Ожидаемый результат:**

*   Шаг 3: `LU1_RODISTRIB` соответствует ручному заданию: км 0–50 = 845, км 50–100 = 860, км 100–150 = 850

*   Шаг 6: `LU1_RODISTRIB` возвращён к автоматическому расчёту (по PLTM/UR)


**Teardown:** `RESET()`


* * *

##### **HY-CALC-052 — Распределение плотности: порог формирования партии**

**Требование:** R-HYDR-013
**Описание:** Новая партия создаётся при смене плотности > `DensLimit`. Ровно на пороге — **не создаётся** (строгое неравенство `>`).
**Формула:**

```
Если |ρ_новая − ρ_текущая| > DensLimit → новая партия
Если |ρ_новая − ρ_текущая| ≤ DensLimit → та же партия (шум)
```

**Обоснование (граничные значения):**

*   `DensLimit = 5` кг/м³ (из ИМ)

*   Текущая партия: ρ = 850

*   Граничный: |855 − 850| = 5 → **не создаётся** (5 > 5 = false)

*   Превышение: |856 − 850| = 6 → **создаётся** (6 > 5 = true)


**Предусловие:**

*   `LU1_DENSLIMIT = 5` кг/м³ (из ИМ)

*   `LU1_DENSTIME = 3600` с (из ИМ)

*   Текущая партия: ρ = 850 на км 0–100

*   `PLTM1_RO = 850` (плотномер на границе км 100)

*   `LU1_RODISTRIBMANUAL` — пуст (автоматический режим)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU2.PLT1.TI.Ro", 855)` — ровно на пороге

2.  `WAIT(1c)` — LuRoDistribAlg (каждую секунду)

3.  `hmi.get("MT1.LU1.TI.RoDistrib")` — проверить, что новая партия НЕ создана

4.  `hmi.set("MT1.LU1.SGLU2.PLT1.TI.Ro", 856)` — превышение порога

5.  `WAIT(1c)`

6.  `hmi.get("MT1.LU1.TI.RoDistrib")` — проверить, что новая партия создана


**Ожидаемый результат:**

*   Шаг 3: Плотность на км 100–200 остаётся 850 (855 − 850 = 5, не > 5, партия не делится)

*   Шаг 6: Плотность на км 100–200 = 856 (856 − 850 = 6 > 5, новая партия создана)



**Альтернативный кейс [НИЗКИЙ ПРИОРИТЕТ]: DensTime vs POLL(1с)**
| # | Действие | Ожидаемое |
| --- | --- | --- |
| 1 | `hmi.set("MT1.LU1.SGLU2.PLT1.TI.Ro", 856)` (разница 6 > 5) | Партия **не** создана немедленно |
| 2 | `WAIT(1c)` (6с) | `LU1_RODISTRIB` **не изменился** (DensTime=3600с, перерасчёт ещё не пришёл) |
| 3 | Временно установить `DensTime = 10с` через Redis | — |
| 4 | `WAIT(15c)` | `LU1_RODISTRIB` обновлён (новая партия создана) |
| 5 | Вернуть `DensTime = 3600с` | — |

**Обоснование:** Алгоритм POLL(1с) проверяет каждую секунду, но пересчитывает партии только раз в `DensTime`. Это значит что при DensTime=3600с изменение PLTM_RO не влияет на RoDistrib в течение часа.
**Teardown:** `RESET()`

* * *

##### **HY-CALC-053 — Унификация дельт на все датчики**

**Требование:** R-HYDR-026
**Описание:** Диспетчер задаёт единое значение дельты на уровне ТУ — все дочерние KIP/UR получают его мгновенно. 6 пар унификации:
| LU-тег | KIP/UR-тег | Применимость |
| --- | --- | --- |
| `LU_UNIFIED_PRESSDELTARANGEMAX` | `KIP_PRESSDELTARANGEMAX` | Все KIP на ТУ |
| `LU_UNIFIED_PRESSDELTARANGEMIN` | `KIP_PRESSDELTARANGEMIN` | Все KIP на ТУ |
| `LU_UNIFIED_QVMOMDELTARANGEMAX` | `UR_QVMOMDELTARANGEMAX` | Все UR на ТУ |
| `LU_UNIFIED_QVMOMDELTARANGEMIN` | `UR_QVMOMDELTARANGEMIN` | Все UR на ТУ |
| `LU_UNIFIED_PRESSDELTASCHEDULERANGEMAX` | `KIP_PRESSDELTASCHEDULERANGEMAX` | Все KIP на ТУ |
| `LU_UNIFIED_PRESSDELTASCHEDULERANGEMIN` | `KIP_PRESSDELTASCHEDULERANGEMIN` | Все KIP на ТУ |

**Предусловие:**

*   ТУ1: 3 KIP (KIP1, KIP2, KIP3), 2 UR (UR1, UR2)

*   Разные значения: KIP1: ΔMax=0.2, KIP2: ΔMax=0.3, KIP3: ΔMax=0.1

*   UR1: QVΔMax=5.0, UR2: QVΔMax=7.0


**Действия:**

1.  `hmi.set("MT1.LU1.TI.UnifiedPressDeltaRangeMax", 0.4)`

2.  `hmi.set("MT1.LU1.TI.UnifiedPressDeltaRangeMin", -0.15)`

3.  `hmi.set("MT1.LU1.TI.UnifiedQVmomDeltaRangeMax", 6.0)`

4.  `WAIT(event)` — LuUnifiedAlg

5.  Проверить все дочерние теги:


*   `hmi.get("KIP1.TI.PressDeltaRangeMax")` → 0.4

*   `hmi.get("KIP2.TI.PressDeltaRangeMax")` → 0.4

*   `hmi.get("KIP3.TI.PressDeltaRangeMax")` → 0.4

*   `hmi.get("KIP1.TI.PressDeltaRangeMin")` → −0.15

*   `hmi.get("UR1.TI.QVmomDeltaRangeMax")` → 6.0

*   `hmi.get("UR2.TI.QVmomDeltaRangeMax")` → 6.0


**Ожидаемый результат:**

*   Все KIP получили `PressDeltaRangeMax = 0.4`

*   Все KIP получили `PressDeltaRangeMin = −0.15`

*   Все UR получили `QVmomDeltaRangeMax = 6.0`


**Teardown:** `RESET()`

* * *

##### **HY-CALC-054 — Уставка ЦСПА: контроль вне режима контроля**

**Требование:** R-HYDR-010, R-HYDR-036
**Описание:** Уставка ЦСПА — последний рубеж защиты. Превышение генерирует `AlmLimitCSPA` **всегда**, независимо от режима контроля. Даже при Control=0 (ремонт, профилактика) превышение фиксируется.
**Формула:**

```
Если Press > LimitMaxPressCSPA → AlmLimitCSPA = true
HeadLimitMaxCSPA = (LimitMaxPressCSPA / ρ) × 101970 + H (для визуализации)
```

**Обоснование:**

*   `LimitMaxPressCSPA = 6.0` МПа (из ИМ)

*   P = 6.5 > 6.0 → аларм

*   HeadLimit = (6.0/850)×101970 + 63.5 = 719.5 + 63.5 = 783.0 м

*   P = 5.5 < 6.0 → без аларма


**Предусловие:**

*   `LU1_CONTROL = 0` (не на контроле — проверка что ЦСПА работает вне контроля)

*   `KIP1_LIMITMAXPRESSCSPA = 6.0` МПа (из ИМ)

*   `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`

*   `KIP1_PRESS = 5.5` (ниже уставки)

*   `KIP1_ALMLIMITCSPA = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 6.5)` — превышение

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmLimitCSPA")`

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadLimitMaxCSPA")`

5.  `hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmLimitCSPA")` — подтвердить доставку

6.  `hmi.history("MT1.LU1.SGLU1.KIP1.Alm.AlmLimitCSPA", from=ts_start, to=ts_now)` — проверить текст

7.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.5)` — вернуть

8.  `WAIT(event)`

9.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmLimitCSPA")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_ALMLIMITCSPA = true` (6.5 > 6.0) — **даже при Control=0**

*   Шаг 4: `KIP1_HEADLIMITMAXCSPA = 783.0 м`

*   Шаг 5: `hmi.history` возвращает запись: value=true, text содержит «Давление превышает уставку ЦСПА 6.0 МПа, текущее 6.5 МПа»

*   Шаг 8: `KIP1_ALMLIMITCSPA = false` (сброшен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-055 — Высота датчика: расчёт из конфигурации ТУ**

**Требование:** R-HYDR-002 (HYDRO-76)
**Описание:** Высота датчика определяется линейной интерполяцией между точками конфигурации ТУ. Без высоты формула напора не завершается.
**Формула:**

```
H_на_km = H_ниже + (H_выше − H_ниже) × (km − km_ниже) / (km_выше − km_ниже)
```

**Обоснование:**

*   Конфигурация: км [0, 50, 100, 150, 200], H [60, 62, 65, 68, 70]

*   KIP на км 75: между (50, 62) и (100, 65)

*   H = 62 + (65−62) × (75−50)/(100−50) = 62 + 3×0.5 = **63.5 м**

*   Gраничные:
    *   KIP на км 50 (ровно на точке): H = 62 м

    *   KIP на км 225 (вне диапазона 0–200): не рассчитывается

    *   Пустые LU_KM/LU_HEIGHT: не рассчитывается


**Предусловие:**

*   `LU1_KM = [0, 50, 100, 150, 200]`, `LU1_HEIGHT = [60, 62, 65, 68, 70]`

*   `KIP1_KM = 75`


**Действия:**

1.  `WAIT(60c)` — KipHeightAlg по циклу

2.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Height")`

3.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Km", 50)` — ровно на точке

4.  `WAIT(60c)`

5.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Height")`

6.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Km", 225)` — вне диапазона

7.  `WAIT(60c)`

8.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Height")`


**Ожидаемый результат:**

*   Шаг 2: `KIP1_HEIGHT = 63.5 м` (интерполяция)

*   Шаг 5: `KIP1_HEIGHT = 62 м` (ровно на точке конфигурации)

*   Шаг 8: `KIP1_HEIGHT` не меняется (остаётся 62) или `invalid = true` — вне диапазона


**Teardown:** `RESET()`

* * *

##### **HY-CALC-056 — Расчёт диапазона напора (HeadRange)**

**Требование:** R-HYDR-007, R-HYDR-032, R-HYDR-008
**Описание:** Границы диапазона давления пересчитываются в метры столба жидкости. HeadRange используется для проверок: не выходит ли верхняя граница за несущую, не опускается ли нижняя ниже конфигурации ТУ.
**Формулы:**

```
HeadRangeMax = (PressRangeMax / ρ) × 101970 + H
HeadRangeMin = (PressRangeMin / ρ) × 101970 + H
```

**Обоснование:**

*   PressRangeMax = 5.2, PressRangeMin = 4.9

*   ρ = 850, H = 63.5

*   HeadRangeMax = (5.2/850)×101970 + 63.5 = 624.0 + 63.5 = **687.5 м**

*   HeadRangeMin = (4.9/850)×101970 + 63.5 = 587.9 + 63.5 = **651.4 м**


**Два контрольных срабатывания:**

1.  `HeadRangeMin < H_конфигурации` → аларм (нижняя граница ниже конфигурации)

2.  `HeadRangeMax > CarrierHeadDef` → предупреждающий аларм (верхняя граница выше несущей)


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `KIP1_PRESSRANGEMAX = 5.2`, `KIP1_PRESSRANGEMIN = 4.9`

*   `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`

*   `LU1_CARRIERHEADDEF[km_75] ≈ 801.3 м`

*   `LU1_HEIGHT[km_75] = 63.5 м`


**Действия:**

1.  `WAIT(event)`

2.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadRangeMax")`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadRangeMin")`

4.  Проверить: 687.5 < 801.3 (не выше несущей) и 651.4 > 63.5 (не ниже конфигурации) → штатно


**Ожидаемый результат:**

*   `KIP1_HEADRANGEMAX = 687.5 м`

*   `KIP1_HEADRANGEMIN = 651.4 м`

*   `KIP1_HEADDELTARANGEMAX = (0.2 / 850) × 101970 = 24.0 м`

*   `KIP1_HEADDELTARANGEMIN = (0.1 / 850) × 101970 = 12.0 м`

*   Штатно: ни одна граница не нарушает несущую/конфигурацию


**Teardown:** `RESET()`

* * *

##### **HY-CALC-057 — Диапазон напора: верхняя граница выше несущей**

**Требование:** R-HYDR-032
**Описание:** **Предупреждающий** аларм: верхняя граница диапазона напора превышает несущую. Фактический напор ещё в норме, но если давление продолжит расти — будет разрушение.
**Формула:**

```
Если HeadRangeMax > CarrierHeadDef[km] → AlmDevRangeHeadCarrier = true
```

**Обоснование:**

*   CarrierHeadDef[km 75] ≈ 801.3 м

*   Для HeadRangeMax > 801.3: `(PressRangeMax/850)×101970 + 63.5 > 801.3`

*   → `PressRangeMax > (801.3 − 63.5) × 850 / 101970 = 737.8 × 850 / 101970 = 6.15 МПа`

*   Увеличиваем ΔMax до 1.5: `PressRangeMax = 5.0 + 1.5 = 6.5 МПа`

*   `HeadRangeMax = (6.5/850)×101970 + 63.5 = 779.5 + 63.5 = 843.0 м > 801.3 м` → аларм


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `KIP1_PRESSSTATION = 5.0`

*   `KIP1_PRESSDELTARANGEMAX = 0.2` (штатно)

*   `LU1_CARRIERHEADDEF[km_75] ≈ 801.3 м`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.PressDeltaRangeMax", 1.5)` — завысить дельту

2.  `WAIT(event)` — пересчёт RangeMax и HeadRangeMax

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadRangeMax")`

4.  Проверить аларм (тег уточняется — вероятно `KIP_ALMDEVRANGEHEADCARRIER`)

5.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.PressDeltaRangeMax", 0.2)` — вернуть

6.  `WAIT(event)`

7.  Проверить: аларм сброшен


**Ожидаемый результат:**

*   Шаг 3: `KIP1_HEADRANGEMAX = 843.0 м`

*   Шаг 4: Аларм = true (843.0 > 801.3)

*   Шаг 7: Аларм = false (возврат к 687.5 < 801.3)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-058 — Дебаланс: проверка алармов в топике alarm**

**Требование:** R-HYDR-033
**Описание:** E2E-проверка: алармы дебаланса записаны в топик Kafka `alarm` с правильным форматом.
**Формат события:**

```json
{
  "tag": "MT1.LU1.Alm.AlmDevQmom",
  "ts": 1700000000000,
  "value": true,
  "text": "Дебаланс расходов превышает допустимый: 2.0 м³/ч при лимите ±1.5 м³/ч",
  "priority": "WARNING",
  "state": "ACTIVE"
}
```

**Четыре аларма дебаланса:**
| Тег | Описание |
| --- | --- |
| `LU1_ALMDEVQMOM` | Мгновенный |
| `LU1_ALMDEVQAVG` | Средний за час |
| `LU1_ALMDEVQAVGSTATION` | Стационарный средний |
| `LU1_ALMDEVQAVGSTATION2` | Стационарный мгновенный |

**Предусловие:**

*   `LU1_CONTROL = 1`

*   `LU1_DIFFQMOMLIMITMAX = 1.5`, `LU1_DIFFQMOMLIMITMIN = −1.5`

*   UR1 (выходной): QVmom = 120.0

*   UR2 (входной): QVmom = 122.0


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 122.0)`

2.  `WAIT(60c)`

3.  `hmi.wait_alarm("MT1.LU1.Alm.AlmDevQmom", timeout=30s)` — подтвердить доставку

4.  `hmi.history("MT1.LU1.Alm.AlmDevQmom", from=ts_start, to=ts_now)` — проверить полный формат (value, text, priority, state)

5.  `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 120.3)`

6.  `WAIT(60c)`

7.  `hmi.wait_alarm("MT1.LU1.Alm.AlmDevQmom", timeout=30s)` — подтвердить сброс

8.  `hmi.history("MT1.LU1.Alm.AlmDevQmom", from=ts_start, to=ts_now)` — проверить: value=false, state="CLEARED"


**Ожидаемый результат:**

*   Шаг 3: `hmi.wait_alarm` подтверждает value=true

*   Шаг 4: `hmi.history` возвращает: value=true, priority="WARNING", state="ACTIVE", text содержит «2.0 м³/ч», «±1.5»

*   Шаг 7: `hmi.wait_alarm` подтверждает value=false (сброс)

*   Шаг 8: `hmi.history` возвращает: value=false, state="CLEARED"


**Teardown:** `RESET()`

* * *

##### **HY-CALC-059 — Самотеки: проверка алармов в топике alarm**

**Требование:** R-HYDR-035
**Описание:** E2E-проверка алармов самотеков в топике `alarm`.
**Три аларма:**
| Тег | Описание |
| --- | --- |
| `LU1_ALMGRAVITY` | Обнаружен самотечный сегмент |
| `LU1_ALMGRAVITYPOSSIBLE` | Риск перехода в самотёк |
| `KIP1_ALMGRAVITYPOSSIBLE` | Напор на конкретном датчике близок к конфигурации |

**Предусловие:**

*   Конфигурация ТУ1: пик км 65, H = 400 м (как в HY-CALC-038)

*   KIP1 (км 50): Press = 3.0 (Head = 722 > 400)

*   KIP2 (км 80): Press = 0.5 (Head = 359.9 < 400)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 3.0)`

2.  `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.5)`

3.  `WAIT(event)`

4.  `hmi.wait_alarm("MT1.LU1.Alm.AlmGravity", timeout=10s)` — подтвердить доставку

5.  `hmi.history("MT1.LU1.Alm.AlmGravity", from=ts_start, to=ts_now)` — проверить: value=true, text содержит «самотечный», «перевальная точка»


**Ожидаемый результат:**

*   `hmi.wait_alarm` подтверждает value=true

*   `hmi.history` возвращает: value=true, text содержит «самотечный участок км 50–80, перевальная точка на км 65»


**Teardown:** `RESET()`


##### **HY-CALC-060 — Статус ремонта: автоматическое отключение/включение**

**Требование:** EVOSCADA-21706 (DisableAndRemontStatusAlg)
**Описание:** При переходе датчика в ремонт (`RemontStatus ≠ 0`) система автоматически ставит `Disable = true`. При возвращении из ремонта (`RemontStatus = 0`) — `Disable = false`. Работает для KIP, UR, PLTM.
**Логика:**

```
RemontStatus ≠ 0 AND Disable = false → Disable = true (отключаем)
RemontStatus = 0 AND Disable = true → Disable = false (включаем)
```

**Дополнительно (TU.SetOn/Off):**

*   `TU.SetOff = true` → `Disable = true` (команда отключения)

*   `TU.SetOn = true` AND `RemontStatus ≠ 0` → **НЕ включается** (в ремонте)

*   `TU.SetOn = true` AND `RemontStatus = 0` → `Disable = false` (включается)


**Обоснование:**

*   RemontStatus = 1 → ремонт → автоматическое отключение

*   RemontStatus = 0 → норма → автоматическое включение

*   При ремонте команда SetOn игнорируется (защита от случайного включения)


**Предусловие:**

*   `KIP1_DISABLE = false`

*   `KIP1_REMONTSTATUS = 0` (норма)

*   `KIP1_TU_SETON = false`, `KIP1_TU_SETOFF = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.RemontStatus", 1)` — в ремонт

2.  `WAIT(event)` — DisableAndRemontStatusAlg

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")`

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.TU.SetOn", true)` — попытка включения в ремонте

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")` — должен остаться true

7.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.RemontStatus", 0)` — вернули из ремонта

8.  `WAIT(event)`

9.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")`

10.  `hmi.set("MT1.LU1.SGLU1.KIP1.TU.SetOff", true)` — команда отключения

11.  `WAIT(event)`

12.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")`

13.  `hmi.set("MT1.LU1.SGLU1.KIP1.TU.SetOn", true)` — команда включения

14.  `WAIT(event)`

15.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Disable")`


**Ожидаемый результат:**

*   Шаг 3: `Disable = true` (автоматически, из-за ремонта)

*   Шаг 6: `Disable = true` (SetOn игнорируется — датчик в ремонте)

*   Шаг 9: `Disable = false` (вернули из ремонта, автоматически включён)

*   Шаг 12: `Disable = true` (команда SetOff)

*   Шаг 15: `Disable = false` (команда SetOn, ремонт не активен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-061 — Видимость датчика (KipVisibleAlg)**

**Требование:** R-HYDR-041
**Описание:** Датчик видим, если:

1.  `Disable = false` (не отключён)

2.  Родительский SGLU видим (`SGLU_VISIBLE = true`)


Если датчик отключён **или** сегмент скрыт — датчик невидим.
**Формула:**

```
KIP_VISIBLE = (KIP_DISABLE = false) AND (SGLU_VISIBLE = true)
```

**Предусловие:**

*   `KIP1_DISABLE = false`

*   `SGLU1_VISIBLE = true`

*   `KIP1_VISIBLE = true` (штатно)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", true)` — отключить датчик

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")`

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", false)` — включить

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")`

7.  `hmi.set("MT1.LU1.SGLU1.State.Visible", false)` — скрыть сегмент

8.  `WAIT(event)`

9.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")`

10.  `hmi.set("MT1.LU1.SGLU1.State.Visible", true)` — показать сегмент

11.  `WAIT(event)`

12.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_VISIBLE = false` (отключён)

*   Шаг 6: `KIP1_VISIBLE = true` (включён, сегмент видим)

*   Шаг 9: `KIP1_VISIBLE = false` (сегмент скрыт)

*   Шаг 12: `KIP1_VISIBLE = true` (всё штатно)


**Teardown:** `RESET()`

* * *



##### **HY-CALC-062 — Отклонение напора и давления (KipHeadDeltaPressAlg)**

**Требование:** R-HYDR-028
**Описание:** После фиксации базового состояния (Control=1) система рассчитывает отклонения текущего напора и давления от базовых значений. Используются для визуализации на АРМ и генерации алармов.
**Формулы:**

```
HeadDelta = Head − HeadStation
PressDelta = Press − PressStation
```

**Обоснование:**

*   PressStation = 5.0 МПа, HeadStation = 663.2 м (зафиксировано при Control=1)

*   P = 5.3 → Head = (5.3/850)×101970 + 63.5 = 635.8 + 63.5 = 699.3 м

*   `PressDelta = 5.3 − 5.0 = 0.3` МПа

*   `HeadDelta = 699.3 − 663.2 = 36.1` м

*   P = 4.8 → Head = (4.8/850)×101970 + 63.5 = 573.6 + 63.5 = 637.1 м

*   `PressDelta = 4.8 − 5.0 = −0.2` МПа

*   `HeadDelta = 637.1 − 663.2 = −26.1` м


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `KIP1_PRESSSTATION = 5.0`

*   `KIP1_HEADSTATION = 663.2 м`

*   `KIP1_PRESS = 5.0` (штатно, Delta = 0)

*   `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.3)` — отклонение вверх

2.  `WAIT(event)` — KipHeadDeltaPressAlg

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressDelta")`

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadDelta")`

5.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 4.8)` — отклонение вниз

6.  `WAIT(event)`

7.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressDelta")`

8.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadDelta")`

9.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — вернуть в норму

10.  `WAIT(event)`

11.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressDelta")`

12.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadDelta")`


**Ожидаемый результат:**

*   Шаг 3: `KIP1_PRESSDELTA = 0.3` МПа

*   Шаг 4: `KIP1_HEADDELTA = 36.1` м

*   Шаг 7: `KIP1_PRESSDELTA = −0.2` МПа

*   Шаг 8: `KIP1_HEADDELTA = −26.1` м

*   Шаг 11: `KIP1_PRESSDELTA = 0.0` МПа

*   Шаг 12: `KIP1_HEADDELTA = 0.0` м


**Teardown:** `RESET()`

* * *

##### **HY-CALC-063 — План перекачки (PumpingPlanAlg)**

**Требование:** R-HYDR-009
**Описание:** Система получает JSON-план перекачки с режимами и временными окнами. Каждую минуту (planScannerInterval) проверяет актуальный режим. По событиям KIP обновляет плановые значения. Записывает `PressSchedule`, `HeadSchedule`, `RegimName`.
**Логика:**

```
1. Загрузить JSON плана (из LU1_TI.ARMTPumpPlan или внешнего источника)
2. Каждая минута: определить текущее время → найти активный режим
3. Для каждого KIP: рассчитать плановое давление/напор по режиму
4. Записать: KIP_PRESSSCHEDULE, KIP_HEADSCHEDULE, LU_SCHEDULEREGIMNAME
5. При смене режима: обновить значения
```

**Формат JSON плана (упрощённый):**

```json
{
  "regims": [
    {
      "name": "Нормальный",
      "startTime": "06:00",
      "endTime": "22:00",
      "pressure": 5.0,
      "head": 670.0
    },
    {
      "name": "Ночной",
      "startTime": "22:00",
      "endTime": "06:00",
      "pressure": 4.5,
      "head": 620.0
    }
  ]
}
```

**Обоснование:**

*   Тестируем смену режима: «Нормальный» (P=5.0) → «Ночной» (P=4.5)

*   planScannerInterval = 60 мин (из application.yml)

*   Для ускорения теста: можно временно установить planScannerInterval = 1 мин


**Предусловие:**

*   `LU1_TI.ARMTPumpPlan` содержит JSON плана (загружен ранее)

*   Текущее время: 06:00 (начало режима «Нормальный»)

*   `KIP1_PRESSSCHEDULE` — пуст или устаревшее значение

*   `LU1_SCHEDULEREGIMNAME` — пуст


**Действия:**

1.  `WAIT(60c)` — первый скан планнера (план загружен, определяет режим)

2.  `hmi.get("MT1.LU1.TI.SchedulerRegimName")`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressSchedule")`

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadSchedule")`

5.  `WAIT(60min)` — переход к 07:00 (или сменить время в стенде)

6.  Проверить: режим не изменился (всё ещё «Нормальный», до 22:00)

7.  Сменить время на 22:00 (через системное время стенда или эмуляцию)

8.  `WAIT(60c)` — следующий скан

9.  `hmi.get("MT1.LU1.TI.SchedulerRegimName")`

10.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressSchedule")`


**Ожидаемый результат:**

*   Шаг 2: `LU1_SCHEDULEREGIMNAME = "Нормальный"`

*   Шаг 3: `KIP1_PRESSSCHEDULE = 5.0` МПа

*   Шаг 4: `KIP1_HEADSCHEDULE = 670.0` м

*   Шаг 9: `LU1_SCHEDULEREGIMNAME = "Ночной"`

*   Шаг 10: `KIP1_PRESSSCHEDULE = 4.5` МПа


**Примечание:** Тест с планом перекачки — ночной (60 мин цикл). Для ускорения:

*   Вариант 1: Временно установить `planScannerInterval = 60s` в application.yml

*   Вариант 2: Симулировать смену системного времени стенда


**Teardown:** `RESET()`

* * *

##### **HY-CALC-064 — Перенос времени контроля (LuNewControlTimeAlg / FAST)**

**Требование:** R-HYDR-046
**Описание:** По команде `SetTimeShift` система загружает историю значений (Press, Head, Ro) на момент целевого времени из ClickHouse и записывает их как текущие. Используется для FAST-режима (ускоренного перерасчёта истории при переносе контроля).
**Логика:**

```
1. Диспетчер: SetTimeShift = true + целевой timestamp
2. LuNewControlTimeAlg:
   a. Запросить ClickHouse: SELECT tag, value, invalid FROM history WHERE ts = target_ts
   b. Для каждого KIP/UR: записать Press, Head, Ro из истории как текущие
   c. Записать в топик model_main_{sessionId} (для FAST) или main (для оперативного)
3. Далее стандартный расчёт по загруженным значениям
```

**Обоснование:**

*   FAST-режим: диспетчер переносит контроль на момент времени в прошлом

*   Система подтягивает состояние системы на тот момент и пересчитывает

*   Цель: проверить, что на момент X всё было штатно / были алармы


**Предусловие:**

*   Сессия моделирования создана: `model_main_{sessionId}`

*   В ClickHouse есть история за последние 24 часа

*   На момент T_target (например, 2 часа назад): KIP1_PRESS = 4.8, KIP1_RO = 850

*   Текущее: KIP1_PRESS = 5.0


**Действия:**

1.  `hmi.set("MT1.LU1.TU.SetTimeShift", true)` + целевой timestamp (T_target)

2.  `WAIT(event)` — LuNewControlTimeAlg

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Press")` — должно быть значение из истории

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` — пересчитано по историческим данным

5.  Проверить в топике `model_main_{sessionId}`: значения записаны


**Ожидаемый результат:**

*   Шаг 3: `KIP1_PRESS = 4.8` (значение из истории на T_target, а не текущее 5.0)

*   Шаг 4: `KIP1_HEAD` пересчитано: `(4.8/850)×101970 + 63.5 = 573.6 + 63.5 = 637.1 м`

*   В топике `model_main_{sessionId}` записаны значения с timestamp = T_target


**Примечание:**

*   Тест требует данных в ClickHouse. Перед тестом: записать историю через Kafka (нормальный поток работы)

*   FAST-режим работает в рамках сессии моделирования (топики `model_main_*`)

*   Точный формат команды SetTimeShift (timestamp в отдельном теге или в том же) уточняется


**Teardown:** Закрыть сессию (`mod-hist` → close) → `RESET()`

* * *

##### **HY-CALC-065 — Расширение: скорость давления — PressRateKiplimit > 1**

**Требование:** R-HYDR-034
**Описание:** HY-CALC-033 проверяет `PressRateKiplimit = 1` (достаточно 1 датчика). Дополнительно проверяем: при `PressRateKiplimit = 2` — нужно минимум 2 датчика с превышением для аларма.
**Обоснование:**

*   `PressRateKiplimit = 2` (из ИМ — для ТУ с большим числом датчиков)

*   1 KIP с V = 0.8 МПа/мин → count = 1 < 2 → **аларма нет**

*   2 KIP с V = 0.8 МПа/мин → count = 2 ≥ 2 → **аларм**


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `LU1_PRESSRATELIMIT = 0.05` МПа/мин

*   `LU1_PRESSRATEKIPLIMIT = 2` (из ИМ)

*   `LU1_PRESSRATEALGORITHM = 1`

*   3 KIP: KIP1, KIP2, KIP3, все Press = 5.0 (стабильно)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.4)` — только 1 датчик

2.  `WAIT(60c)`

3.  `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")` — должен быть false

4.  `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.4)` — второй датчик

5.  `WAIT(60c)`

6.  `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")` — должен быть true

7.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — стабилизировать первый

8.  `hmi.set("MT1.LU1.SGLU1.KIP2.TI.Press", 5.0)` — стабилизировать второй

9.  `WAIT(60c)`

10.  `hmi.get("MT1.LU1.Alm.AlmRateLimitPress")` — false


**Ожидаемый результат:**

*   Шаг 3: `LU1_ALMPRESSRATELIMIT = false` (1 < 2, недостаточно)

*   Шаг 6: `LU1_ALMPRESSRATELIMIT = true` (2 ≥ 2, достаточно)

*   Шаг 10: `LU1_ALMPRESSRATELIMIT = false` (сброшен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-066 — Расширение: трассировка — TracesSave=true и TracesOff**

**Требование:** R-HYDR-027
**Описание:** Дополнительные проверки трассировки:

1.  При `TracesSave = true` — записи старше TTL **не удаляются**

2.  При `TracesOff = true` — массивы очищаются, флаг сбрасывается


**Предусловие:**

*   `LU1_TRACEINTERVAL = 10` с

*   `LU1_TRACETTL = 60` с

*   `LU1_TRACESON = true` (активна)

*   `KIP1_PRESS = 5.0` (стабилен)


**Действия (часть 1: TracesSave=true):**

1.  `hmi.set("MT1.LU1.State.TracesSave", true)`

2.  Накопить 90 с (9 итераций)

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")` — проверить длину


**Действия (часть 2: TracesOff):** 4. `hmi.set("MT1.LU1.TU.TracesOff", true)` 5. `WAIT(event)` 6. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.TracesPress")` — пуст 7. `hmi.get("MT1.LU1.TU.TracesOff")` — сброшен
**Ожидаемый результат:**

*   Шаг 3: В массиве **9 записей** (90с / 10с), несмотря на TTL = 60с (TracesSave=true → ничего не удаляется)

*   Шаг 6: `KIP1_TRACESPRESS = []` (очищен)

*   Шаг 7: `LU1_TU_TRACESOFF = false` (сброшен)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-067 — Расширение: автоматическое распределение плотности**

**Требование:** R-HYDR-013
**Описание:** HY-CALC-051 проверяет ручной режим. Дополнительно: автоматический расчёт по PLTM_RO и UR_QVMOM. Система делит ТУ на УРР (участки равного расхода) и формирует партии.
**Логика:**

```
1. Определить УРР: участки между UR (по км)
2. Для каждого УРР:
   a. Взять PLTM_RO (плотность) для этого участка
   b. Если |Ro_новый − Ro_предыдущий| > DensLimit → новая партия
   c. Иначе →延续 текущей партии
3. Записать LU_RODISTRIB: массив плотностей по км
```

**Обоснование:**

*   ТУ1: км 0–200

*   UR1 на км 0, UR2 на км 100, UR3 на км 200

*   УРР: [0–100], [100–200]

*   PLTM1 (км 50): Ro = 850

*   PLTM2 (км 150): Ro = 852 (разница 2 < 5 = DensLimit → та же партия)

*   Результат: одна партия на всё ТУ: ρ = 850 (или среднее)


**Вариант 2 (разные партии):**

*   PLTM1 (км 50): Ro = 850

*   PLTM2 (км 150): Ro = 856 (разница 6 > 5 → новая партия)

*   Результат: две партии: км 0–100 = 850, км 100–200 = 856


**Предусловие:**

*   `LU1_RODISTRIBMANUAL` — пуст (автоматический режим)

*   `LU1_DENSLIMIT = 5` кг/м³

*   UR1 (км 0), UR2 (км 100), UR3 (км 200)

*   PLTM1 (км 50): Ro = 850

*   PLTM2 (км 150): Ro = 856


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.PLT1.TI.Ro", 850)`

2.  `hmi.set("MT1.LU1.SGLU2.PLT2.TI.Ro", 856)`

3.  `WAIT(1c)` — LuRoDistribAlg (каждую секунду)

4.  `hmi.get("MT1.LU1.TI.RoDistrib")`

5.  `hmi.set("MT1.LU1.SGLU2.PLT2.TI.Ro", 852)` — разница 2 < 5

6.  `WAIT(1c)`

7.  `hmi.get("MT1.LU1.TI.RoDistrib")`


**Ожидаемый результат:**

*   Шаг 4: `LU1_RODISTRIB` — две партии: км 0–100 = 850, км 100–200 = 856 (разница 6 > 5)
    *   Шаг 4а: `hmi.get("MT1.LU1.TI.RoDistribSpeed")` // если тег существует в коде — прочитать скорость партии (м/ч). Если отдельного тега нет — проверить, что при изменении QVmom границы партиций смещаются пропорционально: v = (4 × Q) / (π × D²)

*   Шаг 7: `LU1_RODISTRIB` — одна партия: км 0–200 = 850 или 851 (разница 2 < 5, не делится)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-068 — Расширение: фильтрация конфигурации — все 3 фильтра одновременно**

**Требование:** R-HYDR-014
**Описание:** HY-CALC-044 проверяет каждый фильтр. Дополнительно: все 3 типа артефактов одновременно в одном массиве + проверка, что краевые точки сохраняются.
**Обоснование:**

*   Длина ТУ = 25 км → порог частоты: 25/3000 = 0.00833 км

*   Вход: `[0, 10, 10.0001, 10.0002, 10.008, 15, 15, 20, 25]`
    *   10.0001: расстояние 0.0001 < 0.00833 → **частота** (удалить)

    *   10.0002: отклонение от линии < 0.001 → **шум** (удалить)

    *   10.008: расстояние 0.008 < 0.00833 → **частота** (удалить)

    *   15 (второй): **дубль** (удалить)

*   Ожидаемый результат: `[0, 10, 15, 20, 25]`


**Предусловие:**

*   `LU1_KM = [0, 10, 10.0001, 10.0002, 10.008, 15, 15, 20, 25]`

*   `LU1_HEIGHT = [60, 62, 62.0005, 62.0008, 62.008, 63, 63, 65, 68]`

*   `LU1_PMAXDEFAULT = [6.0, 6.1, 6.1, 6.1, 6.1, 6.2, 6.2, 6.3, 6.4]`


**Действия:**

1.  Загрузить конфигурацию в data-manager

2.  `WAIT(60c)` — LuDataThinningAlg

3.  `hmi.get("MT1.LU1.TI.KM")`

4.  `hmi.get("MT1.LU1.TI.Height")`

5.  Проверить: длина массивов = 5, краевые точки (0, 60) и (25, 68) на месте


**Ожидаемый результат:**

*   `LU1_KM = [0, 10, 15, 20, 25]`

*   `LU1_HEIGHT = [60, 62, 63, 65, 68]`

*   `LU1_PMAXDEFAULT = [6.0, 6.1, 6.2, 6.3, 6.4]`

*   Все три массива: 5 элементов (согласованная длина)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-069 — Расширение: самотёки — плато на конфигурации ТУ**

**Требование:** R-HYDR-018
**Описание:** На конфигурации ТУ может быть плато (несколько точек с одинаковой высотой). Алгоритм должен корректно обрабатывать: перевальная точка — не одна, а диапазон.
**Логика:**

```
Плато: точки (50, 400), (60, 400), (70, 400) — все с H = 400
Перевальная точка: не одна координата, а диапазон [50, 70]
Сегмент самотечный, если Head < 400 на любом участке плато
```

**Предусловие:**

*   Конфигурация: `LU_KM = [0, 50, 60, 70, 80, 100]`, `LU_HEIGHT = [300, 400, 400, 400, 300, 280]`

*   Плато: км 50–70, H = 400

*   KIP1 (км 40): Press = 3.0 → Head = 722 (высоко)

*   KIP2 (км 80): Press = 0.5 → Head = 359.9 (< 400 → самотек)


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 3.0)`

2.  `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.5)`

3.  `WAIT(event)`

4.  `hmi.get("MT1.LU1.Alm.AlmGravity")`

5.  `hmi.get("MT1.LU1.TI.PassPoints")`

6.  `hmi.get("MT1.LU1.TI.GravitySegs")`


**Ожидаемый результат:**

*   `LU1_ALMGRAVITY = true`

*   `LU1_PASSPOINTS` содержит диапазон или точку плато: [50] или [50, 60, 70] (зависит от реализации)

*   `LU1_GRAVITYSEGS = ["40,80"]` или ["50,80"] (сегмент ниже плато)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-070 — Расширение: дебаланс — DiffQavg и DiffQavgStation**

**Требование:** R-HYDR-033
**Описание:** HY-CALC-019/020 проверяют только мгновенный `DiffQmom`. Дополнительно: средний за час (`DiffQavg`) и стационарный (`DiffQavgStation`).
**Логика:**

```
DiffQavg = скользящее среднее DiffQmom за последний час (3600 с)
DiffQavgStation = DiffQavg при Station = true (зафиксированное значение)

Алармы:
- AlmDevQavg: |DiffQavg| > LimitMax
- AlmDevQavgStation: |DiffQavgStation| > LimitMax (при Station=true)
```

**Обоснование:**

*   Мгновенный: DiffQmom = 2.0 (аларм)

*   Средний за час: если 55 мин было 0.5, а 5 мин было 15.0:
    *   DiffQavg = (55×0.5 + 5×15.0) / 60 = (27.5 + 75) / 60 = 1.71

    *   1.71 > 1.5 → аларм по среднему

*   Стационарный: если Station=true → DiffQavgStation фиксируется


**Предусловие:**

*   `LU1_CONTROL = 1`

*   `LU1_DIFFQMOMLIMITMAX = 1.5`

*   `LU1_STATION = true`

*   Установившийся DiffQmom = 0.5 (штатно, >1 ч)

*   `LU1_DIFFQAVG = 0.5`, `LU1_ALMDEVQAVG = false`


**Действия:**

1.  `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 130.0)` — резкий рост (DiffQmom = 10)

2.  `WAIT(60c)` — DiffQmom = 10, но DiffQavg ещё ~0.5 (только 1 мин из 60)

3.  `hmi.get("MT1.LU1.TI.DiffQmom")` → 10.0

4.  `hmi.get("MT1.LU1.TI.DiffQavg")` → ~0.65 (немного выросло)

5.  `hmi.get("MT1.LU1.Alm.AlmDevQmom")` → true (мгновенный аларм)

6.  `hmi.get("MT1.LU1.Alm.AlmDevQavg")` → false (средний ещё в норме)

7.  `WAIT(3600c)` — час прошёл, DiffQavg = 10.0

8.  `hmi.get("MT1.LU1.TI.DiffQavg")` → 10.0

9.  `hmi.get("MT1.LU1.Alm.AlmDevQavg")` → true (средний аларм)


**Ожидаемый результат:**

*   Шаг 5: `LU1_ALMDEVQMOM = true` (мгновенный: 10 > 1.5)

*   Шаг 6: `LU1_ALMDEVQAVG = false` (средний: 0.65 < 1.5)

*   Шаг 9: `LU1_ALMDEVQAVG = true` (средний: 10.0 > 1.5)


**Примечание:** Тест с ожиданием 1 часа — ночной. Для ускорения: временно уменьшить окно усреднения в ИМ (если возможно) или проверять только логику через Redis (записать DiffQavg напрямую и проверить аларм).
**Teardown:** `RESET()`

* * *

##### **HY-CALC-071 — Расширение: стационарность LU — зона «недостаточно данных»**

**Требование:** R-HYDR-017
**Описание:** HY-CALC-026 проверяет «достоверно стационарный», HY-CALC-027 — «достоверно нестационарный». Дополнительно: третья зона — «недостаточно данных».
**Логика:**

```
Зона 1 (стационарный): нестационарных < CountKIPNoStation AND стационарных ≥ LimitKIP → true
Зона 2 (нестационарный): нестационарных ≥ CountKIPNoStation → false
Зона 3 (недостаточно данных): стационарных < LimitKIP AND нестационарных < CountKIPNoStation → false
```

**Обоснование:**

*   5 KIP: 1 стационарен, 4 нестационарны

*   `CountKIPNoStation = 2`, `LimitKIP = 3`

*   Нестационарных = 4 ≥ 2 → **Зона 2** (нестационарный)


**Вариант для Зоны 3:**

*   5 KIP: 1 стационарен, 1 нестационарен, 3 invalid

*   Нестационарных = 1 < 2 (порог)

*   Стационарных = 1 < 3 (LimitKIP)

*   → **Зона 3** (недостаточно данных) → false


**Предусловие:**

*   5 KIP: KIP1 (Station=true), KIP2 (Station=false), KIP3–KIP5 (invalid=true)

*   `LU1_COUNTKIPNOSTATION = 2`

*   `LU1_LIMITKIP = 3`


**Действия:**

1.  `hmi.set("KIP3.Press", 5.0, invalid=true)`

2.  `hmi.set("KIP4.Press", 5.0, invalid=true)`

3.  `hmi.set("KIP5.Press", 5.0, invalid=true)`

4.  `WAIT(event)` — LuStationAlg

5.  `hmi.get("MT1.LU1.State.Station")`

6.  `hmi.get("MT1.LU1.State.CounterKIP")`


**Ожидаемый результат:**

*   Шаг 5: `LU1_STATION = false` (Зона 3: стационарных = 1 < LimitKIP = 3, нестационарных = 1 < CountKIPNoStation = 2)

*   Шаг 6: `LU1_COUNTERKIP = 1` (только KIP1 валиден)


**Teardown:** `RESET()`

* * *

##### **HY-CALC-072 — Автопостановка — прерывание во время отсчёта**

**Требование:** R-HYDR-025
**Описание:** HY-CALC-028 проверяет полный цикл. Дополнительно: прерывание отсчёта при потере стационарности и возобновление после восстановления.
**Логика:**

```
1. AutoControlOn=true, Station=true → TimeLeft = 180 (отсчёт начался)
2. TimeLeft: 180 → 120 (цикл 1)
3. Скачок → Station=false → TimeLeft = −1 (отсчёт прерван)
4. Стабилизация → Station=true → TimeLeft = 180 (отсчёт заново)
```

**Предусловие:**

*   `LU1_CONTROL = 0`

*   `LU1_AUTOCONTROLON = true`

*   `LU1_STATION = true` (все KIP стабильны)

*   `LU1_CONTROLAUTOTIMEOUT = 180` с


**Действия:**

1.  `WAIT(60c)` — цикл 1

2.  `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")` → 180

3.  `WAIT(60c)` — цикл 2

4.  `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")` → 120

5.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.7)` — скачок (Station → false)

6.  `WAIT(event)`

7.  `hmi.get("MT1.LU1.State.Station")`

8.  `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`

9.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` — стабилизация

10.  `WAIT(130c)` — 120 с стабильности + 10 с margin

11.  `hmi.get("MT1.LU1.State.Station")`

12.  `WAIT(60c)` — следующий цикл

13.  `hmi.get("MT1.LU1.State.ControlAutoTimeLeft")`


**Ожидаемый результат:**

*   Шаг 2: `TimeLeft = 180` (отсчёт начался)

*   Шаг 4: `TimeLeft = 120` (идёт отсчёт)

*   Шаг 7: `Station = false` (скачок 0.7 > DevMaxStation 0.5)

*   Шаг 8: `TimeLeft = −1` (отсчёт прерван)

*   Шаг 11: `Station = true` (восстановлена стабильность)

*   Шаг 13: `TimeLeft = 180` (отсчёт начался **заново**, не продолжается с 120)


**Примечание:** Для ускорения — временно установить `TimeIntSetStation = 15 с` и `ControlAutoTimeOut = 30 с` через Redis. Тогда: 2 цикла по 60 с → прерывание → 20 с стабильности → 1 цикл → TimeLeft = 0 → Control = 1.
**Teardown:** `RESET()`


### 3.8 Каскадные эффекты

##### **HY-CALC-083 — Каскад: SGLU Activity=false → влияние на датчики**

**Требование:** R-HYDR-039, R-HYDR-041 **Описание:** Когда группа задвижек закрыта (GRZDV_STATUS=0) → SGLU_ACTIVITY=false → SGLU_VISIBLE=false (если Priority=1, ControlOn=false) → KIP_VISIBLE=false. Проверяем полный каскад.
**Предусловие:**

*   `SGLU1_PARTGRZDV = ["GRZDV1"]`

*   `GRZDV1_TYPE = 1` (OR), `GRZDV1_PART = ["ZDV1"]`

*   `ZDV1_STATUS = 0` (закрыта) → `GRZDV1_STATUS = 0` → `SGLU1_ACTIVITY = false`

*   `SGLU1_PRIORITY = 1`, `SGLU1_CONTROLON = false`

*   `SGLU1_VISIBLE = false` (Priority=1, ControlOn=false, Activity=false)

*   `KIP1_DISABLE = false`

*   `KIP1_VISIBLE = false` (SGLU невидим)

*   `KIP1_PRESS = 5.0` (приходит, валидный)

*   `LU1_CONTROL = 1`


**Действия (часть 1: проверка каскада при закрытии):**

1.  `hmi.set("MT1.LU1.SGLU1.GRZDV1.ZDV1.Status", 0)` — закрыть (если не закрыта)

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.GRZDV1.Status")` → 0

4.  `hmi.get("MT1.LU1.SGLU1.State.Activity")` → false

5.  `hmi.get("MT1.LU1.SGLU1.State.Visible")` → false

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")` → false

7.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")` — нет (SGLU_CONTROLON может быть false)

8.  `hmi.get("MT1.LU1.State.CounterKIP")` — **проверить**: считает ли KIP1 (Press валидный, но Visible=false)


**Действия (часть 2: проверка при открытии):**

1.  `hmi.set("MT1.LU1.SGLU1.GRZDV1.ZDV1.Status", 2)` — открыть

2.  `WAIT(event)`

3.  `hmi.get("MT1.LU1.SGLU1.State.Activity")` → true

4.  `hmi.get("MT1.LU1.SGLU1.State.Visible")` → true

5.  `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")` → true

6.  `hmi.get("MT1.LU1.State.CounterKIP")` — KIP1 учитывается


**Ожидаемый результат:**

*   Шаг 4: `SGLU1_ACTIVITY = false`

*   Шаг 5: `SGLU1_VISIBLE = false` (Priority=1, ControlOn=false, Activity=false → по формуле: (false AND true) OR (false AND 1) = false)

*   Шаг 6: `KIP1_VISIBLE = false` (SGLU невидим)

*   Шаг 8: `LU1_COUNTERKIP` — **зафиксировать фактическое поведение**. Ожидание: KIP1 считается (т.к. Press валидный, CounterKIP считает по invalid, а не по Visible)

*   Шаг 11: `SGLU1_ACTIVITY = true`

*   Шаг 12: `SGLU1_VISIBLE = true` (Priority=1, ControlOn=false, Activity=true → (false AND true) = true)

*   Шаг 13: `KIP1_VISIBLE = true`

*   Шаг 14: `LU1_COUNTERKIP` увеличен на 1 (KIP1 учтён)


**Критический вопрос (зафиксировать):** `CounterKIP` считает по `KIP_PRESS.invalid` или по `KIP_VISIBLE`? Если по invalid — датчик «невидимый» (Visible=false) всё равно учитывается в `CounterKIP`. Это важно для корректности `IndicatorLink`.
**Teardown:** `RESET()`


##### **HY-CALC-084 — Каскад: Control=1, все KIP отключены**


**Требование:** R-HYDR-038, R-HYDR-028 **Описание:** При Control=1 все датчики отключены. `CounterKIP = 0` → `AlmKIPAllLink = true`. Алармы давления не генерируются (все Disable=true). Нет противоречия: аларм связи есть, алармов давления нет.

**Предусловие:**


*   `LU1_CONTROL = 1` (на контроле)

*   `KIP1_PRESSSTATION = 5.0`, `KIP1_PRESSRANGEMAX = 5.2` (зафиксированы)

*   `KIP1_PRESS = 5.5` (высоко, но датчик отключён)

*   Все 5 KIP: `Disable = true`



**Действия:**


1.  `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", true)` (и все остальные)

2.  `WAIT(2c)`

3.  `hmi.get("MT1.LU1.State.CounterKIP")`

4.  `hmi.get("MT1.LU1.Alm.AlmKIPAllLink")`

5.  `hmi.get("MT1.LU1.State.IndicatorLink")`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`

7.  `hmi.get("MT1.LU1.Alm.AlmPressDev")`

8.  `hmi.get("MT1.LU1.State.IndicatorControl")`



**Ожидаемый результат:**


*   Шаг 3: `LU1_COUNTERKIP = 0`

*   Шаг 4: `LU1_ALMKIPALLLINK = true`

*   Шаг 5: `LU1_INDICATORLINK = 2` (красный)

*   Шаг 6: `KIP1_ALMDEVMAXRANGE = false` (Disable=true, не участвует)

*   Шаг 7: `LU1_ALMPRESSDEV = false` (нет активных отклонений)

*   Шаг 8: `LU1_INDICATORCONTROL = 1` (Norm — нет отклонений) или `0` (зависит от реализации)



**Критерий:** Нет противоречия — аларм связи (IndicatorLink=2) сосуществует с отсутствием алармов давления. Диспетчер видит: «нет связи, но и нет аварийного давления».

**Teardown:** `RESET()`



##### **HY-CALC-085 — Каскад: SGLU_CONTROLON=false → KipPressRangeAlg vs KipAlmDevRangeMaxMinAlg**


**Требование:** R-HYDR-028 **Описание:** `KipPressRangeAlg` требует `SGLU_CONTROLON=true`. `KipAlmDevRangeMaxMinAlg` — требует только `Control=1 AND Disable=0`. При `SGLU_CONTROLON=false`: `AlmDevMaxRange` может быть true, но `PressRangeAlarm` — false.

**Предусловие:**


*   `LU1_CONTROL = 1`

*   `SGLU1_CONTROLON = false`

*   `KIP1_DISABLE = false`

*   `KIP1_PRESSSTATION = 5.0`, `KIP1_PRESSRANGEMAX = 5.2`

*   `KIP1_PRESS = 5.5` (выше границы)



**Действия:**


1.  `WAIT(event)`

2.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`

4.  `hmi.set("MT1.LU1.SGLU1.State.ControlOn", true)`

5.  `WAIT(event)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")`

7.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.PressRangeAlarm")`



**Ожидаемый результат:**


*   Шаг 2: `KIP1_ALMDEVMAXRANGE = true` (5.5 > 5.2, Control=1, Disable=false)

*   Шаг 3: `KIP1_PRESSRANGEALARM = false` (SGLU_CONTROLON=false → #9 не срабатывает)

*   Шаг 6: `KIP1_ALMDEVMAXRANGE = true`

*   Шаг 7: `KIP1_PRESSRANGEALARM = true` (SGLU_CONTROLON=true → #9 срабатывает)



**Обоснование:** Два разных аларма с разными условиями. `AlmDevMaxRange` — «давление выше границы», `PressRangeAlarm` — «давление вне диапазона на контролируемом сегменте».

**Teardown:** `RESET()`




## 4. Правила исполнения

1.  **Изоляция:** Каждый тест стартует с начального состояния. Teardown обязателен.

2.  **Ожидание:** Всегда использовать `WAIT(cycle)` с запасом 5 с. Никогда не ждать «на глаз».

3.  **Проверка:** Проверять **и** тег (hmi.get), **и** событие в топике alarm (kafka.consume) (если актуально для сценария).

4.  **Граничные значения:** При проверке границ — всегда тестировать ровно на границе (без аларма) и за границей (с алармом).

5.  **Исправление:** При сбое — фиксировать фактический результат, не исправлять ожидаемый.

6.  **Номер сценария:** В репорте указывать HY-CALC-xxx.

7.  **Consumer Lag:** При красном тесте (непройден) дополнительно зафиксировать в Allure-репорте:

    *   `kafka.lag(cspa-main, group=hydro-calculation)` — текущий consumer lag

    *   `kafka.lag(model_main_{id}, group=hydro-calculation)` — если тест в режиме моделирования


    Формат: `kafka_lag: {topic}={lag_value} (threshold: 100 msgs)`. Если lag > 100(например) — пометить в репорте: «⚠️ Возможно проблема в большом консьюмер лаге».
    Это помогает отличить алгоритм считает не так или данные ещё не дошли до расчётного ядра.


## 5. Чек-лист подготовки стенда

| # | Шаг | Апи |  |
| --- | --- | --- | --- |
| 1 | hydro-calculation развёрнут |  |  |
| 2 | hmi-backend развёрнут, API доступен |  |  |
| 3 | Kafka развёрнут, топики main/alarm/model_* существуют |  |  |
| 4 | PostgreSQL: ИМ загружено (конфигурация ТУ, KIP, UR, PLTM, GRZDV, ZDV) |  |  |
| 5 | Redis: кэш ИМ загружен |  |  |
| 6 | ClickHouse: schema готова, тестовые данные для HY-CALC-064 |  |  |
| 7 | Конфигурация ТУ для автотестов выбрана и загружена в data-manager |  |  |
| 8 | Значения ИМ зафиксированы (ΔMax, ΔMin, DensLimit, PressRateLimit, LimitKIP, TimeIntSetStation, ControlAutoTimeOut) |  |  |
| 9 | Начальное состояние подтверждено: Control=0, AutoControlOn=false, все Disable=false |  |  |
| 10a | hmi-backend: health | `GET http://hmi-backend:8080/actuator/health` | `{"status":"UP"}` |
| 10b | hmi-backend: прогревание завершено | `GET http://hmi-backend:8080/diag/instance` | HTTP 200, тело = app-id (не 503) |
| 10c | hmi-backend: WS V2 доступен | WS-подключение к `ws://hmi-backend:8080/v2/hotlink`, отправить `{"cmd":"PING","id":"test"}` | Получен `PONG` с `id:"test"` в течение 5 с |
| 10d | hmi-backend: доступ к тестовым тегам | `GET http://hmi-backend:8080/v2/tag-get?tagName=MT1.LU1.SGLU1.KIP1.TI.Press` + `X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]` | HTTP 200, тело содержит `"tag"` и `"data"` |
| 10e | hmi-backend: запись тега работает | `POST /v2/tag-set` с тестовым тегом | HTTP 200 |
| 10f | hmi-backend → Kafka: значение попадает в `cspa-main` | `kafka.consume("cspa-main", filter="tag=MT1.LU1.SGLU1.KIP1.TI.Press")` после шага 10e | Сообщение получено в течение 5 с |

* * *

## 6. Допущения

| # | Описание | Статус | Пояснение |
| --- | --- | --- | --- |
| 1 | `hmi.set` (`POST /v2/tag-set`) публикует значение в Kafka **hot topics** (конфигурируются через `CSPA_TOPICS` / `TopicRouteConfig`). Для оперативного режима hot topic должен совпадать с `cspa-main`. Для моделирования — с `model_main_{sessionId}` | **Допущение** | hmi-backend сам не знает о `cspa-main` / `model_main_*`. Механизм привязки: env `CSPA_TOPICS` или `TopicRouteConfig`. **Верифицируется чек-листом 10f** |
| 2 | `hmi.get` (`GET /v2/tag-get`) читает текущее значение из **DataStream** (Kafka consumer → `TagValueStreamHandler` → буфер). Кэш метаданных тегов — `TagInfoService` (TTL **5 с**) | **Подтверждено документацией** | hmi-backend не читает напрямую из Redis для значений тегов |
| 3 | При `POST /v2/tag-set` hmi-backend **валидирует тип** значения против типа тега (`ProtoValidator.validate()`). Несоответствие → HTTP 400 | **Подтверждено документацией** | В автотестах: значения передаются как строки (`"5.0"`, `"true"`) |
| 4 | До завершения **AppWarmUp** все бизнес-REST-эндпоинты hmi-backend возвращают **503**. Разрешены: `/actuator/*`, `/health*`, `/diag/*` | **Подтверждено документацией** | В чек-листе: после `actuator/health = UP` дождаться `diag/instance = 200` |
| 5 | WS V2 hmi-backend агрегирует подписки в окне **50 мс** (`tn-scada.hmi.sample-time`) | **Подтверждено документацией** | В автотестах: после `TAG_SET` ожидание `SUB_ANSWER` — до 200 мс (запас) |
| 6 | WS V2 hmi-backend: `Minuteman` закрывает неактивные сессии (`stale-time` = 3600 с), будит при `wake-time` = 30 с | **Подтверждено документацией** | В длительных сценариях: `PING` каждые 15–20 с |
| 7 | `hmi.history` (`POST /v2/tags-get-history`) читает из **ClickHouse** напрямую (не из Kafka-буфера) | **Подтверждено документацией** | Для сценариев HY-CALC-058/059/064: данные должны быть уже записаны в CH |
| 8 | Все значения, помеченные «из ИМ» — **примеры**. Конкретные значения фиксируются при подготовке стенда | **Допущение** |  |
| 9 | Тег `LU1_TU_TRANSITIONCONTROLON` — **допущение**. Реальный механизм перехода в Control=2 уточняется | **Допущение** |  |
| 10 | Формат JSON плана перекачки — **допущение** | **Допущение** |  |
| 11 | Приоритет в alarm (WARNING/CRITICAL/ALARM) — **допущение** | **Допущение** |  |
| 12 | Обновление ИМ в runtime (изменение значений в PostgreSQL/Redis без рестарта hydro-calculation). Предполагается что для тестов конфигурация фиксируется на этапе подготовки и не изменяется во время тест-ранна. Если потребуется динамическое изменение — использовать рестарт или отдельный сценарий | **Допущение** |  |




## 7. Полнота покрытия

### 7.1 Алгоритмы

Всего в репозитории hydro-calculation реализован 43 алгоритма
Сценарии покрывают полностью 42 алгоритмов
Не покрыт (осознанно) 1 алгоритм - ChecklistAlg (не влияет на расчеты, возможно покрыть только юнит тестами (разработчиками бэка))
**Покрытие по алгоритмам: 42/43 = 97.7%**

### **7.2 Реестр требований**

Всего требований 101, из них можно отнести к гидрокалькуляциям 43 требования
| Метрика | Значение |  |
| --- | --- | --- |
| Полное покрытие | **42 / 43 = 97.7%** | **R-HYDR-001–007, 009*, 010–014, 016–043** |

# **hydro-history-and-model: тест план**



## Легенда источников

|  |  |
| --- | --- |
| **ТРП** | Технические требования — проект ЭВОСКАДА/Гидроуклон |
| **РА** | Руководство Администратора |
| **ИО** | Информационное обеспечение (таблицы параметров LU, KIP, SGLU, UR, PLTM…) |
| **СИМ** | Сервис моделирования и истории (v2) (3 режима, диаграммы) |
| **КД** | Конструктивная документация mod-hist (кодовая база) |
| **HYDRO** | ТЗ hydro-calculation (алгоритмы, ИМ) |

* * *



## 1. Описание микросервиса mod-hist

### 1.0 Назначение и контекст

**mod-hist** (hydro-history-and-model) — сервис управления сессиями моделирования и пересчёта истории для системы СДКУ Гидроуклон. Его задача — предоставлять операторам и системам верхнего уровня возможность:

1.  **Запускать сессии расчёта** в одном из трёх режимов (`historical`, `modelling`, `timeshift`)

2.  **Сохранять/воспроизводить сессии** (play-model)

3.  **Обмениваться данными** с внешними системами (импорт XLSX/ZIP_CSV, экспорт отчётов)

4.  **Отслеживать прогресс** расчёта (watermark — отметка времени, до которой обработаны данные)

5.  **Управлять жизненным циклом сессии** (создание → запуск → пауза → остановка → закрытие → удаление)

6.  **Сохранять значения и алармы** (ValueSaver, AlarmSaver)


Микросервис **не выполняет гидравлические расчёты сам** — он управляет **hydro-calculation** через Kafka-команды и передаёт ему входные данные. mod-hist является **оркестратором**: он знает, что считать, когда, и куда записать результат, но сам не считает напоры и дебалансы.

#### Три режима работы (ProcessingMode)

| Код | Значение | Описание | Источник данных | Тема Kafka |
| --- | --- | --- | --- | --- |
| 0 | `historical` | Ускоренный перерасчёт истории из ClickHouse. SpeedFactor 0.25×–60×. Автоматическое завершение по targetTime. | ClickHouse | `model_main_{sessionId}` |
| 1 | `modelling` | Полное моделирование. Оператор задаёт входные параметры вручную (hmi.set) или из файла. Ручное управление временем (advance). | Ручной ввод / импорт | `model_main_{sessionId}` |
| 2 | `timeshift` | Сдвиг времени контроля. Перенос момента постановки на контроль на другой период. Использует сохранённые данные (saved/imported). | Сохранённая сессия / импорт | `model_main_{sessionId}` |

#### Жизненный цикл сессии (SessionStatus — 13 состояний)

```
CREATED(0) → OPENING(1) → PLAYING(3) → PAUSED(2) → PLAYING(3) → DONE(8)
                  │           │
                  │           ├──→ SAVING(4) → SAVED(5)
                  │           │           │
                  │           │           └→ CANCELLING → CANCELLED
                  │           │
                  │           ├──→ ERROR(12) → [retry → PLAYING(3)]
                  │           │           │
                  │           │           └→ CLOSING(10) → CLOSED(11)
                  │           │
                  │           └──→ CLOSING(10) → CLOSED(11) → DELETED(9)
                  │
                  └──→ ERROR(12)
```



**Полный реестр состояний сессии:**
| Код | Статус | Описание | Переходы |
| --- | --- | --- | --- |
| 0 | `CREATED` | Сессия создана. Параметры заданы, но ещё не запущена. | → OPENING (start), → CLOSING (close без запуска) |
| 1 | `OPENING` | Промежуточное: идёт инициализация (подписка Kafka, загрузка из CH, отправка START). | → PLAYING (успех), → ERROR (сбой) |
| 2 | `PAUSED` | Приостановлена. Watermark зафиксирован. Ожидает resume. | → PLAYING (resume), → CLOSING (close) |
| 3 | `PLAYING` | Активно работает. Watermark движется. Основной рабочий статус. | → PAUSED (pause), → DONE (auto-stop), → SAVING (save), → CLOSING (close), → ERROR (сбой) |
| 4 | `SAVING` | Идёт сохранение сессии (написание в CH/Blob). | → SAVED (успех), → ERROR (сбой), → CANCELLING (отмена) |
| 5 | `SAVED` | Сессия сохранена. Готова к воспроизведению (play-model). | → CLOSING (close), → DELETED |
| 6 | `IMPORTING` | Идёт импорт данных (XLSX/ZIP_CSV). | → IMPORTED (успех), → ERROR (сбой) |
| 7 | `IMPORTED` | Импорт завершён. Данные в буфере. | → OPENING (start), → CLOSING |
| 8 | `DONE` | Остановлена. Watermark зафиксирован. Ресурсы ещё аллоцированы. | → CLOSING (close), → SAVING (save), → DELETED |
| 9 | `DELETED` | Удалена. Запись в БД помечена, данные очищены. | (терминальное) |
| 10 | `CLOSING` | Идёт закрытие: освобождение ресурсов (Kafka, Redis, CH). | → CLOSED (успех), → ERROR (сбой) |
| 11 | `CLOSED` | Закрыта. Ресурсы освобождены. Сессия недоступна для операций. | → DELETED (cleanup) |
| 12 | `ERROR` | Ошибка. Не удалось продолжить. | → PLAYING (retry), → CLOSING (close), → CLOSED |

#### Режим historical (перерасчёт истории)

```
┌──────────┐      ┌──────────────┐       ┌─────────────────────────────────────────────────┐
│ Оператор │      │  hmi-backend │       │              mod-hist                           │
└────┬─────┘      └──────────────┘       │                                                 │
     │               │                   │  SessionWorker                                  │
     │               │                   │  ├─ создаёт сессию (startTime, targetTime,      │
     │               │                   │  │   speedRatio, targets)                       │
     │               │                   │  ├─ DataExchange: загружает из ClickHouse       │
     │               │                   │  │   (пагинация по 1000)                        │
     │               │                   │  ├─ WorkerExecutor: публикует в model_main_{id} │
     │               │                   │  │   с виртуальным ts (speedRatio)              │
     │               │                   │  ├─ отправляет START (Kafka: mod-hist-commands) │
     │               │                   │  └─ читает watermark, управляет прогрессом      │
     │               │                   └──────────────────┬──────────────────────────────┘
     │               │                                      │
     │               │         ┌────────────────────────────▼────────────────────────────┐
     │               │         │  ClickHouse (история)                                   │
     │               │         │  SELECT tag, value, invalid FROM history                │
     │               │         │  WHERE tag IN (targets) AND ts BETWEEN start AND target │
     │               │         │  ORDER BY ts LIMIT 1000 OFFSET {page*1000}              │
     │               │         └─────────────────────────────────────────────────────────┘
     ▼               ▼
 └─────────────────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────────────────┐
              │         Kafka: model_main_{sessionId}       │
              │  (виртуальный поток: вход + выход)          │
              │  {tag, ts, value, invalid}                  │
              │  ts = виртуальное время (≠ реальное)        │
              │  Реальный цикл: каждые 1000ms/speedRatio    │
              └─────────────────────┬───────────────────────┘
                                    │
                                    ▼
              ┌─────────────────────────────────────────────────────────────────┐
              │                     hydro-calculation                           │
              │  KafkaSource ← model_main_{sessionId} (сырые значения)          │
              │       │                                                         │
              │  CalculationCore (N алгоритмов)                                 │
              │       │                                                         │
              │  KafkaSink → model_main_{sessionId} (расчётные)                 │
              │  KafkaSink → model_alarm_{sessionId} (алармы)                   │
              └─────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
                           hmi-backend → WebSocket → Оператор
```




| # | Актор | Действие | Канал | Хранилище |
| --- | --- | --- | --- | --- |
| 1 | Оператор | `POST /v2/mod-hist/sessions/historical` | REST → mod-hist | Redis, PostgreSQL |
| 2 | mod-hist (DataExchange) | Загрузка истории из CH | HTTP → ClickHouse :8123 | ClickHouse (read) |
| 3 | mod-hist (WorkerExecutor) | Публикует пачки в `model_main_{id}` с виртуальным ts | Kafka producer | — |
| 4 | mod-hist | `START` (topic=model_main_{id}, speedRatio) | Kafka `mod-hist-commands` | — |
| 5 | hydro-calc | Читает `model_main_{id}`, считает | Kafka consumer | — |
| 6 | hydro-calc | Публикует результаты + алармы | Kafka `model_main_{id}` + `model_alarm_{id}` | — |
| 7 | mod-hist | Читает `model_main_{id}`, обновляет watermark = max(виртуальный ts) | Kafka consumer | Redis |
| 8 | mod-hist | Когда watermark ≥ targetTime → DONE | — | Redis, PostgreSQL |
| 9 | Оператор | Видит прогресс, результаты | WS + REST | — |

**Ключевые особенности:**

*   Данные по **отдельному** топику `model_main_{sessionId}` (не мешаются с оперативным)

*   Timestamps **виртуальные** (≠ реальное время) — mod-hist управляет темпом

*   Источник — **ClickHouse**

*   Hydro-calculation не знает, что это "модель" — просто читает topic


#### Режим modelling (моделирование)

```
┌──────────┐      ┌──────────────┐       ┌─────────────────────────────────────────────────┐
│ Оператор │      │  hmi-backend │       │              mod-hist                           │
└────┬─────┘      └──────────────┘       │                                                 │
     │               │                   │  SessionWorker                                  │
     │               │                   │  ├─ создаёт сессию (processingMode=modelling)   │
     │               │                   │  ├─ (опционально) импорт: XLSX/ZIP_CSV → буфер  │
     │               │                   │  ├─ hmi.set: оператор задаёт значения           │
     │               │                   │  ├─ advance: двигает virtualTime                │
     │               │                   │  ├─ публикует данные в model_main_{id}          │
     │               │                   │  └─ START (Kafka: mod-hist-commands)            │
     │               │                   └──────────────────┬──────────────────────────────┘
     │               │                                      │
     │               │         ┌────────────────────────────▼────────────────────────────┐
     │               │         │  Источники данных (выбирается один):                    │
     │               │         │  (A) Ручной ввод: hmi.set(tag, value) → Kafka           │
     │               │         │  (B) Файл импорта: XLSX/ZIP_CSV → буфер → advance       │
     │               │         │  (C) ClickHouse: аналогично historical, но оператор     │
     │               │         │      сам двигает время                                  │
     │               │         └─────────────────────────────────────────────────────────┘
     ▼               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
              ┌─────────────────────────────────────────────┐
              │         Kafka: model_main_{sessionId}       │
              │  {tag, ts, value, invalid}                  │
              │  ts = виртуальное (задаёт оператор)         │
              └─────────────────────┬───────────────────────┘
                                    │
                                    ▼
              ┌─────────────────────────────────────────────────────────────┐
              │                     hydro-calculation                       │
              │  CalculationCore (N алгоритмов)                             │
              │  KafkaSink → model_main_{sessionId} (расчётные)             │
              │  KafkaSink → model_alarm_{sessionId} (алармы)               │
              └─────────────────────┬───────────────────────────────────────┘
                                    │
                                    ▼
                       hmi-backend → WebSocket → Оператор
```

| # | Актор | Действие | Канал |
| --- | --- | --- | --- |
| 1 | Оператор | `POST /v2/mod-hist/sessions/modelling` | REST → mod-hist |
| 2a | Оператор | Импорт XLSX/ZIP_CSV | REST → mod-hist |
| 2b | Оператор | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 7.0)` | REST hmi-backend → Kafka `model_main_{id}` |
| 3 | mod-hist | `START` (topic=model_main_{id}) | Kafka `mod-hist-commands` |
| 4 | Оператор | `advance(seconds=60)` [псевдо] | REST → mod-hist |
| 5 | mod-hist | virtualTime += 60s. Публикует из буфера | Kafka producer |
| 6 | hydro-calc | Читает, считает | Kafka consumer |
| 7 | Оператор | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → 903 м | REST hmi-backend |

**Ключевые отличия от historical:**

*   **Оператор управляет временем** (advance), а не скоростью

*   Источник — **ручной ввод или файл** (не CH)

*   Нет целевого watermark: сессия идёт пока оператор не остановит

*   Можно моделировать «что если» на ходу


#### Режим timeshift (сдвиг времени контроля)

| # | Актор | Действие | Канал |
| --- | --- | --- | --- |
| 1 | Оператор | `POST /v2/mod-hist/sessions/time-shift` (startTime, shiftDuration, targets) | REST → mod-hist |
| 2 | mod-hist | Загружает сохранённые данные (saved/imported) для исходного периода | CH / Redis |
| 3 | mod-hist | Пересчитывает с сдвигим времени (virtualTime = startTime + shift) | Kafka `model_main_{id}` |
| 4 | hydro-calc | Считает по сдвинутым данным | Kafka consumer |
| 5 | Оператор | Видит результат: «что было бы, если контроль начался на 2 ч раньше» | WS + REST |

**Назначение:** оператор хочет оценить, как бы выглядел контроль, если бы он был поставлен в другой момент. Например, ТУ был остановлен в 14:00, а контроль поставлен в 15:00 — timeshift пересчитывает с 14:00.

* * *





* * *

### **1.1 Архитектура развёртывания**



```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Тестовый стенд                                   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                 mod-hist (Java Spring Boot)                     │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌────────────────┐  ┌────────────────────┐   │    │
│  │  │SessionWorker │  │   Watermark    │  │  WorkerExecutor    │   │    │
│  │  │(управление   │  │  (отметка      │  │  (исполнение       │   │    │
│  │  │  сессиями)   │  │   времени)     │  │   вычислений)      │   │    │
│  │  └──────────────┘  └────────────────┘  └────────────────────┘   │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌────────────────┐  ┌────────────────────┐   │    │
│  │  │ DataExchange │  │  ValueSaver    │  │  AlarmSaver        │   │    │
│  │  │(импорт/      │  │  (сохранение   │  │  (сохранение       │   │    │
│  │  │  экспорт)    │  │   значений)    │  │   алармов)         │   │    │
│  │  └──────────────┘  └────────────────┘  └────────────────────┘   │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌────────────────┐  ┌────────────────────┐   │    │
│  │  │  Cleanup     │  │  Report        │  │  HealthController  │   │    │
│  │  │  (очистка)   │  │  (отчёты)      │  │  (/actuator/health)│   │    │
│  │  └──────────────┘  └────────────────┘  └────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│         ▲                     ▲                   ▲                     │
│  ┌──────┴──────┐  ┌───────────┴───────┐  ┌────────┴─────────┐           │
│  │ Kafka       │  │ PostgreSQL        │  │ Redis/ClickHouse │           │
│  │ model_main_*│  │ (сессии, конфиг)  │  │ (ИМ, история,    │           │
│  │ cspa-main   │  │                   │  │  кэш)            │           │
│  └─────────────┘  └───────────────────┘  └──────────────────┘           │
│         ▲                     ▲                   ▲                     │
│  ┌──────┴──────┐  ┌───────────┴───────┐  ┌────────┴─────────┐           │
│  │hydro-calc   │  │ data-manager      │  │ hmi-backend      │           │
│  │(расчёты)    │  │ (ИМ, конфиг)      │  │ (операторский UI)│           │
│  └─────────────┘  └───────────────────┘  └──────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```





**Иерархия объектов:**

```
MT (магистральный трубопровод)
└─ LU (линейный участок)
    ├─ SGLU (сегмент участка)
    │   ├─ KIP (датчик давления)
    │   ├─ UR (расходомер)
    │   └─ PLTM (плотномер)
    ├─ GRZDV (группа задвижек)
    │   └─ ZDV (задвижка)
    └─ [другие объекты]
```

**В mod-hist иерархия дополняется сущностями сессии:**

```
Session (сессия)
├─ sessionId (UUID)
├─ mode (REAL_TIME / FAST / SIMULATION)
├─ status (CREATED / RUNNING / PAUSED / STOPPED / CLOSED)
├─ watermark (timestamp — до какого момента обработаны данные)
├─ targets (список LU/KIP/UR для расчёта)
├─ dataExchange (импорт/экспорт)
└─ resources (аллоцированные ресурсы: Kafka consumer group, Redis keys, CH queries)
```

* * *

### 1.2 Взаимодействие с внешними сервисами

| Сервис | Канал | Направление | Описание |
| --- | --- | --- | --- |
| **hmi-backend** | REST `POST /v2/tag-set` | ← вход (оператор → hmi-backend) | Запись значения тега. Body: `{"tag":"...","data":{"value":"...","invalid":false,"ts":...}}`. Заголовки: `X-USER-FULLNAME` (required), `X-USER-ALLOW-PATTERNS` (required) |
| **hmi-backend** | REST `GET /v2/tag-get?tagName=...` | ← вход (оператор → hmi-backend) | Чтение одного тега. Ответ: `{"tag":"...","data":{"value":"...","invalid":false,"ts":...,"ts2":...}}` |
| **hmi-backend** | REST `POST /v2/tags-set` | ← вход | Массовая запись. Body: массив `TagSetRequest` |
| **hmi-backend** | REST `GET|POST /v2/tags-get` | ← вход | Массовое чтение |
| **hmi-backend** | WS V2 `ws://hmi-backend:8080/v2/hotlink` | → выход (hmi-backend → клиент) | Подписка на изменения тегов (`SUBSCRIBE`), чтение (`TAG_GET`), запись (`TAG_SET`). Окно агрегации: **50 мс** |
| **hmi-backend** | WS V2 `PONG` | → выход | Heartbeat-ответ на `PING` |
| **hydro-calculation** | Kafka (`mod-hist-commands`) | → выход | Команды: START, STOP, CLOSE, SET_WATERMARK, PAUSE, RESUME |
| **hydro-calculation** | Kafka (`model_main_{id}`) | ← вход | Результаты расчётов |
| **data-manager** | HTTP GET / Redis | ← конфиг | Теги, уставки, профиль ИМ |
| **ClickHouse** | HTTP/SQL :8123 | ← история | Данные для historical; экспорт результатов |
| **Redis** | Redis Protocol | ←/→ кэш | Состояние сессий, watermark, буферы |
| **PostgreSQL** | JDBC | ←/→ | Метаданные сессий, результаты |
| **Kafka** | Producer/Consumer | ←/→ | Потоки данных и команд |

Примечание: hmi-backend выступает прокси между оператором/mod-hist и Kafka. Запись через tag-set публикует сообщение в Kafka (hot topics, конфигурируются через CSPA_TOPICS / TopicRouteConfig). Чтение — из DataStream (Kafka consumer → буферизация → подписчики).

### 1.3 Константы и числовые значения

| Константа | Значение | Конфиг | Описание |
| --- | --- | --- | --- |
| Таймаут подтверждения от hydro-calculation | 30 с | `SessionWorker.confirmTimeoutMs` | Если не ответил за 30 с → ERROR |
| Интервал проверки watermark | 5 с | `Watermark.checkIntervalMs` | Периодичность обновления |
| Максимум сессий одновременно | 10 | `SessionWorker.maxSessions` | Ограничение на активные сессии |
| Буфер данных | 10 000 сообщений | `WorkerExecutor.bufferSize` | Буфер (FIFO) |
| TTL сессии в Redis | 24 часа | `SessionWorker.sessionTTL` | Автозакрытие неактивных |
| Максимальная скорость | 60× (60000) | `FastMode.maxSpeedFactor` | Максимум speedRatio |
| Минимальная скорость | 0.25× (250) | `FastMode.minSpeedFactor` | Минимум speedRatio |
| Интервал записи в CH | 60 с | `DataExchange.exportInterval` | Экспорт результатов |
| Размер страницы (пагинация) | 1000 | `DataExchange.pageSize` | Записей за запрос к CH |
| Таймаут WebSocket | 60 с | `WsConfig.timeout` | Без ping → закрытие |
| Максимальный размер импорта | 50 МБ | `DataExchange.maxImportSize` | Ограничение файла |
| Интервал cleanup | 3600 с | `Cleanup.intervalMs` | Проверка устаревших сессий |
| Порог отставания watermark | 120 с | `Watermark.lagThreshold` | Предупреждение о lag |

**Допустимые значения speedRatio (как в UI):**
| UI | speedRatio (int) | Описание |
| --- | --- | --- |
| 0.25× | 250 | Замедление (для детального анализа) |
| 0.5× | 500 | Замедление |
| 1× | 1000 | Реальное время |
| 2× | 2000 | Ускорение |
| 5× | 5000 | Ускорение |
| 10× | 10000 | Значительное ускорение |
| 60× | 60000 | Максимальное ускорение |

* * *

### **1.4 Ключевые понятия и формулы**

**Watermark** — отметка времени (timestamp, ms), до которой обработаны данные.

```
Watermark = max(время последнего обработанного сообщения)
TargetWatermark = targetTime (для historical) / ∞ (для modelling)
Lag = TargetWatermark − Watermark
Progress% = ((Watermark − StartTime) / (TargetTime − StartTime)) × 100
```

**Скорость обработки (historical):**

```
speedRatio: int, где 1000 = ×1 (реальное время)
Виртуальный шаг = 1000ms / (speedRatio / 1000) = 1000000 / speedRatio мс

Пример: speedRatio = 2000 (2×) → шаг = 500 мс
Пример: speedRatio = 60000 (60×) → шаг ≈ 16.7 мс
```

**ETA (оценка времени до завершения):**

```
ETA = (TargetTime − Watermark) / speedRatio × 1000 (в мс реального времени)
```

**Формула напора (из реализации, HYDRO-75):**

```
h = (P / ρ) × 101970 + H

где:
  h — напор, м
  P — давление [KIP].TI.Press, кгс/см²
  ρ — плотность [KIP].TI.Ro, кг/м³ (если < 500 → использовать 500)
  H — высотная отметка [KIP].Height, м
     (если [KIP].State.Manual = true и invalid = false → [KIP].HeightCorrection)

Пример: P=7.0, ρ=850, H=63.5
  h = (7.0/850) × 101970 + 63.5 = 839.8 + 63.5 = 903.3 м
```

**Буфер:**


```
BufferCapacity = 10 000
Запись: BufferIndex = (BufferIndex + 1) % BufferCapacity
При переполнении: старые сообщения теряются (FIFO)
Аларм BUFFER_OVERFLOW: потеряно > 10% буфера за цикл
```



* * *



### 1.5 Режимы работы — детальное описание




#### historical

| Параметр | Значение |
| --- | --- |
| Источник | ClickHouse |
| Watermark | Движется со скоростью speedRatio |
| SpeedRatio | 250–60000 (0.25×–60×) |
| Целевой watermark | targetTime |
| Завершение | Автоматически при Watermark = TargetTime → DONE |
| Применение | Перерасчёт истории, верификация |

#### modelling

| Параметр | Значение |
| --- | --- |
| Источник | Ручной ввод (hmi.set) / импорт XLSX/ZIP_CSV |
| Watermark | Управление оператором (advance) |
| SpeedRatio | Не применим |
| Целевой watermark | Неограничен |
| Завершение | По команде оператора (stop) |
| Применение | «Что если», обучение, отладка |

#### timeshift

| Параметр | Значение |
| --- | --- |
| Источник | Сохранённая сессия (saved) / импорт (imported) |
| Watermark | Сдвигается на shiftDuration |
| SpeedRatio | 1000 (×1) по умолчанию |
| Целевой watermark | startTime + shiftDuration |
| Завершение | Автоматически |
| Применение | Оценка «что было бы при ином моменте контроля» |

* * *

### 1.6 Справочник enum-значений

#### ProcessingMode

| Код | Значение |
| --- | --- |
| 0 | `historical` |
| 1 | `modelling` |
| 2 | `timeshift` |

#### SessionStatus

| Код | Значение |
| --- | --- |
| 0 | `CREATED` |
| 1 | `OPENING` |
| 2 | `PAUSED` |
| 3 | `PLAYING` |
| 4 | `SAVING` |
| 5 | `SAVED` |
| 6 | `IMPORTING` |
| 7 | `IMPORTED` |
| 8 | `DONE` |
| 9 | `DELETED` |
| 10 | `CLOSING` |
| 11 | `CLOSED` |
| 12 | `ERROR` |

#### SaveSessionStatus

| Код | Значение |
| --- | --- |
| 0 | `CREATED` |
| 1 | `SAVING` |
| 2 | `SAVED` |
| 3 | `CANCELLING` |
| 4 | `CANCELLED` |
| 5 | `ERROR` |

#### HistoryImportStatus

| Код | Значение |
| --- | --- |
| 0 | `CREATED` |
| 1 | `RUNNING` |
| 2 | `DONE` |
| 3 | `ERROR` |
| 4 | `DELETED` |

#### ImportFormat

| Код | Значение |
| --- | --- |
| 0 | `XLSX` |
| 1 | `ZIP_CSV` |

#### PlayerMode

| Код | Значение |
| --- | --- |
| 0 | `Play` |
| 1 | `Stop` |
| 2 | `SetSpeed` |
| 3 | `Seek` |

#### SourceMode

| Код | Значение |
| --- | --- |
| 0 | `saved` |
| 1 | `imported` |
| 2 | `history` |

#### WatermarkState

| Код | Значение |
| --- | --- |
| 0 | `INIT` |
| 1 | `MOVING` |
| 2 | `STALLED` |
| 3 | `COMPLETE` |

#### SessionEventType (WebSocket)

| Код | Значение |
| --- | --- |
| 0 | `SESSION_CREATED` |
| 1 | `SESSION_OPENED` |
| 2 | `SESSION_PAUSED` |
| 3 | `SESSION_RESUMED` |
| 4 | `SESSION_DONE` |
| 5 | `SESSION_CLOSED` |
| 6 | `SESSION_ERROR` |
| 7 | `WATERMARK_UPDATED` |
| 8 | `WATERMARK_STALLED` |
| 9 | `WATERMARK_COMPLETE` |
| 10 | `DATA_IMPORT_COMPLETE` |
| 11 | `DATA_EXPORT_COMPLETE` |
| 12 | `BUFFER_OVERFLOW` |
| 13 | `SPEED_CHANGE` |
| 14 | `SESSION_SAVED` |
| 15 | `SESSION_SAVING` |
| 16 | `SESSION_DELETED` |

* * *

### 1.7 Иерархия тегов

Имя тега в системе однозначно определяет объект и его параметр:
`{MT}.{LU}.{SGLU}.{KIP/UR/PLTM/GRZDV/ZDV}.{TI/State/Alm/TU}.{Параметр}      `

### 1.8 Обозначения и соглашения для сценариев


**REST mod-hist (реальные endpoint'ы из реализации):**

| Обозначение | Метод | Путь | Описание |
| --- | --- | --- | --- |
| `api.createHistorical(params)` | POST | `/v2/mod-hist/sessions/historical` | Создание historical |
| `api.createModelling(params)` | POST | `/v2/mod-hist/sessions/modelling` | Создание modelling |
| `api.createTimeshift(params)` | POST | `/v2/mod-hist/sessions/time-shift` | Создание timeshift |
| `api.playModel(sessionId)` | POST | `/v2/mod-hist/sessions/play-model/{id}` | Воспроизведение сохранённой |
| `api.save(sessionId)` | POST | `/v2/mod-hist/sessions/{id}/save` | Сохранение сессии |
| `api.import_(sessionId, file)` | POST | `/v2/history-import/...` | Импорт (HistoryImportController) |
| `api.export_(sessionId, format)` | GET/POST | `/v2/report/...` | Экспорт (ReportController) |


**REST mod-hist (псевдо-ручки, не подтверждены в реализации):**


> ⚠️ **Псевдо-ручка** — endpoint существует как абстракция в тестплане - по аналогии с ТЗ. Реальный путь/метод может отличаться. Перед выполнением сценария требуется верификация по коду.


| Обозначение | Метод | Путь | Описание |
| --- | --- | --- | --- |
| `api.start(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/start` | Запуск сессии |
| `api.stop(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/stop` | Остановка |
| `api.pause(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/pause` | Пауза |
| `api.resume(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/resume` | Возобновление |
| `api.close(sessionId)` ⚠️ | DELETE | `/v2/mod-hist/sessions/{id}` | Закрытие |
| `api.delete(sessionId)` ⚠️ | DELETE | `/v2/mod-hist/sessions/{id}/delete` | Удаление |
| `api.get(sessionId)` ⚠️ | GET | `/v2/mod-hist/sessions/{id}` | Чтение |
| `api.list(filters)` ⚠️ | GET | `/v2/mod-hist/sessions` | Список |
| `api.advance(sessionId, seconds)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/advance` | Продвижение (modelling) |
| `api.watermark(sessionId)` ⚠️ | GET | `/v2/mod-hist/sessions/{id}/watermark` | Watermark |
| `api.progress(sessionId)` ⚠️ | GET | `/v2/mod-hist/sessions/{id}/progress` | Прогресс |
| `api.setSpeed(sessionId, ratio)` ⚠️ | PUT | `/v2/mod-hist/sessions/{id}/speed` | Смена скорости |
| `api.retry(sessionId)` ⚠️ | POST | `/v2/mod-hist/sessions/{id}/retry` | Повтор после ERROR |


**hmi-backend (для установки/чтения значений):**

#### REST-вызовы (рекомендуемые для автотестов)

| Абстракция в тестплане | Реальный endpoint | Метод | Body / Query | Заголовки |
| --- | --- | --- | --- | --- |
| `hmi.set(tag, value, invalid?)` | `/v2/tag-set` | POST | `{"tag":"MT1.LU1.SGLU1.KIP1.TI.Press","data":{"value":"7.0","invalid":false,"ts":1705300000000}}` | `X-USER-FULLNAME: Test`, `X-USER-ALLOW-PATTERNS: ["MT1..*"]`, `Content-Type: application/json` |
| `hmi.setBatch(tags[])` | `/v2/tags-set` | POST | `[{"tag":"...","data":{"value":"...","invalid":false,"ts":...}}, ...]` | те же |
| `hmi.get(tag)` | `/v2/tag-get` | GET | Query: `tagName=MT1.LU1.SGLU1.KIP1.TI.Press` | `X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]` (default `[".*"]`) |
| `hmi.getBatch(tags[])` | `/v2/tags-get` | GET / POST | Query: `tagNames=t1&tagNames=t2` или body: `["t1","t2"]` | те же |


**Формат ответа** `hmi.get`**:**

```
{ "tag": "MT1.LU1.SGLU1.KIP1.TI.Press", "data": { "value": "7.0", "invalid": false, "ts": 1705300000000, "ts2": 1705300000000 } }
```

**Важно:** В V2 value — плоский JSON-примитив внутри `data.value` (не вложенная типизация `{"doubleVar": 7.0}`). Тип валидируется сервером через `ProtoValidator` против типа тега. Несоответствие → HTTP 400 + `ValueConversionException`.

#### WebSocket V2 (для подписки на изменения)

**Путь: ~** `ws://hmi-backend:8080/v2/hotlink`
**Формат кадра:**

```
{ "cmd": "SUBSCRIBE", "id": "req-001", "args": ["MT1.LU1.SGLU1.KIP1.TI.Press", "MT1.LU1.SGLU1.KIP1.TI.Head"], "headers": { "X-USER-GET-ALLOW-PATTERNS": "["MT1\..*"]" } }
```


| Команда | Назначение | Args | Headers |
| --- | --- | --- | --- |
| `SUBSCRIBE` | Подписка на изменения тегов | `["tag1","tag2"]` | `X-USER-GET-ALLOW-PATTERNS` |
| `UNSUBSCRIBE` | Отписка | `["tag1","tag2"]` | — |
| `UNSUBSCRIBE_ALL` | Сброс всех подписок сессии | `null` | — |
| `TAG_GET` | Одноразовое чтение | `["tag1"]` | `X-USER-GET-ALLOW-PATTERNS` |
| `TAG_SET` | Запись значения | `[{"tag":"...","data":{"value":"123"}}]` | `X-USER-ALLOW-PATTERNS`, `X-USER-FULLNAME` |
| `PING` | Heartbeat | `{"id":"ping-001"}` | — |

**Ответы WS V2:**
| Тип | Когда приходит |
| --- | --- |
| `SUB_ANSWER` | Пакет значений по подписке (агрегация в окне **50 мс**) |
| `CALL_ANSWER` | Ответ на `TAG_GET` / `TAG_SET` |
| `CALL_ERROR` | Ошибка выполнения |
| `PONG` | Ответ на `PING` |

> **Примечание по маршрутизации в Kafka:** hmi-backend публикует `tag-set` в hot topics (конфигурируются через `CSPA_TOPICS` / `TopicRouteConfig`). Для mod-hist необходимо, чтобы hot topic совпадал с `model_main_{sessionId}` (или mod-hist читал из того же потока). **Конкретный механизм привязки остаётся допущением**


**Kafka / Redis / CH:**

| Обозначение | Описание |
| --- | --- |
| `kafka.send(topic, msg)` | Прямая отправка в Kafka |
| `kafka.consume(topic, filter, timeout)` | Ожидание сообщения |
| `redis.get(key)` / `redis.set(key, value)` | Чтение/запись Redis |
| `ch.query(sql)` | SQL-запрос к ClickHouse :8123 |
| `pg.query(sql)` | SQL-запрос к PostgreSQL :5432 |


**Общие:**

| Обозначение | Описание |
| --- | --- |
| `WAIT(n)` | Слепое ожидание n секунд |
| `WAIT(event, timeout)` | Ожидание события с таймаутом |
| `RESET()` | Cleanup (раздел 2.5) |
| `CONFIG_X = Y` | Значение, заданное в конфигурации |


**Правила ожидания:**


*   REST: таймаут 30 с

*   WS: таймаут 60 с

*   Kafka: max(interval, 30) с

*   `api.get` — допустимо 3 повторных запроса с интервалом 2 с



**Заголовки (все REST):**



| Заголовок | Для чего | Обязательность |
| --- | --- | --- |
| `X-USER-FULLNAME` | Идентификация (аудит) | **Required** при `tag-set` |
| `X-USER-ALLOW-PATTERNS` | Разрешение на запись | **Required** при `tag-set` |
| `X-USER-GET-ALLOW-PATTERNS` | Разрешение на чтение | Optional (default `[".*"]`) при `tag-get` |
| `X-USER-FORBIDDEN-PATTERNS` | Чёрный список (запись) | Optional, **приоритет над allow** |
| `X-USER-GET-FORBIDDEN-PATTERNS` | Чёрный список (чтение) | Optional |
| `X-USER-IP` | IP для аудита | Optional |
| `X-USER-FULLNAME` | Идентификация (аудит) | **Required** при `tag-set` |
| `X-USER-ALLOW-PATTERNS` | Разрешение на запись | **Required** при `tag-set` |
| `X-USER-GET-ALLOW-PATTERNS` | Разрешение на чтение | Optional (default `[".*"]`) при `tag-get` |
| `X-USER-FORBIDDEN-PATTERNS` | Чёрный список (запись) | Optional, **приоритет над allow** |
| `X-USER-GET-FORBIDDEN-PATTERNS` | Чёрный список (чтение) | Optional |
| `X-USER-IP` | IP для аудита | Optional |


**Заголовки (WS, в поле** `headers`**):**

```
"X-USER-ALLOW-PATTERNS": "[\"MT1\\..*\"]"
"X-USER-FULLNAME": "Test"
```

**WS V2: эти заголовки передаются в поле** `headers` **JSON-кадра (как строки JSON-массивов)**

```
"headers": {
  "X-USER-ALLOW-PATTERNS": "[\"MT1\\..*\"]",
  "X-USER-FULLNAME": "Test"
}
```



**Ограничения hmi-backend, влияющие на автотесты:**

1.  **503 до готовности:** Все бизнес-эндпоинты возвращают 503 до завершения AppWarmUp. В автотесте: после `actuator/health = UP` дождаться `GET /diag/instance` → 200 (интервал опроса: 1 с, max 30 с).

2.  **Валидация типа:** `POST /v2/tag-set` с несовпадающим типом значения (например, `"value":"abc"` для DOUBLE-тега) → **HTTP 400**. В автотесте: использовать числовые значения как строки (`"7.0"`, не `7.0`).

3.  **Agregation WS V2 (50 мс):** При подписке через WS V2 значения приходят пакетом не чаще чем раз в 50 мс. В автотесте: после `TAG_SET` ожидать `SUB_ANSWER` с таймаутом ≥ 200 мс.

4.  **Minuteman (30 с):** WS-сессия hmi-backend без активности будится каждые 30 с (`wake-time`), закрывается через 3600 с (`stale-time`). В длительных сценариях (> 2 мин) отправлять `PING` каждые 15–20 с.

5.  **Kafka-маршрутизация:** hmi-backend не знает о `model_main_{sessionId}`. Привязка hot topic к топику сессии — ответственность конфигурации (см. допущение 17). Если hot topic ≠ `model_main_{sessionId}` — значения не дойдут до hydro-calculation.


* * *

`   `

## 2. ТЕСТОВЫЙ СТЕНД

### 2.1 Компоненты

| Компонент | Роль | Примечание |
| --- | --- | --- |
| **mod-hist** | Тестируемый сервис | Java Spring Boot |
| **hydro-calculation** | Расчётный сервис | Java Spring Boot |
| **hmi-backend** | Операторский API + WS | REST порт **8080**; WS V2: `ws://hmi-backend:8080/v2/hotlink`; WS V1: `ws://hmi-backend:8080/hotlink` |
| **Kafka** | Брокер | Порт 9092 |
| **PostgreSQL** | Сессии, ИМ | Порт 5432 |
| **Redis** | Кэш, watermark, буферы | Порт 6379 |
| **ClickHouse** | История, экспорт | Порт 8123 |



### 2.2 Топики Kafka

| Топик | Назначение | Формат |
| --- | --- | --- |
| `cspa-main` | Оперативный поток (вход + выход) | `{tag, ts, value, invalid}` |
| `model_main_{sessionId}` | Виртуальный поток (historical/modelling/timeshift) | `{tag, ts, value, invalid}` |
| `model_alarm_{sessionId}` | Алармы сессии | `{tag, ts, value, text, priority, state}` |
| `mod-hist-commands` | Команды → hydro-calc | `{sessionId, command, params, ts}` |
| `mod-hist-results` | Результаты → mod-hist | `{sessionId, tag, value, ts}` |

**Команды mod-hist → hydro-calc:** `START`, `STOP`, `CLOSE`, `SET_WATERMARK`, `PAUSE`, `RESUME`

### 2.3 Начальное состояние

*   mod-hist, hydro-calculation, hmi-backend — UP, **прогревание завершено** (`HmiEvoService.isReady() = true`). Проверка: `GET http://hmi-backend:8080/actuator/health` → `{"status":"UP"}`. До завершения AppWarmUp бизнес-эндпоинты возвращают **503** (`ServerReadyRestInterceptor`). Допустимо: `/actuator/*`, `/health*`.

*   Kafka: топики существуют

*   PostgreSQL: таблицы `sessions`, `session_results` — пусты

*   Redis: `session:*` отсутствуют

*   ClickHouse: тестовая история ≥ 24 ч для MT1.LU1 (≥ 10 000 сообщений)

*   Конфигурация ТУ1 загружена в data-manager

*   `api.list()` → пустой массив

*   `LU.State.Control = 0`, все `Disable = false`


### 2.4 Cleanup

После каждого тест-кейса:

1.  Все активные сессии → `api.stop` → `api.close`

2.  Redis: `session:{id}:*` удалены

3.  PostgreSQL: записи удалены или помечены CLOSED/DELETED

4.  Kafka: consumer groups удалены

5.  ClickHouse: тестовые данные удалены

6.  hydro-calculation: буферы очищены (CLOSE)

7.  hmi-backend: WS-подписки отключены (команда `UNSUBSCRIBE_ALL` через `ws://hmi-backend:8080/v2/hotlink` или закрытие WS-сокета)

8.  hmi-backend: сессия WS закрыта (если использовалась для TAG_SET/SUBSCRIBE в рамках сценария)


* * *

## 3. СЦЕНАРИИ АВТОТЕСТОВ

### **3.1 Управление сессиями: жизненный цикл**

* * *

#### HY-HIST-001 — Создание historical-сессии: базовый сценарий

**Требование:** R-HYDR-050, R-HYDR-051
**Описание:** Оператор создаёт сессию historical для перерасчёта истории за период 08:00–12:00 со скоростью 2× (speedRatio=2000). Система проверяет валидность параметров, аллоцирует ресурсы, возвращает sessionId. Сессия в состоянии CREATED (0).
**Обоснование:**

*   `processingMode = 0` (historical) — основной режим перерасчёта

*   `startTime = 08:00`, `targetTime = 12:00` — 4-часовой диапазон

*   `speedRatio = 2000` (2×) — скорость: 4ч / 2 = 2 ч реального (наверно лучше быстрее, зависит от данных)

*   `targets = ["MT1.LU1"]` — один ТУ


**Предусловие:**

*   Стенд в начальном состоянии (2.3)

*   В ClickHouse данные за 08:00–12:00 для MT1.LU1

*   Конфигурация ТУ1 загружена

*   Нет активных сессий


**Действия:**

1.  `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T12:00:00Z","speedRatio":2000,"targets":["MT1.LU1"]})`

2.  Проверить ответ: `sessionId` не пуст, `status = 0` (CREATED), `processingMode = 0`

3.  `api.get(sessionId)` ⚠️ — убедиться, что сессия сохранена

4.  `api.list({status: 0})` ⚠️ — сессия в списке


**Ожидаемый результат:**

*   Шаг 1: HTTP 201, тело:


```json
{
  "sessionId": "<uuid>",
  "processingMode": 0,
  "status": 0,
  "startTime": "2026-11-09T08:00:00Z",
  "targetTime": "2026-11-09T12:00:00Z",
  "speedRatio": 2000,
  "targets": ["MT1.LU1"],
  "watermark": null,
  "progress": 0.0
}
```

*   Шаг 3: Все поля из шага 1, `startedAt = null`, `status = 0`

*   Шаг 4: Одна сессия с данным sessionId

*   PostgreSQL: строка в `sessions`, `status = 0`


**Teardown:** `api.close(sessionId)` ⚠️ → `WAIT(5)` → `RESET()`

* * *



#### HY-HIST-002 — Создание: валидация speedRatio

**Требование:** R-HYDR-050
**Описание:** Некорректные значения speedRatio отклоняются. Допустимый диапазон: 250–60000.
**Обоснование:**

*   `speedRatio = 0` → деление на ноль → крах

*   `speedRatio = 249` → ниже минимума (0.25×)

*   `speedRatio = 60001` → выше максимума (60×) - сценарий под фронт, по факту в коде 100 000 максимум

*   Граничные допустимые: 250 (0.25×) и 60000 (60×)


**Предусловие:** Стенд в начальном состоянии
**Действия:**
_Часть 1: speedRatio = 0 (недопустимо)_

1.  `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T12:00:00Z","speedRatio":0,"targets":["MT1.LU1"]})`

2.  Проверить: HTTP 400


_Часть 2: speedRatio = 249 (ниже минимума)_ 3. `api.createHistorical({...,"speedRatio":249,...})` 4. Проверить: HTTP 400
_Часть 3: speedRatio = 60001 (выше максимума)_ 5. `api.createHistorical({...,"speedRatio":60001,...})` 6. Проверить: HTTP 400
_Часть 4: speedRatio = 250 (граничный, допустимо)_ 7. `api.createHistorical({...,"speedRatio":250,...})` 8. Проверить: HTTP 201
_Часть 5: speedRatio = 60000 (граничный, допустимо)_ 9. `api.createHistorical({...,"speedRatio":60000,...})` 10. Проверить: HTTP 201
**Ожидаемый результат:**

*   Шаги 2, 4, 6: HTTP 400, `{"error":"speedRatio must be between 250 and 60000"}`

*   Шаги 8, 10: HTTP 201, сессия создана


**Teardown:** `api.close` ⚠️ для созданных → `RESET()`

* * *

#### HY-HIST-003 — Создание: startTime > targetTime

**Требование:** R-HYDR-050
**Описание:** Логическая ошибка: startTime позже targetTime. Невозможно обработать из будущего в прошлое.
**Действия:**

1.  `api.createHistorical({"startTime":"2026-11-09T12:00:00Z","targetTime":"2026-11-09T08:00:00Z","speedRatio":2000,"targets":["MT1.LU1"]})`

2.  Проверить ответ


**Ожидаемый результат:**

*   HTTP 400, `{"error":"startTime must be before targetTime"}`

*   `api.list({})` ⚠️ → пустой массив


**Teardown:** `RESET()`

* * *

#### HY-HIST-004 — Создание: пустой список targets

**Требование:** R-HYDR-050
**Описание:** `targets = []` — система не знает, что считать.
**Действия:**

1.  `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T12:00:00Z","speedRatio":2000,"targets":[]})`

2.  Проверить ответ


**Ожидаемый результат:**

*   HTTP 400, `{"error":"targets must contain at least one element"}`


**Teardown:** `RESET()`

* * *

#### HY-HIST-005 — Запуск: CREATED → OPENING → PLAYING

**Требование:** R-HYDR-051, R-HYDR-052
**Описание:** Запуск сессии. Каскад: REST → CREATED(0) → OPENING(1) → PLAYING(3). Система:

1.  Меняет статус 0 → 1 (OPENING) — идёт инициализация

2.  Подписывается на Kafka / начинает загрузку из CH

3.  Отправляет `START` в hydro-calculation

4.  Инициализирует watermark = startTime

5.  По завершении инициализации: 1 → 3 (PLAYING)

6.  Публикует `SESSION_OPENED` (WS, type=1)


**Обоснование:**

*   OPENING — промежуточное: может занять время (загрузка из CH, подключение Kafka)

*   Для historical с 4-часовым диапазоном: загрузка 144000+ сообщений → OPENING может быть 5–30 с

*   Watermark после PLAYING = startTime


**Предусловие:**

*   Сессия создана (HY-HIST-001), `status = 0`


**Действия:**

1.  `ws.subscribe(sessionId)`

2.  `api.start(sessionId)` ⚠️

3.  `ws.wait_event(sessionId, 1, timeout=60)` — SESSION_OPENED (type=1)

    > Таймаут 60 с: для большого диапазона OPENING может быть длительным

4.  `api.get(sessionId)` ⚠️ — проверить статус

5.  `api.watermark(sessionId)` ⚠️ — проверить watermark

6.  `kafka.consume("mod-hist-commands", {"sessionId": sessionId, "command":"START"}, timeout=15)`


**Ожидаемый результат:**

*   Шаг 3: Событие `type=1` (SESSION_OPENED). Возможно: событие приходит после перехода в PLAYING (зависит от реализации — OPENING и PLAYING могут быть в одном срезе по времени)

*   Шаг 4: `status = 3` (PLAYING), `startedAt` заполнен

*   Шаг 5: `watermark = "2026-11-09T08:00:00Z"`, `target = "2026-11-09T12:00:00Z"`, `state = 1` (MOVING)

*   Шаг 6: В Kafka:


```json
{"sessionId":"<id>","command":"START","params":{"processingMode":0,"startTime":1705300000000,"targetTime":1705314000000,"speedRatio":2000},"ts":...}
```

**Примечание:** Если OPENING → PLAYING происходит быстрее, чем WS-клиент успевает подписаться, событие SESSION_OPENED может быть пропущено. В этом случае проверяем по `api.get`: status должен быть 3.
**Teardown:** `api.stop(sessionId)` ⚠️ → `api.close(sessionId)` ⚠️ → `WAIT(5)` → `RESET()`

* * *

#### HY-HIST-006 — Повторный запуск (идемпотентность)

**Требование:** R-HYDR-051
**Описание:** Двойной клик «Запустить». Второй запрос не создаёт дубль.
**Предусловие:** Сессия PLAYING (status=3)
**Действия:**

1.  `api.start(sessionId)` ⚠️ — повторный

2.  Проверить ответ

3.  `api.get(sessionId)` ⚠️

4.  `kafka.consume("mod-hist-commands", {"sessionId": sessionId, "command":"START"}, timeout=5)` — проверить что START только один


**Ожидаемый результат:**

*   Шаг 1: HTTP 200 `{"message":"Session already playing"}` **ИЛИ** HTTP 409 _(допущение: 200)_

*   Шаг 3: `status = 3`, `startedAt` не изменился

*   Шаг 4: В Kafka за всё время — только ОДНО START


**Teardown:** `api.stop` ⚠️ → `api.close` ⚠️ → `RESET()`

* * *

#### HY-HIST-007 — Пауза: PLAYING → PAUSED

**Требование:** R-HYDR-053
**Описание:** Приостановка. Watermark фиксируется, не сбрасывается.
**Предусловие:** Сессия PLAYING, `watermark ≈ 09:30:00`
**Действия:**

1.  `ws.subscribe(sessionId)`

2.  `api.pause(sessionId)` ⚠️

3.  `ws.wait_event(sessionId, 2, timeout=10)` — SESSION_PAUSED (type=2)

4.  `api.get(sessionId)` ⚠️

5.  `api.watermark(sessionId)` ⚠️ → `wm_pause`

6.  `WAIT(10)`

7.  `api.watermark(sessionId)` ⚠️ → `wm_after`


**Ожидаемый результат:**

*   Шаг 3: `type=2`

*   Шаг 4: `status = 2` (PAUSED)

*   Шаг 5: `wm_pause = "2026-11-09T09:30:00Z"` (зафиксировано)

*   Шаг 7: `wm_after = wm_pause` (не изменилось за 10 с)


**Teardown:** `api.resume(sessionId)` ⚠️ → `api.stop` ⚠️ → `api.close` ⚠️ → `RESET()`

* * *

#### HY-HIST-008 — Возобновление: PAUSED → PLAYING

**Требование:** R-HYDR-053
**Описание:** Продолжение с того же watermark.
**Предусловие:** Сессия PAUSED, `watermark = 09:30:00`
**Действия:**

1.  `ws.subscribe(sessionId)`

2.  `api.resume(sessionId)` ⚠️

3.  `ws.wait_event(sessionId, 3, timeout=10)` — SESSION_RESUMED (type=3)

4.  `api.get(sessionId)` ⚠️

5.  `api.watermark(sessionId)` ⚠️ → `wm_resume`

6.  `WAIT(5)`

7.  `api.watermark(sessionId)` ⚠️ → `wm_moved`


**Ожидаемый результат:**

*   Шаг 3: `type=3`

*   Шаг 4: `status = 3` (PLAYING)

*   Шаг 5: `wm_resume = "2026-11-09T09:30:00Z"` (не сбросился)

*   Шаг 7: `wm_moved > wm_resume` (двигается)


**Teardown:** `api.stop` ⚠️ → `api.close` ⚠️ → `RESET()`

* * *

#### HY-HIST-009 — Остановка: PLAYING → DONE

**Требование:** R-HYDR-054
**Описание:** Остановка. Watermark фиксируется. Ресурсы ещё не удалены (сессия не закрыта).
**Обоснование:**

*   DONE ≠ CLOSED: после DONE можно экспортировать, сохранить, а потом закрыть

*   Watermark = момент, до которого обработаны данные


**Предусловие:** Сессия PLAYING, `watermark = 10:15:00`
**Действия:**

1.  `ws.subscribe(sessionId)`

2.  `api.stop(sessionId)` ⚠️

3.  `ws.wait_event(sessionId, 4, timeout=15)` — SESSION_DONE (type=4)

4.  `api.get(sessionId)` ⚠️

5.  `api.watermark(sessionId)` ⚠️ → `wm_final`

6.  `api.list({status: 8})` ⚠️

7.  `WAIT(10)`

8.  `api.watermark(sessionId)` ⚠️ → `wm_check`


**Ожидаемый результат:**

*   Шаг 3: `type=4` (SESSION_DONE)

*   Шаг 4: `status = 8` (DONE), `stoppedAt` заполнен

*   Шаг 5: `wm_final = "2026-11-09T10:15:00Z"`

*   Шаг 6: Сессия в списке со status=8

*   Шаг 8: `wm_check = wm_final` (не изменился)


**Teardown:** `api.close(sessionId)` ⚠️ → `WAIT(5)` → `RESET()`

* * *

#### HY-HIST-010 — Закрытие: DONE → CLOSING → CLOSED

**Требование:** R-HYDR-055
**Описание:** Закрытие остановленной сессии. Освобождение ресурсов.
**Предусловие:** Сессия DONE (status=8)
**Действия:**

1.  `ws.subscribe(sessionId)`

2.  `api.close(sessionId)` ⚠️

3.  `ws.wait_event(sessionId, 5, timeout=15)` — SESSION_CLOSED (type=5)

4.  `api.get(sessionId)` ⚠️

5.  `api.start(sessionId)` ⚠️ — попытка запуска

6.  `api.stop(sessionId)` ⚠️ — попытка остановки


**Ожидаемый результат:**

*   Шаг 3: `type=5` (SESSION_CLOSED)

*   Шаг 4: `status = 11` (CLOSED), `closedAt` заполнен

*   Шаг 5: HTTP 409 `{"error":"Session is closed"}`

*   Шаг 6: HTTP 409

*   PostgreSQL: `status = 11`, `closed_at` заполнен


**Teardown:** `RESET()`

* * *

#### HY-HIST-011 — Повторное закрытие (идемпотентность)

**Требование:** R-HYDR-055
**Предусловие:** Сессия CLOSED (status=11)
**Действия:**

1.  `api.close(sessionId)` ⚠️

2.  Проверить ответ


**Ожидаемый результат:**

*   HTTP 409 _(допущение)_

*   Система не упала


**Teardown:** `RESET()`

* * *

#### HY-HIST-012 — Превышение максимума сессий

**Требование:** R-HYDR-056
**Описание:** `maxSessions = 10`. 11-я сессия отклоняется.
**Предусловие:** Стенд в начальном состоянии
**Действия:**

1.  Создать и запустить 10 сессий: `api.createHistorical(...)` + `api.start(...)` ⚠️ × 10

2.  `api.list({status: 3})` ⚠️ → 10 сессий PLAYING

3.  `api.createHistorical(...)` — 11-я

4.  Проверить ответ


**Ожидаемый результат:**

*   Шаг 2: 10 сессий

*   Шаг 3: HTTP 429 `{"error":"Maximum number of sessions (10) reached"}`

*   11-я не создана


**Teardown:** `api.stop` ⚠️ + `api.close` ⚠️ × 10 → `RESET()`

* * *

#### HY-HIST-013 — TTL: автозакрытие неактивной

**Требование:** R-HYDR-057
**Описание:** Сессия PAUSED > TTL → автозакрытие.
**Обоснование:**

*   TTL = 24 ч в проде. В тесте: временно 50 с через конфиг.


**Предусловие:**

*   TTL временно = 50 с _(уточнить механизм: Redis key / actuator / env)_

*   Сессия PAUSED


**Действия:**

1.  `api.createModelling({"targets":["MT1.LU1"]})`

2.  `api.start(id)` ⚠️

3.  `api.pause(id)` ⚠️

4.  `WAIT(55)` — 50 с TTL + 5 с margin

5.  `api.get(id)` ⚠️

6.  `api.list({status: 11})` ⚠️


**Ожидаемый результат:**

*   Шаг 5: `status = 11` (CLOSED) — автоматически

*   `closedAt` заполнен

*   `closeReason = "TTL_EXCEEDED"` _(допущение: формат поля)_


**Примечание:** Механизм изменения TTL в тесте: **уточнить** (Redis / config / env variable).
**Teardown:** `RESET()` (с возвратом TTL к 24ч)

* * *

### 3.2 Режим historical (перерасчёт истории)

* * *

#### HY-HIST-014 — historical: базовый цикл обработки

**Требование:** R-HYDR-058
**Описание:** Полный цикл historical: создание → запуск → обработка → автоматическое завершение (DONE). Диапазон 10 мин, скорость 10× (speedRatio=10000) → реальное время ≈ 60 с.
**Обоснование:**

*   10 мин / 10× = 60 с реального — приемлемо для автотеста

*   speedRatio = 10000 — один из допустимых значений UI


**Предусловие:**

*   В CH данные за 08:00–08:10 для MT1.LU1

*   Конфигурация ТУ1 загружена


**Действия:**

1.  `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:10:00Z","speedRatio":10000,"targets":["MT1.LU1"]})`

2.  `api.start(id)` ⚠️

3.  `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED

4.  `WAIT(30)` — 30 с × 10× = 300 с виртуального (5 мин из 10)

5.  `api.watermark(id)` ⚠️

6.  `api.progress(id)` ⚠️

7.  `WAIT(35)` — ещё 35 с × 10× = 350 с (всего 650 > 600 = target)

8.  `ws.wait_event(id, 9, timeout=60)` — WATERMARK_COMPLETE (type=9)

9.  `api.get(id)` ⚠️

10.  `api.watermark(id)` ⚠️


**Ожидаемый результат:**

*   Шаг 5: `watermark ≈ "2026-11-09T08:05:00Z"` (300 с = 5 мин)

*   Шаг 6: `progress ≈ 50%` (300/600 × 100)

*   Шаг 8: `type=9` (WATERMARK_COMPLETE)

*   Шаг 9: `status = 8` (DONE) — автоматически

*   Шаг 10: `watermark = "2026-11-09T08:10:00Z"` (= targetTime), `state = 3` (COMPLETE)


**Реальное время сценария:** ≈ 2 мин (30+35 с + задержки)
**Teardown:** `api.close(id)` ⚠️ → `WAIT(5)` → `RESET()`

* * *

#### HY-HIST-015 — historical: изменение скорости во время работы

**Требование:** R-HYDR-061
**Описание:** Увеличение скорости с 2× на 10× во время работы. Watermark не сбрасывается. Событие SPEED_CHANGE.
**Предусловие:**

*   Сессия historical: `start = 08:00`, `target = 08:10` (600 с), `speedRatio = 2000` (2×)

*   `watermark = 08:03:00` (180 с, progress = 30%)

*   Осталось: 420 с виртуального / 2× = 210 с реального


**Действия:**

1.  `ws.subscribe(id)`

2.  `api.setSpeed(id, 10000)` ⚠️ (2× → 10×)

3.  `ws.wait_event(id, 13, timeout=10)` — SPEED_CHANGE (type=13)

4.  `api.get(id)` ⚠️

5.  `api.watermark(id)` ⚠️ → `wm_before`

6.  `WAIT(45)` — 45 с × 10× = 450 с виртуального > 420 (остаток)

7.  `ws.wait_event(id, 9, timeout=30)` — WATERMARK_COMPLETE

8.  `api.get(id)` ⚠️


**Ожидаемый результат:**

*   Шаг 3: `type=13`, `data.oldSpeed = 2000`, `data.newSpeed = 10000`

*   Шаг 4: `speedRatio = 10000`

*   Шаг 5: `wm_before = "2026-11-09T08:03:00Z"` (не сбросился)

*   Шаг 7: Сессия завершена

*   Шаг 8: `status = 8` (DONE)

*   Реальное время от смены до завершения: ≈ 45 с (420/10 = 42 с + задержка)


**Teardown:** `api.close(id)` ⚠️ → `RESET()`

* * *

#### HY-HIST-016 — historical: скорость 0.25× (замедление)

**Требование:** R-HYDR-060
**Описание:** Минимальная скорость 0.25× (speedRatio=250). Виртуальное время идёт медленнее реального. Диапазон 4 мин → реальное: 4мин/0.25 = 16 мин. Проверяем первые 30 с.
**Обоснование:**

*   0.25× — минимальная допустимая скорость

*   30 с реального × 0.25 = 7.5 с виртуального

*   Проверка, что watermark движется **медленнее** реального времени


**Предусловие:** В CH данные за 08:00–08:04
**Действия:**

1.  `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:04:00Z","speedRatio":250,"targets":["MT1.LU1"]})`

2.  `api.start(id)` ⚠️

3.  `ws.wait_event(id, 1, timeout=30)`

4.  `WAIT(30)` — 30 с реального

5.  `api.watermark(id)` ⚠️

6.  `api.progress(id)` ⚠️


**Ожидаемый результат:**

*   Шаг 5: `watermark ≈ "2026-11-09T08:00:07Z"` (30 × 0.25 = 7.5 с виртуального)

*   Шаг 6: `progress ≈ 3.1%` (7.5/240 × 100)

*   Watermark двигается медленнее реального времени


**Примечание:** Полный цикл займёт 16 мин — для автотеста достаточно 30 с.
**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

* * *

#### HY-HIST-017 — historical: нет данных в ClickHouse

**Требование:** R-HYDR-060, R-HYDR-062
**Описание:** В CH нет данных за указанный период. Система обрабатывает это успешно без последствий.
**Предусловие:** В CH **нет** данных за 20:00–21:00
**Действия:**

1.  `api.createHistorical({"startTime":"2026-11-09T20:00:00Z","targetTime":"2026-11-09T21:00:00Z","speedRatio":5000,"targets":["MT1.LU1"]})`

2.  `api.start(id)` ⚠️

3.  `ws.wait_event(id, 6, timeout=30)` — SESSION_ERROR (type=6) **ИЛИ** 8

4.  `WAIT(30)`

5.  `api.get(id)` ⚠️


**Ожидаемый результат:** УТОЧНИТЬ

*   **Вариант A**: `type=6`, `data.error = "No data in ClickHouse"`, `status = 12` (ERROR)

*   **Вариант B**: `status = 8` (DONE), сессия завершена без обработки


_(Допущение: Вариант A)_
**Teardown:** `api.close(id)` ⚠️ → `RESET()`

* * *

#### HY-HIST-018 — historical: частичные данные (прерывание)

**Требование:** R-HYDR-062
**Описание:** Данные за 08:00–08:05, нет за 08:05–08:10. Обработка имеющихся, без падения.
**Предусловие:** В CH: 08:00–08:05 (300 сообщений), нет 08:05–08:10
**Действия:**

1.  `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:10:00Z","speedRatio":10000,"targets":["MT1.LU1"]})`

2.  `api.start(id)` ⚠️

3.  `WAIT(60)` — 60 с × 10× = 600 с = весь диапазон

4.  `ws.wait_event(id, 9, timeout=60)` — WATERMARK_COMPLETE

5.  `api.get(id)` ⚠️

6.  `api.watermark(id)` ⚠️


**Ожидаемый результат:**

*   Шаг 4: WATERMARK_COMPLETE (сессия завершена)

*   Шаг 5: `status = 8` (DONE)

*   В `model_main_{id}`: сообщения только за 08:00–08:05

*   _(Допущение: поле_ `dataGaps` _в ответе_ `api.get`_)_


**Teardown:** `api.close(id)` ⚠️ → `RESET()`

* * *

#### HY-HIST-019 — historical: большой объём (пагинация CH)

**Требование:** R-HYDR-063
**Описание:** 5000 сообщений → 5 страниц по 1000. Все загружаются без потери.
**Предусловие:** В CH: 5000 сообщений за 08:00–08:01
**Действия:**

1.  `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:01:00Z","speedRatio":10000,"targets":["MT1.LU1"]})`

2.  `api.start(id)` ⚠️

3.  `WAIT(20)` — 20 с × 10× = 200 с > 60 (весь диапазон)

4.  `ws.wait_event(id, 9, timeout=30)`

5.  Подсчёт: `kafka.consume("model_main_" + id, timeout=10)` × N **ИЛИ** `ch.query("SELECT count(*) ...")`

6.  Сравнить: = 5000 (± 1%)


**Ожидаемый результат:**

*   Шаг 4: Завершена

*   Шаг 5–6: 5000 сообщений, нет дыр


**Teardown:** `api.close(id)` ⚠️ → `RESET()`

* * *

#### HY-HIST-020 — historical: максимальная скорость 60× (по UI) (скорее всего максимальная 100х)

**Требование:** R-HYDR-061
**Описание:** `speedRatio = 60000` (60×). 10 мин / 60× = 10 с реального. Проверка без переполнения буфера.
**Предусловие:** В CH: 10 000 сообщений за 10 мин
**Действия:**

1.  `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:10:00Z","speedRatio":60000,"targets":["MT1.LU1"]})`

2.  `api.start(id)` ⚠️

3.  `WAIT(20)` — 20 с × 60× = 1200 с > 600 (весь диапазон)

4.  `ws.wait_event(id, 9, timeout=30)`

5.  `api.get(id)` ⚠️

6.  `api.progress(id)` ⚠️


**Ожидаемый результат:**

*   Шаг 4: Завершена (реальное время: 600/60 = 10 с + задержка)

*   Шаг 5: `status = 8` (DONE)

*   Шаг 6: `progress = 100%`

*   `messagesDropped = 0`

*   В `model_main_{id}`: все 10 000 сообщений


**Teardown:** `api.close(id)` ⚠️ → `RESET()`

* * *

### 3.3 Режим modelling (моделирование)

* * *

#### HY-HIST-021 — modelling: базовый цикл (ручной ввод)

**Требование:** R-HYDR-064
**Описание:** Оператор задаёт Press=7.0 через hmi.set. Hydro-calculation рассчитывает Head. Оператор двигает время advance.
**Обоснование:**

*   «Что если Press = 7.0» → Head = (7.0/850)×101970 + 63.5 = 903.3 м

*   Нет привязки к реальному времени


**Предусловие:**

*   Конфигурация ТУ1 загружена

*   `[KIP].TI.Ro = 850`, `[KIP].Height = 63.5`


**Действия:**

1.  `api.createModelling({"targets":["MT1.LU1"]})`

2.  `api.start(id)` ⚠️

3.  `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED

4.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 7.0)` ⚠️

5.  `WAIT(5)`

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️

7.  `api.advance(id, 60)` ⚠️

8.  `api.watermark(id)` ⚠️


**Ожидаемый результат:**

*   Шаг 6: `Head ≈ 903.3 м` (рассчитано hydro-calculation)
    *   Расчёт: (7.0 / 850) × 101970 + 63.5 = 839.8 + 63.5 = **903.3**

*   Шаг 8: `watermark` увеличен на 60 с относительно шага 4


**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`


#### HY-HIST-022 — modelling: advance на большой интервал (1 час)


**Требование:** R-HYDR-065

**Описание:** Оператор продвигает виртуальное время на 1 час (3600 с) одним вызовом `advance`. Это моделирует ситуацию, когда оператор хочет перематывать время крупными шагами. Система должна: корректно увеличить watermark на 3600 с, если в буфере (из импорта) есть данные за этот интервал — опубликовать их в Kafka, если данных нет — просто продвинуть watermark без публикации.

**Причинно-следственная связь:** В отличие от historical, где темп задан speedRatio и данные идут «потоком», в modelling оператор полностью контролирует время. Один `advance(3600)` = «прошло 1 час виртуального времени». Если оператор не загружал файл импорта и не задавал значения через hmi.set — hydro-calculation получит «пустое» время и рассчитает по последним известным значениям (или по нулям, если ничего не было).

**Предусловие:**


*   Сессия modelling создана и запущена (status = 3, PLAYING)

*   `watermark` = начальное значение (например, `2026-11-09T09:00:00Z`)

*   Файл импорта **не** загружен (сценарий без данных)

*   Конфигурация ТУ1 загружена



**Действия:**


1.  `api.watermark(id)` ⚠️ _Зафиксируем текущий watermark до advance, чтобы потом проверить разницу. Ожидаем:_ `2026-11-09T09:00:00Z` _(или значение, установленное при запуске)._

2.  `api.advance(id, 3600)` ⚠️ _Сдвигаем виртуальное время на 1 час вперёд. Система должна: (а) увеличить watermark на 3600 с, (б) если в буфере есть данные за 09:00–10:00 — опубликовать их в_ `model_main_{id}`_, (в) если данных нет — просто продвинуть watermark. Hydro-calculation получает «пустой» интервал и рассчитывает по последним значениям._

3.  `WAIT(5)` _Даём время на обработку: публикация в Kafka, расчёт hydro-calculation, обновление watermark в Redis._

4.  `api.watermark(id)` ⚠️ _Читаем новый watermark. Ожидаем:_ `2026-11-09T10:00:00Z` _(09:00 + 1 час). Разница с шагом 1 должна быть ровно 3600 с (± 2 с на задержки)._

5.  `api.get(id)` ⚠️ _Проверяем_ `messagesProcessed` _и_ `messagesDropped`_. Если файл импорта не загружен —_ `messagesProcessed` _не должен резко вырасти (нет данных для публикации). Если загружен — должно быть число сообщений за 1 час._

6.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️ _Проверяем, что hydro-calculation успел пересчитать. Даже если данных не было — напор рассчитан по последним известным Press/Ro/Height. Значение должно существовать (не null)._



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 1 | `watermark = "2026-11-09T09:00:00Z"` | Исходное состояние |
| 4 | `watermark = "2026-11-09T10:00:00Z"` | +3600 с |
| 5 | `messagesProcessed` не изменилось (без импорта) | Нет данных для публикации |
| 6 | `Head` имеет значение (≠ null) | Hydro-calc рассчитал по последним входам |


**Примечание:** Если advance на 1 час вызывает внутренний «разброс» на подшаги (например, по 60 с) — это допустимо. Главное: итоговый watermark = 09:00 + 3600 с.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-023 — modelling: пошаговое advance (по 1 минуте × 3)


**Требование:** R-HYDR-065

**Описание:** Оператор двигает время по 1 минуте за шаг (`advance(60)`). Это «медленное воспроизведение» — оператор хочет видеть, как меняются значения на каждом шаге. Сценарий проверяет, что watermark увеличивается ровно на 60 с за каждый вызов, что нет накопления ошибок (drift), и что система корректно обрабатывает последовательные advance без конфликтов.

**Причинно-следственная связь:** При пошаговом advance hydro-calculation получает одно значение (или пакет) за 1 минуту и пересчитывает. Если оператор будет менять Press на каждом шаге (например, 5.0 → 5.5 → 6.0) — напор будет меняться соответствующим образом. В этом сценарии мы не меняем Press — проверяем только механику advance.

**Предусловие:**


*   Сессия modelling запущена (status = 3)

*   `watermark = "2026-11-09T09:00:00Z"`

*   Значение Press уже задано: `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` (чтобы hydro-calc имел данные для расчёта)



**Действия:**


1.  `api.advance(id, 60)` ⚠️ _Шаг 1: сдвигаем на 1 минуту. Виртуальное время: 09:00 → 09:01. Если в буфере нет данных — просто продвигаем._

2.  `api.watermark(id)` ⚠️ _Проверяем: watermark должен быть_ `09:01:00`_. Это подтверждает, что advance обработан синхронно (или почти синхронно — допустимая задержка 2 с)._

3.  `WAIT(3)` _Короткая пауза: даём hydro-calculation время на расчёт по текущим значениям. Это важно: если сразу делать следующий advance, hydro-calc может не успеть пересчитать по предыдущему состоянию._

4.  `api.advance(id, 60)` ⚠️ _Шаг 2: 09:01 → 09:02._

5.  `api.watermark(id)` ⚠️ _Ожидаем:_ `09:02:00`_. Разница с шагом 2: ровно 60 с._

6.  `WAIT(3)`

7.  `api.advance(id, 60)` ⚠️ _Шаг 3: 09:02 → 09:03._

8.  `api.watermark(id)` ⚠️ _Ожидаем:_ `09:03:00`_. Разница с шагом 5: ровно 60 с._

9.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️ _Проверяем, что hydro-calculation работает: напор рассчитан. При Press=5.0, Ro=850, H=63.5: Head = (5.0/850)×101970 + 63.5 = 599.8 + 63.5 = 663.3 м. Значение не должно быть null._



**Ожидаемый результат:**

| Шаг | Watermark | Дельта | Пояснение |
| --- | --- | --- | --- |
| 2 | 09:01:00 | +60 с | Шаг 1 |
| 5 | 09:02:00 | +60 с | Шаг 2, drift = 0 |
| 8 | 09:03:00 | +60 с | Шаг 3, drift = 0 |
| 9 | Head ≈ 663.3 м | — | Hydro-calc работает |


**Критично:** Если на шаге 8 watermark = 09:03:01 или 09:02:59 — это накопление ошибок (drift). Допустимое отклонение: ± 1 с на 3 шага.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-024 — modelling: отрицательный advance (откат времени)


**Требование:** R-HYDR-065

**Описание:** Оператор пытается откатить время назад: `advance(-60)`. Это логически некорректно для watermark (монотонная величина — не может двигаться назад). Ожидаемое поведение: система отклоняет запрос с ошибкой 400.

**Причинно-следственная связь:** Watermark — «фронт» обработки. Если мы откатим его назад, hydro-calculation получит данные «из прошлого» повторно → дубли в расчётах, нарушение логики алармов. Поэтому откат должен быть запрещён на уровне валидации.

**Альтернативное поведение (не предпочтительное):** если система допускает откат — это означает, что оператор может «перемотать» и пересчитать. Но это ломает модель: уже обработанные сообщения не «возвратятся» из Kafka, алармы уже сработали. Поэтому **ожидаем отказ**.

**Предусловие:**


*   Сессия modelling запущена, `watermark = "2026-11-09T09:05:00Z"`



**Действия:**


1.  `api.advance(id, -60)` ⚠️ _Пытаемся откатить на 1 минуту назад. Ожидаем: система отклоняет. Это не «ошибка системы», а валидация входного параметра: seconds < 0 недопустим._

2.  `WAIT(2)` _Короткая пауза на обработку запроса (хотя он должен быть отклонён сразу — 400 приходит синхронно)._

3.  `api.watermark(id)` ⚠️ _Проверяем, что watermark_ **_не изменился_**_. Должно быть_ `09:05:00` _— как до попытки advance._

4.  `api.get(id)` ⚠️ _Проверяем, что статус сессии не изменился (остался PLAYING = 3), нет ошибок в логах сессии._



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 1 | HTTP 400, `{"error":"advance seconds must be positive"}` | Валидация: отрицательное значение отклонено |
| 3 | `watermark = "2026-11-09T09:05:00Z"` | Не изменился |
| 4 | `status = 3` (PLAYING) | Сессия не пострадала |


**Примечание:** _(Допущение: отрицательный advance отклоняется с 400. Если реализация допускает откат — это требует отдельного обсуждения с разработкой.)_

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-025 — modelling: невалидные данные (invalid=true)


**Требование:** R-HYDR-064

**Описание:** Оператор записывает значение с флагом `invalid = true` (имитация сбоя датчика). Hydro-calculation должен отреагировать аналогично реальному времени: напор будет помечен как invalid, алармы по несущей не сработают, но `AlmFailOn` (неисправность датчика) — сработает.

**Причинно-следственная связь:** В hydro-calculation (HYDRO-75) есть проверка: если `invalid = true` → `Head.invalid = true`. Далее в логике алармов: если `invalid = true` → алармы по давлению/напору **не генерируются** (не знаем, реальное ли значение), но `AlmFailOn = true` (датчик неисправен). Это защитный механизм: оператор видит «датчик сломан», но не получает ложных алармов по несущей.

**Предусловие:**


*   Сессия modelling запущена

*   До этого Press = 7.0 (валидное), Head = 903.3 м (валидный)

*   `[KIP].State.Disable = false` (датчик не отключён)



**Действия:**


1.  `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 7.0, invalid=true)` ⚠️ _Записываем то же значение (7.0), но с флагом invalid=true. Это имитирует ситуацию: датчик выдал значение, но оно помечено как невалидное (например, превышен порог допустимого диапазона, или АЦП пометил как сбой). Hydro-calculation получит сообщение_ `{tag, value:7.0, invalid:true}`_._

2.  `WAIT(5)` _Время на: публикацию в Kafka → обработку hydro-calculation → запись результата в model_main_{id} → доступность через hmi-backend._

3.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️ _Читаем напор. Ожидаем: значение существует (рассчитано по формуле), НО_ `invalid = true`_. То есть hydro-calc посчитал (7.0/850)×101970 + 63.5 = 903.3, но пометил результат как невалидный, потому что вход невалидный._

4.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")` ⚠️ _Читаем аларм неисправности. Ожидаем:_ `AlmFailOn = true`_. Логика:_ `Disable=false AND invalid=true → AlmFailOn=true`_. Оператор видит: «датчик KIP1 неисправен»._

5.  `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn")` ⚠️ _(если существует)_ _Читаем аларм «давление выше уставки». Ожидаем:_ **_не сработал_** _(false), потому что_ `invalid=true` _блокирует генерацию алармов по значению. Это важно: если бы аларм сработал — это ложная тревога._



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 3 | `Head.value ≈ 903.3`, `Head.invalid = true` | Рассчитан, но помечен как невалидный |
| 4 | `AlmFailOn = true` | Датчик «неисправен» |
| 5 | `AlmHighOn = false` (или не сработал) | Алармы по значению заблокированы invalid |


**Примечание:** Если `AlmHighOn` не существует как отдельный тег — проверяем через `model_alarm_{id}`: в Kafka не должно быть аларма по несущей за этот момент.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`


* * *



### 3.4 Работа с файлами: импорт



* * *



#### HY-HIST-026 — Импорт XLSX (modelling)


**Требование:** R-HYDR-066

**Описание:** Оператор загружает XLSX-файл с временной шкалой входных параметров для моделирования. Файл содержит 1 тег (Press) и 3 временных точки. После импорта данные попадают в буфер сессии. При последующем `advance` система подставляет значения из буфера по таймстампам и публикует в `model_main_{id}`.

**Формат XLSX (один лист):**

| tag | timestamp | value | invalid |
| --- | --- | --- | --- |
| MT1.LU1.SGLU1.KIP1.TI.Press | 2026-11-09T09:00:00Z | 5.0 | false |
| MT1.LU1.SGLU1.KIP1.TI.Press | 2026-11-09T09:01:00Z | 5.1 | false |
| MT1.LU1.SGLU1.KIP1.TI.Press | 2026-11-09T09:02:00Z | 5.2 | false |


**Причинно-следственная связь:** Импорт — способ загрузить «сценарий» (последовательность значений во времени). Оператор готовит его в Excel, загружает, и затем «проигрывает» через advance. После импорта сессия получает статус IMPORTED (7) — данные в буфере, готовы к использованию.

**Предусловие:**


*   Сессия modelling создана (status = 0, CREATED), **не запущена**

*   XLSX-файл подготовлен (3 строки данных, 1 тег)

*   Конфигурация ТУ1 загружена



**Действия:**


1.  `api.import_(id, file=import.xlsx)` ⚠️ _Загружаем XLSX через HistoryImportController. Система: (а) парсит файл, (б) валидирует формат (колонки: tag, timestamp, value, invalid), (в) сохраняет данные в буфер (Redis/память), (г) меняет статус сессии на IMPORTED (7). Формат запроса: multipart/form-data с файлом._

2.  `WAIT(5)` _Время на парсинг и запись в буфер. Для 3 строк — мгновенно, но закладываем 5 с на задержки сети/БД._

3.  `api.get(id)` ⚠️ _Проверяем статус сессии. Ожидаем:_ `status = 7` _(IMPORTED). Поле_ `importStatus` _или аналогичное:_ `2` _(DONE по HistoryImportStatus)._

4.  `api.start(id)` ⚠️ _Запускаем сессию. Она переходит: CREATED → OPENING → PLAYING. Теперь можно advance._

5.  `ws.wait_event(id, 1, timeout=30)` _Ожидаем SESSION_OPENED._

6.  `api.advance(id, 120)` ⚠️ _Продвигаем на 2 минуты (120 с). Система должна: взять из буфера значения с ts ≤ 09:02:00 (все 3), опубликовать их в_ `model_main_{id}`_. VirtualTime: 09:00 → 09:02._

7.  `WAIT(5)` _Время на: публикацию 3 сообщений → hydro-calculation расчёт → доступность результатов._

8.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Press")` ⚠️ _Читаем текущее значение Press. Ожидаем:_ `5.2` _(последнее значение в диапазоне 09:00–09:02). Система подставила значения из импортированного файла._

9.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️ _Проверяем расчёт: Head = (5.2/850)×101970 + 63.5 = 623.8 + 63.5 = 687.3 м. Hydro-calculation рассчитал по импортированному Press._



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 3 | `status = 7` (IMPORTED) | Импорт завершён, данные в буфере |
| 6 | HTTP 200 | Advance принят |
| 8 | `Press = 5.2` | Последнее значение из файла |
| 9 | `Head ≈ 687.3 м` | Рассчитано по импортированному Press |


**Примечание:** Если advance на 120 с публикует все 3 сообщения одновременно (а не по одному на минуту) — это допустимо. Главное: итоговое значение = 5.2, и в `model_main_{id}` есть 3 сообщения с ts 09:00, 09:01, 09:02.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-027 — Импорт ZIP_CSV (historical)


**Требование:** R-HYDR-066

**Описание:** Импорт ZIP_CSV для historical-сессии. ZIP содержит CSV-файлы с историческими данными, подготовленными внешним инструментом. ZIP_CSV — это исторические данные, которые заменяют (или дополняют) данные из ClickHouse.

**Формат ZIP:**


```
import.zip
├── MT1_LU1_KIP1_Press.csv
│   tag,timestamp,value,invalid
│   MT1.LU1.SGLU1.KIP1.TI.Press,2026-11-09T08:00:00Z,5.0,false
│   MT1.LU1.SGLU1.KIP1.TI.Press,2026-11-09T08:00:01Z,5.01,false
│   ...
├── MT1_LU1_UR1_QVmom.csv
│   tag,timestamp,value,invalid
│   MT1.LU1.UR1.TI.QVmom,2026-11-09T08:00:00Z,120.0,false
│   ...
```


**Причинно-следственная связь:** Ситуация: ClickHouse недоступен или данные в нём повреждены или требуется проверка на спец версии. Оператор имеет резервную копию в CSV, упакованную в ZIP. Загружает — и historical-сессия работает по этим данным вместо CH. Альтернативный случай: данные из внешнего источника (другая подстанция, другой формат) — оператор конвертирует в CSV и загружает.

**Предусловие:**


*   Сессия historical создана (status = 0), период 08:00–08:05, speedRatio = 10000

*   ZIP-файл подготовлен (2 CSV: Press и QVmom, по 5 строк)

*   В ClickHouse данные **отсутствуют** за этот период (чтобы убедиться, что используются именно импортированные)



**Действия:**


1.  `api.import_(id, file=import.zip, format="ZIP_CSV")` ⚠️ _Загружаем ZIP. Система: (а) распаковывает, (б) парсит каждый CSV, (в) валидирует (колонки, формат ts, числовые значения), (г) сохраняет в буфер. Статус сессии → IMPORTED (7)._

2.  `WAIT(10)` _Время на: распаковку ZIP, парсинг 2 CSV, запись в буфер/БД. Для 10 строк — быстро, но ZIP-операции могут добавить задержку._

3.  `api.get(id)` ⚠️ _Проверяем:_ `status = 7` _(IMPORTED). Поле_ `importedTags` _или аналогичное:_ `["MT1.LU1.SGLU1.KIP1.TI.Press", "MT1.LU1.UR1.TI.QVmom"]`_._

4.  `api.start(id)` ⚠️ _Запускаем. Система использует данные из импорта вместо CH (т.к. CH пуст для этого периода)._

5.  `ws.wait_event(id, 1, timeout=30)`

6.  `WAIT(40)` _40 с × 10× = 400 с виртуального > 300 с (5 мин = весь диапазон). Сессия должна завершиться._

7.  `ws.wait_event(id, 9, timeout=60)` — WATERMARK_COMPLETE

8.  `api.get(id)` ⚠️ _Проверяем финальный статус и количество обработанных сообщений._



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 3 | `status = 7` (IMPORTED), 2 тега | Импорт успешен |
| 7 | WATERMARK_COMPLETE | Сессия завершена |
| 8 | `status = 8` (DONE), `messagesProcessed ≈ 10` | 5 строк Press + 5 строк QVmom |


**Примечание:** _(Допущение: импорт заменяет данные из CH. Если реализация смешивает — это нужно уточнить. В текущем тесте CH пуст, поэтому результат одинаков.)_

**Teardown:** `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-028 — Импорт: невалидный формат


**Требование:** R-HYDR-066

**Описание:** Оператор загружает файл с битым содержимым (не XLSX, не ZIP — просто текстовый мусор). Система должна отклонить с ошибкой, не испортив сессию. После отклонения оператор может повторить импорт с корректным файлом.

**Причинно-следственная связь:** Если система сломалась и зависла на битом файле (исключение, сбой парсера) — сессия может остаться в неопределённом состоянии (IMPORTING = 6 навечно). Поэтому важно проверить что: (а) ошибка возвращается как 400, (б) сессия остаётся в предыдущем статусе (CREATED = 0), (в) повторный импорт возможен.

**Предусловие:**


*   Сессия modelling создана (status = 0)



**Действия:**


1.  `api.import_(id, file=binary_garbage.bin)` ⚠️ _Загружаем файл, который не является ни XLSX, ни ZIP. Содержимое: случайные байты (или текст "hello world"). Система должна: (а) определить, что формат не распознаётся, (б) вернуть 400, (в) НЕ менять статус сессии._

2.  `WAIT(3)` _Пауза: хотя ошибка должна быть синхронной (400 сразу), закладываем время на случай, если парсер «думает»._

3.  `api.get(id)` ⚠️ _Проверяем, что сессия_ **_не повреждена_**_: status = 0 (CREATED), нет полей с ошибкой импорта,_ `importStatus` _отсутствует или = 0._

4.  `api.import_(id, file=valid.xlsx)` ⚠️ _Повторный импорт с корректным файлом. Проверяем, что сессия «взбодрилась» и принимает данные._

5.  `WAIT(5)`

6.  `api.get(id)` ⚠️ _Проверяем: status = 7 (IMPORTED). Импорт после ошибки — успешен._



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 1 | HTTP 400, `{"error":"Invalid file format"}` | Формат не распознан |
| 3 | `status = 0` (CREATED) | Сессия не повреждена |
| 6 | `status = 7` (IMPORTED) | Повторный импорт успешен |


**Teardown:** `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-029 — Импорт: превышение максимального размера


**Требование:** R-HYDR-067

**Описание:** Файл импорта превышает `maxImportSize = 50 МБ`. Система отклоняет с 413 (Payload Too Large). Сессия не повреждена.

**Предусловие:**


*   Сессия modelling создана (status = 0)

*   Подготовлен файл размером 51 МБ (XLSX с миллионами строк)



**Действия:**


1.  `api.import_(id, file=huge_file.xlsx)` ⚠️ _(51 МБ)_ _Загружаем файл, превышающий лимит. Ожидаем: сервер отклоняет_ **_до_** _парсинга (по размеру), не тратя ресурсы на разбор 51 МБ._

2.  `api.get(id)` ⚠️ _Проверяем: сессия не повреждена, status = 0._



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 1 | HTTP 413, `{"error":"File exceeds maximum size (50 MB)"}` | Превышен лимит |
| 2 | `status = 0` (CREATED) | Не повреждена |


**Teardown:** `api.close(id)` ⚠️ → `RESET()`


* * *



### 3.5 Работа с файлами: экспорт



* * *



#### HY-HIST-030 — Экспорт результатов в CSV


**Требование:** R-HYDR-068

**Описание:** После завершения historical-сессии оператор экспортирует расчётные результаты в CSV. Файл содержит все рассчитанные значения (напоры, перепады, расход) за период сессии. Формат: стандартный CSV с заголовком.

**Формат CSV (результат):**


```csv
tag,timestamp,value,invalid
MT1.LU1.SGLU1.KIP1.TI.Head,2026-11-09T08:00:00Z,663.2,false
MT1.LU1.SGLU1.KIP1.TI.Head,2026-11-09T08:00:01Z,663.3,false
MT1.LU1.SGLU1.KIP1.TI.PressDelta,2026-11-09T08:00:00Z,0.0,false
MT1.LU1.UR1.TI.QVmomDelta,2026-11-09T08:00:00Z,5.0,false
```


**Предусловие:**


*   Сессия historical завершена (status = 8, DONE)

*   Период: 08:00–08:10, speedRatio = 10000

*   В `model_main_{id}` есть результаты (≥ 600 сообщений: 600 с × 1 msg/с × несколько тегов)

*   Расчётные теги присутствуют: Head, PressDelta, QVmomDelta



**Действия:**


1.  `api.export_(id, format="csv", startTime="2026-11-09T08:00:00Z", endTime="2026-11-09T08:05:00Z")` ⚠️ _Запрашиваем экспорт за 5 минут (не весь период — для ускорения теста). Система: (а) читает результаты из_ `model_main_{id}` _(или из CH, если там сохранены) за указанный диапазон, (б) формирует CSV, (в) возвращает как body ответа. Метод: GET или POST — зависит от реализации._

2.  `WAIT(10)` _Время на: чтение из Kafka/CH, формирование CSV, передачу ответа. Для 5 минут × ~5 тегов = ~1500 строк — быстро._

3.  Проверить HTTP-ответ: статус 200, `Content-Type: text/csv` _Убеждаемся, что ответ — файл, а не JSON-ошибка._

4.  Парсить CSV: подсчитать общее число строк (без заголовка) _Ожидаем: ≥ 500 строк (5 мин × 60 с × ~2-3 расчётных тега). Точное число зависит от того, сколько тегов публикует hydro-calculation._

5.  Проверить: в CSV есть строки для `KIP1.TI.Head`, `KIP1.TI.PressDelta`, `UR1.TI.QVmomDelta` _Базовые расчётные теги должны быть в выгрузке. Если их нет — либо hydro-calculation не рассчитал, либо экспорт отфильтровал._

6.  Проверить выборочно: возьмём строку `Head` за `08:00:30Z` и сравним с данными в `model_main_{id}` (через `kafka.consume`) _Значение должно совпадать (точность ± 0.01). Это подтверждает, что экспорт не тормозит и отдал правильные данные из реального потока._



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 3 | HTTP 200, Content-Type: text/csv | Файл сформирован |
| 4 | ≥ 500 строк | Данные за 5 минут |
| 5 | Есть Head, PressDelta, QVmomDelta | Базовые теги присутствуют |
| 6 | Значения совпадают с Kafka | Нет расхождения |


**Teardown:** `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-031 — Экспорт: пустой диапазон


**Требование:** R-HYDR-068

**Описание:** Оператор запрашивает экспорт за период, за который нет данных (например, 20:00–21:00, но сессия шла 08:00–08:10). Система возвращает HTTP 200 с CSV, содержащим только заголовок (0 строк данных). Это **не ошибка** — оператор просто запросил несуществующий период.

**Предусловие:**


*   Сессия historical завершена (status = 8), период 08:00–08:10

*   В `model_main_{id}` данные только за 08:00–08:10



**Действия:**


1.  `api.export_(id, format="csv", startTime="2026-11-09T20:00:00Z", endTime="2026-11-09T21:00:00Z")` ⚠️ _Запрашиваем за 20:00–21:00 — период, за который сессия не работала. Система ищет данные → не находит → формирует пустой CSV._

2.  Проверить: HTTP 200, Content-Type: text/csv, тело = только заголовок `tag,timestamp,value,invalid` (без строк данных)



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 2 | HTTP 200, 1 строка (заголовок), 0 строк данных | Пустой диапазон |


_(Допущение: возвращаем 200 с пустым CSV, а не 404.)_

**Teardown:** `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-032 — Экспорт в JSON (структурированный)


**Требование:** R-HYDR-068

**Описание:** Экспорт в JSON — для программной обработки (Python-скрипт, интеграция с другой системой). В отличие от CSV (плоский, все теги в одной таблице), JSON группирует данные по тегам и содержит метаданные (sessionId, период, единицы измерения).

**Формат JSON:**


```json
{
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "processingMode": 0,
  "period": {"start": "2026-11-09T08:00:00Z", "end": "2026-11-09T08:02:00Z"},
  "exportedAt": "2026-11-09T12:00:00Z",
  "tags": [
    {
      "tag": "MT1.LU1.SGLU1.KIP1.TI.Head",
      "unit": "m",
      "count": 120,
      "data": [
        {"ts": "2026-11-09T08:00:00Z", "value": 663.2, "invalid": false},
        {"ts": "2026-11-09T08:00:01Z", "value": 663.3, "invalid": false}
      ]
    },
    {
      "tag": "MT1.LU1.SGLU1.KIP1.TI.PressDelta",
      "unit": "kgf/cm2",
      "count": 120,
      "data": [...]
    }
  ]
}
```


**Предусловие:**


*   Сессия historical завершена (status = 8), есть данные



**Действия:**


1.  `api.export_(id, format="json", startTime="2026-11-09T08:00:00Z", endTime="2026-11-09T08:02:00Z")` ⚠️ _Запрашиваем JSON за 2 минуты. Система группирует данные по тегам, добавляет метаданные._

2.  Проверить: HTTP 200, `Content-Type: application/json`

3.  Парсить JSON:
    *   `sessionId` = тестовый UUID

    *   `processingMode` = 0 (historical)

    *   `period.start` = 08:00:00, `period.end` = 08:02:00

    *   `tags` — массив, длина ≥ 1

    *   Для каждого тега: `data` — массив, `count` = длина `data`

4.  Проверить: для тега `Head` значение `data[0].value ≈ 663.2` (согласуется с CSV из HY-HIST-030)



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 2 | HTTP 200, application/json | Корректный формат |
| 3 | Валидный JSON, структура соответствует | Метаданные + данные |
| 4 | `Head[0].value ≈ 663.2` | Согласованность с CSV |


**Teardown:** `api.close(id)` ⚠️ → `RESET()`


* * *



### 3.6 Watermark и прогресс



* * *



#### HY-HIST-033 — Watermark: монотонность


**Требование:** R-HYDR-059

**Описание:** Watermark — монотонно неубывающая величина. Она никогда не может уменьшиться (в пределах одной сессии). Если watermark «отскочил» назад — это баг: дубли в данных, неверные расчёты, ложные алармы.

**Причинно-следственная связь:** Watermark = max(ts всех обработанных сообщений). Математически: max(A, B) ≥ A всегда. Если в коде есть `watermark = message.ts` (без max) — при неупорядоченной доставке Kafka watermark может «отскочить». Сценарий ловит именно этот баг.

**Предусловие:**


*   Сессия historical запущена, `speedRatio = 2000` (2×), `watermark ≈ 08:05:00`

*   Сессия стабильно работает (не в ERROR, не PAUSED)



**Действия:**


1.  `api.watermark(id)` ⚠️ → `wm1` _Захват 1. Читаем текущий watermark. Записываем значение._

2.  `WAIT(10)` _10 с реального × 2× = 20 с виртуального. Watermark должен вырасти примерно на 20 с._

3.  `api.watermark(id)` ⚠️ → `wm2` _Захват 2. Сравниваем с wm1:_ `wm2 ≥ wm1`_. Разница: ≈ 20 с (± 20% на задержки)._

4.  `WAIT(10)`

5.  `api.watermark(id)` ⚠️ → `wm3` _Захват 3. Сравниваем с wm2:_ `wm3 ≥ wm2`_._

6.  `WAIT(10)`

7.  `api.watermark(id)` ⚠️ → `wm4` _Захват 4. Сравниваем с wm3:_ `wm4 ≥ wm3`_._

8.  Итоговая проверка: `wm1 ≤ wm2 ≤ wm3 ≤ wm4` (строгая неубывающая последовательность) _Если хотя бы одно нарушение (wm2 < wm1) —_ **_баг_**_: watermark отскочил назад._



**Ожидаемый результат:**

| Пара | Ожидание | Допустимая дельта |
| --- | --- | --- |
| wm2 - wm1 | > 0 (вырос) | ≈ 20 с ± 4 с |
| wm3 - wm2 | > 0 | ≈ 20 с ± 4 с |
| wm4 - wm3 | > 0 | ≈ 20 с ± 4 с |
| Монотонность | wm1 ≤ wm2 ≤ wm3 ≤ wm4 | Без исключений |


**Примечание:** Равенство (wm2 = wm1) допустимо, если за 10 с не было новых сообщений (например, пауза в потоке). Но **уменьшение** — никогда.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-034 — Watermark: STALLED → MOVING (восстановление)


**Требование:** R-HYDR-059

**Описание:** Watermark застрял (STALLED) из-за временного сбоя (например, hydro-calculation не публикует результаты). После восстановления — watermark снова движется (MOVING). Проверяем полный цикл: MOVING → STALLED → MOVING + соответствующие WS-события.

**Предусловие:**


*   Сессия historical запущена, `watermarkState = 1` (MOVING)

*   `lagThreshold` временно = 10 с _(уточнить механизм изменения)_



**Действия:**


1.  `ws.subscribe(id)` _Подписываемся на события: будем ловить WATERMARK_STALLED и WATERMARK_UPDATED._

2.  Эмулировать сбой: остановить hydro-calculation (`kill` или отключить Kafka consumer для `model_main_{id}`) _Теперь hydro-calc не публикует результаты. Mod-hist продолжает читать входные данные, но watermark не обновляется (потому что max(обработанных) не растёт — hydro-calc не ответил)._

3.  `WAIT(20)` — 10 с lagThreshold + 10 с margin _Ждём, пока mod-hist «заметит», что watermark не двигается 10 с._

4.  `ws.wait_event(id, 8, timeout=30)` — WATERMARK_STALLED (type=8) _Ожидаем событие: watermark застрял. В_ `data.lag` _— величина отставания._

5.  `api.watermark(id)` ⚠️ _Проверяем:_ `state = 2` _(STALLED),_ `lag > 10` _(превышен порог)._

6.  Восстановить hydro-calculation (запустить обратно) _Hydro-calc снова публикует. Mod-hist получает результаты, watermark «догоняет»._

7.  `WAIT(15)` _Время на: hydro-calc обработал накопленное → mod-hist обновил watermark._

8.  `api.watermark(id)` ⚠️ _Проверяем:_ `state = 1` _(MOVING),_ `lag = 0` _(догнал)._

9.  `ws.wait_event(id, 7, timeout=30)` — WATERMARK_UPDATED (type=7) _Событие: watermark снова двигается._



**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 4 | `type=8` (STALLED), `data.lag > 10` | Watermark застрял |
| 5 | `state = 2`, `lag > 10` | Подтверждено через REST |
| 8 | `state = 1` (MOVING), `lag = 0` | Восстановлен |
| 9 | `type=7` (WATERMARK_UPDATED) | Событие возобновления |


**Примечание:** Если lagThreshold не можно изменить в тесте — используем 120 с (стандарт) и ждём 130 с. Для автотеста это долго, но корректно.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-035 — Прогресс: расчёт по формуле


**Требование:** R-HYDR-061

**Описание:** Проверяем, что `progress` корректно рассчитывается по формуле: `((watermark - startTime) / (targetTime - startTime)) × 100`. Снимаем 3 точки через равные интервалы и проверяем линейный рост.

**Формула:** `progress% = ((wm - start) / (target - start)) × 100`

**Предусловие:**


*   Сессия historical: `start = 08:00`, `target = 08:10` (600 с), `speedRatio = 10000` (10×)

*   Сессия запущена, watermark движется



**Действия:**


1.  `api.start(id)` ⚠️ _(если ещё не запущена)_ _Запускаем. Watermark начинает с 08:00._

2.  `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED

3.  `WAIT(3)` — 3 с реального × 10× = 30 с виртуального _Ждём ровно 3 с. За это время watermark должен продвинуться на ~30 с._

4.  `api.progress(id)` ⚠️ → `p1`, `api.watermark(id)` ⚠️ → `wm1` _Захват 1. Ожидаем: progress ≈ 5% (30/600×100). Watermark ≈ 08:00:30._

5.  `WAIT(3)` — ещё 30 с виртуального

6.  `api.progress(id)` ⚠️ → `p2`, `api.watermark(id)` ⚠️ → `wm2` _Захват 2. Ожидаем: progress ≈ 10% (60/600×100). Watermark ≈ 08:01:00._

7.  `WAIT(3)` — ещё 30 с виртуального

8.  `api.progress(id)` ⚠️ → `p3`, `api.watermark(id)` ⚠️ → `wm3` _Захват 3. Ожидаем: progress ≈ 15% (90/600×100). Watermark ≈ 08:01:30._

9.  Проверить линейность: `(p2 - p1) ≈ (p3 - p2) ≈ 5%` _Если прогресс «скачет» (например, p1=5%, p2=12%, p3=14%) — неравномерная обработка, возможный баг в WorkerExecutor._



**Ожидаемый результат:**

| Захват | Progress (ожид.) | Watermark (ожид.) | Дельта progress |
| --- | --- | --- | --- |
| p1 | ≈ 5% | 08:00:30 | — |
| p2 | ≈ 10% | 08:01:00 | ≈ 5% |
| p3 | ≈ 15% | 08:01:30 | ≈ 5% |


Допустимое отклонение: ± 2% (задержки Kafka, округление).

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`


* * *



#### HY-HIST-036 — Прогресс: ETA


**Требование:** R-HYDR-061

**Описание:** `etaSeconds` — оценка, сколько реального времени осталось до завершения. Формула: `ETA = (targetTime - watermark) / speedRatio × 1000` (в мс) или `/ (speedRatio/1000)` (в с).

**Формула:** `ETA (с) = (target - wm) / (speedRatio / 1000)`

**Пример:** target = 08:10, wm = 08:05, speedRatio = 10000 (10×) → ETA = 300 / 10 = 30 с реального

**Предусловие:**


*   Сессия historical: `start = 08:00`, `target = 08:10`, `speedRatio = 10000`

*   Сессия запущена, `watermark ≈ 08:05:00` (300 с из 600 с)



**Действия:**


1.  `api.progress(id)` ⚠️ _Читаем прогресс и ETA. Ожидаем: progress = 50%, etaSeconds ≈ 30._

2.  `WAIT(10)` — 10 с реального × 10× = 100 с виртуального _Watermark сдвинется ещё на 100 с. Осталось: 600 - 400 = 200 с виртуального. ETA = 200/10 = 20 с._

3.  `api.progress(id)` ⚠️ _Ожидаем: progress ≈ 66.7%, etaSeconds ≈ 20._



**Ожидаемый результат:**

| Шаг | Progress | ETA (ожид.) | Пояснение |
| --- | --- | --- | --- |
| 1 | 50% | ≈ 30 с | 300 с ост. / 10× |
| 3 | ≈ 67% | ≈ 20 с | 200 с ост. / 10× |


Допустимое отклонение ETA: ± 5 с (задержки, округление).

**Примечание:** Если ETA = 0 при progress < 100% — баг (система думает, что всё уже обработано).

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET



### 3.7 Отказоустойчивость и алармы

* * *

#### HY-HIST-037 — Buffer Overflow: переполнение буфера

**Требование:** R-HYDR-070
**Описание:** Если входящий поток данных быстрее, чем WorkerExecutor обрабатывает (публикует в Kafka), кольцевой буфер (10 000 сообщений) переполняется. Старые сообщения теряются (FIFO). Система генерирует событие `BUFFER_OVERFLOW` (type=12) и фиксирует счётчик потерянных сообщений (`messagesDropped`).
**Причинно-следственная связь:** Буфер — буферизация между «приёмом из CH/Kafka» и «публикацией в model_main_{id}». Если consumer (WorkerExecutor) не успевает за producer (DataExchange), данные копят в буфере. При переполнении — старые вытесняются новыми. Оператор должен знать: «данные потеряны, расчёт за этот период неполный». Если буфер переполняется **тихо** (без аларма) — расчёт будет неверен, а оператор об этом не узнает.
**Предусловие:**

*   Сессия historical запущена, `speedRatio = 10000` (10×)

*   `bufferSize` временно = 100 _(уточнить механизм: Redis key / config / env — чтобы переполнение произошло за ~2 с, а не за 100 с)_

*   Поток данных: 50 msg/с (быстрее обработки при уменьшенном буфере)


**Действия:**

1.  `ws.subscribe(id)` _Подписываемся на события сессии. Будем ловить BUFFER_OVERFLOW (type=12). Это критично: если событие не придёт — значит, переполнение не было детектировано (баг в детекции)._

2.  `api.get(id)` ⚠️ _Зафиксировать исходное состояние:_ `messagesDropped = 0`_,_ `bufferUsed` _= некоторое значение. Это «нулевая точка» для сравнения._

3.  `kafka.consume("model_main_" + id, timeout=5)` → `count_before` _Подсчитать, сколько сообщений уже в_ `model_main_{id}` _до переполнения. Это базовая линия: после переполнения мы проверим, что не все сообщения пришли._

4.  `WAIT(5)` — 5 с × 50 msg/с = 250 сообщений > 100 (буфер) _Ждём 5 с. За это время в буфер попадёт 250 сообщений, но вместимость 100 → 150 потеряны. WorkerExecutor успевает опубликовать только ~100._

5.  `ws.wait_event(id, 12, timeout=15)` — BUFFER_OVERFLOW (type=12) _Ожидаем событие переполнения. В_ `data` _должно быть:_ `dropped` _(число потерянных) или_ `bufferUsed = 100` _(полный буфер). Если событие не пришло за 15 с —_ **_баг_**_: переполнение не детектировано._

6.  `api.get(id)` ⚠️ _Проверяем:_ `messagesDropped > 0` _(конкретно: ≈ 150, допустимое отклонение ± 30 из-за асинхронности)._ `bufferUsed = 100` _(буфер полон)._

7.  `kafka.consume("model_main_" + id, timeout=10)` → `count_after` _Подсчитываем сообщения в_ `model_main_{id}` _после переполнения. Ожидаем:_ `count_after < count_before + 250`_. Разница = потерянные сообщения. Если_ `count_after = count_before + 250` _— буфер не переполнялся (баг в эмуляции)._

8.  `redis.get("session:" + id + ":watermark")` _Проверяем, что watermark_ **_не сломан_** _из-за переполнения. Он должен продолжать двигаться (возможно, с «провалом» — пропущенные ts). Ключевое: watermark не должен «отскочить» назад._


**Ожидаемый результат:**
| Шаг | Ожидание | Для локализации |
| --- | --- | --- |
| 5 | `type=12` (BUFFER_OVERFLOW), `data.dropped ≈ 150` | Если нет события → баг в детекции (Watermark/WorkerExecutor) |
| 6 | `messagesDropped ≈ 150`, `bufferUsed = 100` | Если 0 → буфер не переполнялся (эмуляция не сработала) |
| 7 | `count_after < count_before + 250` | Если равен → сообщения не терялись (буфер больше, чем задумано) |
| 8 | Watermark не отскочил назад | Если отскочил → баг в логике max() |

**Примечание:**

*   Механизм уменьшения bufferSize в тесте: **уточнить** (Redis / config / env)

*   Если уменьшить буфер не получается — используем стандартные 10 000 и ускоряем producer (отправляем 10 000+ сообщений за 1 с через `kafka.send` напрямую в внутренний буфер, минуя DataExchange)

*   Событие BUFFER_OVERFLOW должно прийти **до** того, как все 150 сообщений потеряны (детекция на пороге 90% или при первом вытеснении)


**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()` (с возвратом bufferSize к 10 000)

* * *

#### HY-HIST-038 — SESSION_ERROR: hydro-calculation не отвечает

**Требование:** R-HYDR-072
**Описание:** Hydro-calculation не отвечает на команду START (не прислал подтверждение в `mod-hist-results` за 30 с). Mod-hist переходит в ERROR (status=12). Оператор получает событие SESSION_ERROR (type=6) и видит причину: «hydro-calculation не отвечает».
**Причинно-следственная связь:** Mod-hist отправляет START в Kafka (`mod-hist-commands`). Hydro-calculation должен: (а) прочитать сообщение, (б) подписаться на `model_main_{id}`, (в) прислать подтверждение в `mod-hist-results`. Если hydro-calc упал / не запущен / Kafka ACL не позволяет читать — подтверждения не будет. Через 30 с (confirmTimeoutMs) mod-hist считает: «расчёты не идут» → ERROR.
**Почему это важно:** Без этого механизма сессия бы «зависла» в OPENING (status=1) навсегда. Оператор бы думал, что всё работает, а на самом деле — нет.
**Предусловие:**

*   Hydro-calculation **остановлен** (kill процесса или отключение Kafka consumer)

*   Сессия historical создана (status = 0, CREATED)


**Действия:**

1.  `pg.query("SELECT status FROM sessions WHERE id = '<id>'")` Проверяем в БД, что сессия действительно в CREATED (0).

2.  `ws.subscribe(id)` _Подписываемся. Будем ловить SESSION_ERROR (type=6). Если событие не придёт — проверяем по Redis/PostgreSQL (шаги 5-6)._

3.  `api.start(id)` ⚠️ _Отправляем START. Mod-hist: (а) меняет статус 0→1 (OPENING), (б) публикует START в_ `mod-hist-commands`_, (в) начинает таймер 30 с. Hydro-calc не читает (упал) → подтверждения нет._

4.  `kafka.consume("mod-hist-commands", {"sessionId": id, "command": "START"}, timeout=5)` _Проверяем, что команда START_ **_направлена_** _в Kafka. Это важно для локализации: если START нет в Kafka — проблема в mod-hist (не опубликовал). Если START есть, но hydro-calc не ответил — проблема в hydro-calc / Kafka._

5.  `WAIT(40)` — 30 с confirmTimeout + 10 с margin _Ждём таймаут. 30 с — время ожидания подтверждения. 10 с — запас на задержки._

6.  `ws.wait_event(id, 6, timeout=50)` — SESSION_ERROR (type=6) _Ожидаем событие ошибки. В_ `data.error` _— причина: «hydro-calculation not responding (timeout 30s)» или аналогичное._

7.  `api.get(id)` ⚠️ _Проверяем:_ `status = 12` _(ERROR). Поле_ `error` _или_ `errorReason` _— заполнено._

8.  `redis.get("session:" + id + ":status")` _Кросс-проверка: в Redis тоже 12 (ERROR). Если в Redis 1 (OPENING), а в PostgreSQL 12 — рассинхронизация (баг в обновлении кэша)._

9.  `pg.query("SELECT status, error_reason FROM sessions WHERE id = '<id>'")` _Кросс-проверка в БД: status = 12, error_reason заполнено. Это «источник истины» — если Redis и PG не совпадают, берём PG._


**Ожидаемый результат:**
| Шаг | Ожидание | Для локализации |
| --- | --- | --- |
| 4 | START есть в `mod-hist-commands` | Если нет → mod-hist не опубликовал (баг в SessionWorker) |
| 6 | `type=6`, `data.error` содержит «timeout» или «not responding» | Если нет события → баг в таймаут-обработчике |
| 7 | `status = 12` (ERROR) | Основной критерий |
| 8 | Redis: 12 | Если ≠ 12 → рассинхронизация Redis/PG |
| 9 | PG: 12, error_reason ≠ null | Источник истины |

**Примечание:**

*   Если confirmTimeoutMs нельзя изменить в тесте — ждём 30 с (стандарт). Для автотеста это приемлемо.

*   Альтернативная эмуляция: вместо kill hydro-calc — настроить Kafka ACL, чтобы hydro-calc не мог читать `mod-hist-commands`. Результат тот же, но hydro-calc не «умирает» (удобнее для последующего retry-теста).


**Teardown:** Восстановить hydro-calculation (запустить) → `api.close(id)` ⚠️ → `RESET()`

* * *

#### HY-HIST-039 — Retry: повторный запуск после ERROR

**Требование:** R-HYDR-072
**Описание:** Сессия в ERROR (hydro-calc не ответил). Тестировщик «чинит» ситуацию (запускает hydro-calc) и нажимает retry. Система: возвращает сессию в PLAYING (status=3) с **того же** watermark (не начинается заново).
**В отличие от создания новой сессии:** retry сохраняет: (а) уже обработанные данные (не перечитываем из CH), (б) время (не ждём снова OPENING на 30 с), (в) контекст (оператор видит: «я был на 08:03, продолжил с 08:03»).
**Предусловие:**

*   Сессия historical в ERROR (status=12), `watermark = "2026-11-09T08:03:00Z"`

*   Hydro-calculation **восстановлен** (запущен, готов принимать команды)

*   `mod-hist-results` в Kafka доступен (hydro-calc сможет ответить)


**Действия:**

1.  `kafka.consume("mod-hist-results", {"sessionId": id}, timeout=10)` _Проверяем, что hydro-calc_ **_жив_** _и отвечает. Если есть свежее сообщение в_ `mod-hist-results` _— hydro-calc работает. Если нет за 10 с — hydro-calc всё ещё не готов, retry не имеет смысла._

2.  `ws.subscribe(id)` _Подписываемся. Будем ловить SESSION_OPENED (type=1) после retry._

3.  `api.retry(id)` ⚠️ _(или_ `api.start(id)` _⚠️ — зависит от реализации: отдельный endpoint retry или повторный start для ERROR-сессии)_ _Запускаем retry. Ожидаем: mod-hist меняет статус 12→1 (OPENING)→3 (PLAYING). Публикует START в_ `mod-hist-commands`_. Hydro-calc на этот раз ответит (он жив)._

4.  `kafka.consume("mod-hist-commands", {"sessionId": id, "command": "START"}, timeout=10)` _Проверяем, что START_ **_повторно_** _опубликован. Это важно: если START нет — mod-hist не отправил команду (баг в retry-логике: «уже отправлял, не буду»). Ожидаем: есть второй START._

5.  `WAIT(15)` _Время на: hydro-calc прочитал START → подписался на model_main → прислал подтверждение → mod-hist перевёл в PLAYING._

6.  `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED (type=1) _Событие: сессия открыта (PLAYING). Если не пришло за 30 с — гидро-calc не ответил повторно (возврат к ERROR)._

7.  `api.get(id)` ⚠️ _Проверяем:_ `status = 3` _(PLAYING)._ `startedAt` _—_ **_не перезаписан_** _(осталось время первого запуска, а не retry). Поле_ `error` _— очищено._

8.  `api.watermark(id)` ⚠️ _Критичная проверка:_ `watermark = "2026-11-09T08:03:00Z"`_. Watermark_ **_не сбросился_** _на startTime (08:00). Обработка продолжается с 08:03._

9.  `WAIT(10)` — 10 с × 10× = 100 с виртуального _Даём время на обработку. Watermark должен начать двигаться._

10.  `api.watermark(id)` ⚠️ → `wm_after` _Проверяем:_ `wm_after > "2026-11-09T08:03:00Z"`_. Watermark двигается — обработка идёт._

11.  `redis.get("session:" + id + ":status")` _Кросс-проверка: Redis = 3 (PLAYING). Согласуется с PG._


**Ожидаемый результат:**
| Шаг | Ожидание | Для локализации |
| --- | --- | --- |
| 1 | Hydro-calc отвечает в `mod-hist-results` | Если нет → hydro-calc не восстановлен, тест не валиден |
| 4 | Второй START в `mod-hist-commands` | Если нет → retry не публикует команду (баг) |
| 6 | `type=1` (SESSION_OPENED) | Если нет → гидро-calc снова не ответил (повторный ERROR) |
| 7 | `status = 3`, `error` очищен | Если error не очищен → UI покажет старую ошибку |
| 8 | `watermark = 08:03:00` (не сбросился) | **Критично**: если 08:00 → retry начал заново (баг) |
| 10 | `wm_after > 08:03:00` | Если = 08:03 → watermark не двигается (обработка не идёт) |

**Примечание:**

*   Если отдельный endpoint `retry` не существует (псевдо) — используем `api.start(id)` ⚠️ для сессии в ERROR. Ожидаемое поведение: mod-hist разрешает start для ERROR-сессии (аналогично идемпотентности, но с восстановлением).

*   Если mod-hist **не** позволяет start для ERROR (возвращает 409) — это тоже допустимо: оператор должен создать новую сессию. В этом случае сценарий помечается как «не применимо к текущей реализации» и требуется обсуждение.


**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

* * *

### 3.8 Конфигурация и граничные случаи

* * *

#### HY-HIST-040 — Список сессий: фильтрация

**Требование:** R-HYDR-074
**Описание:** `api.list` ⚠️ поддерживает фильтрацию по `status`, `processingMode`, `targets`. Проверяем каждую комбинацию фильтров и их пересечение.
**Предусловие:**

*   Созданы 3 сессии с разными параметрами:
    *   **S1:** `processingMode = 0` (historical), `status = 3` (PLAYING), `targets = ["MT1.LU1"]`

    *   **S2:** `processingMode = 1` (modelling), `status = 2` (PAUSED), `targets = ["MT1.LU2"]`

    *   **S3:** `processingMode = 2` (timeshift), `status = 8` (DONE), `targets = ["MT1.LU1"]`


**Действия:**

1.  `api.list({status: 3})` ⚠️ _Фильтр по статусу: только PLAYING. Ожидаем: S1 (одна сессия). S2 (PAUSED=2) и S3 (DONE=8) — отфильтрованы._

2.  `api.list({processingMode: 1})` ⚠️ _Фильтр по режиму: только modelling. Ожидаем: S2 (одна сессия). S1 (historical=0) и S3 (timeshift=2) — отфильтрованы._

3.  `api.list({status: 3, processingMode: 0})` ⚠️ _Пересечение: PLAYING + historical. Ожидаем: S1. Это «узкий» фильтр — только сессии, которые одновременно и играют, и historical._

4.  `api.list({targets: "MT1.LU1"})` ⚠️ _Фильтр по targets: сессии, где MT1.LU1 в списке. Ожидаем: S1 и S3 (обе имеют MT1.LU1). S2 (MT1.LU2) — отфильтрована._

5.  `api.list({})` ⚠️ _Без фильтров: все сессии. Ожидаем: S1, S2, S3 (3 сессии)._

6.  `api.list({status: 3, processingMode: 2})` ⚠️ _Пересечение «пустое»: PLAYING + timeshift. Ни одна сессия не подходит (S3 — DONE, не PLAYING; S1 — historical, не timeshift). Ожидаем: пустой массив._

7.  `api.list({status: 99})` ⚠️ _Невалидный статус (99 не существует). Ожидаем: пустой массив (не 500). Система не должна падать на неизвестном значении._


**Ожидаемый результат:**
| Шаг | Фильтр | Ожидаемый результат | Кол-во |
| --- | --- | --- | --- |
| 1 | status=3 | S1 | 1 |
| 2 | processingMode=1 | S2 | 1 |
| 3 | status=3, mode=0 | S1 | 1 |
| 4 | targets="MT1.LU1" | S1, S3 | 2 |
| 5 | (без фильтров) | S1, S2, S3 | 3 |
| 6 | status=3, mode=2 | (пусто) | 0 |
| 7 | status=99 | (пусто) | 0 |

**Teardown:** `api.stop` ⚠️ + `api.close` ⚠️ для всех 3 → `RESET()`

* * *

#### HY-HIST-041 — Доступ к несуществующей сессии (404)

**Требование:** R-HYDR-075
**Описание:** Запрос к несуществующему sessionId возвращает HTTP 404. Система не должна падать с 500 или возвращать пустой объект. 404 — корректная реакция: «такой сессии нет».
**Предусловие:**

*   Сессия с ID `0000` **не существует**

*   Стенд в начальном состоянии (нет сессий)


**Действия:**

1.  `api.get("0000")` ⚠️ _GET к несуществующей сессии. Ожидаем: 404. Тело:_ `{"error":"Session not found"}` _или аналогичное. Это базовый кейс: «сессии нет»._

2.  `api.start("0000")` ⚠️ _Попытка запустить несуществующую сессию. Ожидаем: 404 (не 409, не 500). Логика: если сессии нет — её нельзя запустить. 404 = «не нашла», 409 = «нашла, но нельзя». Здесь — «не нашла»._

3.  `api.pause("0000")` ⚠️ _Попытка паузы. Ожидаем: 404._

4.  `api.close("0000")` ⚠️ _Попытка закрытия. Ожидаем: 404._

5.  `api.watermark("0000")` ⚠️ _Попытка чтения watermark. Ожидаем: 404._

6.  `pg.query("SELECT * FROM sessions WHERE id = '0000'")` _Кросс-проверка: в БД записи нет. Подтверждаем, что 404 — не баг, а корректное поведение (сессия действительно не существует)._


**Ожидаемый результат:**
| Шаг | Операция | Ожидаемый код | Пояснение |
| --- | --- | --- | --- |
| 1 | GET | 404 | Сессия не найдена |
| 2 | START | 404 | Нельзя запустить то, чего нет |
| 3 | PAUSE | 404 | Нельзя приостановить то, чего нет |
| 4 | CLOSE | 404 | Нельзя закрыть то, чего нет |
| 5 | WATERMARK | 404 | Нельзя прочитать то, чего нет |
| 6 | PG query | 0 строк | Подтверждение: сессии нет в БД |

**Примечание:** Если для `api.close` возвращают 204 (No Content) вместо 404 — это допустимо (идемпотентность: «закрыть то, чего нет» = «ничего не делать»). Но для GET/START/PAUSE — строго 404.
**Teardown:** `RESET()`

* * *

#### HY-HIST-042 — WebSocket: отключение клиента не влияет на сессию

**Требование:** R-HYDR-076
**Описание:** UI отключается от WebSocket (закрыта вкладка, потеря сети, перезагрузка). Сессия **не должна** остановиться. WS — канал только для уведомлений, не для управления. Все операции (pause, stop, advance) идут через REST. Если сессия зависит от WS-подключения — это архитектурный баг.
**Причинно-следственная связь:** WS — «односторонняя» связь: mod-hist → клиент (уведомления). Клиент не управляет сессией через WS. Если бы управление шло через WS — при обрыве сессия бы «зависла». Но управление — REST (отдельный канал). WS-обрыв = «оператор не видит события», но сессия работает.
**Предусловие:**

*   Сессия historical запущена (status = 3, PLAYING), `speedRatio = 2000` (2×)

*   WS-подключение активно, события приходят


**Действия:**

1.  `ws.subscribe(id)` _Подписываемся. Убеждаемся, что события приходят (ожидание одного WATERMARK_UPDATED за 10 с)._

2.  `ws.wait_event(id, 7, timeout=15)` — WATERMARK_UPDATED _Подтверждаем: WS работает, события приходят. Watermark движется._

3.  Закрыть WS-соединение (disconnect client) _Имитация: оператор закрыл вкладку / потерял сеть. WS-сокет закрывается. Mod-hist замечает отключение (close frame), но_ **_не должен_** _останавливать сессию._

4.  `WAIT(15)` _15 с без WS. За это время: (а) watermark должен продвинуться (15 с × 2× = 30 с виртуального), (б) сессия должна остаться в PLAYING. Если сессия «зависла» — она бы не двигалась._

5.  `api.get(id)` ⚠️ _Проверяем через REST:_ `status = 3` _(PLAYING). Если status = 12 (ERROR) или 2 (PAUSED) — сессия пострадала от WS-обрыва (_**_баг_**_)._

6.  `api.watermark(id)` ⚠️ → `wm_after` _Проверяем: watermark продвинулся._ `wm_after > wm_шаг2`_. Разница: ≈ 30 с (15 с реального × 2×). Если watermark не изменился — сессия «зависла»._

7.  `kafka.consume("model_main_" + id, timeout=10)` _Проверяем, что в Kafka_ **_есть_** _свежие сообщения (за последние 15 с). Если нет — WorkerExecutor остановился (баг)._

8.  `ws.subscribe(id)` — переподключение _Переподключаемся. Проверяем: (а) подписка успешна, (б) события продолжают приходить._

9.  `ws.wait_event(id, 7, timeout=15)` — WATERMARK_UPDATED _После переподключения события идут. Если не пришло за 15 с — WS не восстановился (баг в reconnection-логике)._

10.  `api.get(id)` ⚠️ _Финальная проверка:_ `status = 3` _(PLAYING). Сессия работает как ни в чём не бывало._


**Ожидаемый результат:**
| Шаг | Ожидание | Для локализации |
| --- | --- | --- |
| 5 | `status = 3` (PLAYING) | Если ≠ 3 → WS-обрыв влияет на сессию (баг) |
| 6 | `wm_after > wm_шаг2`, дельта ≈ 30 с | Если не изменился → WorkerExecutor остановился |
| 7 | Свежие сообщения в Kafka | Если нет → публикация прекратилась |
| 9 | WATERMARK_UPDATED приходит | Если нет → WS не восстановился |
| 10 | `status = 3` | Финальное подтверждение |

**Примечание:**

*   _(Допущение: WS не буферизует события при отключении. При переподключении оператор получает только_ **_новые_** _события, пропущенные за время отключения — потеряны.)_

*   Если реализация **буферизует** (например, 100 последних событий) — при переподключении придёт «залип» старых событий. Это допустимо, но нужно проверить, что они не дублируются.


**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

* * *

#### HY-HIST-044 — Cleanup: автоматическая очистка устаревших сессий

**Требование:** R-HYDR-078
**Описание:** Периодически (каждый `Cleanup.intervalMs` = 3600 с) Cleanup сканирует PostgreSQL на сессии в состоянии CLOSED (11) или DELETED (9), у которых `closedAt < now() - X дней`. Такие записи удаляются из БД, связанные Redis-ключи — очищаются, данные в ClickHouse — архивируются/удаляются.
**В тесте:**

*   `Cleanup.intervalMs` временно = 10 с _(уточнить механизм)_

*   Порог удаления: X = 1 день _(уточнить: из конфигурации)_

*   Создаём «старую» сессию вручную (записываем в PG с closedAt = now() - 2 дня)

*   Ждём cleanup → проверяем, что запись удалена


**Предусловие:**

*   `Cleanup.intervalMs` = 10 с _(временно)_

*   В PostgreSQL: **нет** сессий со status = 11 (CLOSED)

*   В Redis: **нет** ключей `session:*`


**Действия:**

1.  `pg.query("INSERT INTO sessions (id, status, closed_at, processing_mode, created_at) VALUES ('old-test-001', 11, now() - INTERVAL '2 days', 0, now() - INTERVAL '3 days')")` _Создаём «старую» сессию: CLOSED, закрыта 2 дня назад. Это имитация сессии, которая была закрыта давно и должна быть убрана cleanup._

2.  `pg.query("INSERT INTO sessions (id, status, closed_at, processing_mode, created_at) VALUES ('new-test-002', 11, now() - INTERVAL '1 hour', 0, now() - INTERVAL '1 day')")` _Создаём «новую» сессию: CLOSED, закрыта 1 час назад. Она_ **_не должна_** _быть удалена (ещё не достигла порога X дней)._

3.  `redis.set("session:old-test-001:status", "11")` _Создаём Redis-ключ для «старой» сессии. Cleanup должен удалить его вместе с записью в PG._

4.  `redis.set("session:new-test-002:status", "11")` _Redis-ключ для «новой» сессии. Должен_ **_остаться_**_._

5.  `WAIT(20)` — 10 с interval + 10 с margin _Ждём, пока Cleanup запустится (интервал 10 с) и обработает сессии. 20 с — запас._

6.  `pg.query("SELECT id FROM sessions WHERE id = 'old-test-001'")` _Проверяем: запись_ **_удалена_** _(0 строк). Cleanup убрал старую сессию._

7.  `pg.query("SELECT id FROM sessions WHERE id = 'new-test-002'")` _Проверяем: запись_ **_осталась_** _(1 строка). Cleanup не тронул новую сессию._

8.  `redis.get("session:old-test-001:status")` _Проверяем: Redis-ключ_ **_удалён_** _(null). Cleanup очистил кэш._

9.  `redis.get("session:new-test-002:status")` _Проверяем: Redis-ключ_ **_остался_** _(= "11"). Новая сессия не тронута._

10.  `redis.keys("session:*")` _Общий список: должен содержать только_ `session:new-test-002:*`_. Ключи_ `old-test-001` _— отсутствуют._


**Ожидаемый результат:**
| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 6 | 0 строк (удалена) | Старая сессия убрана |
| 7 | 1 строка (осталась) | Новая сессия не тронута |
| 8 | null (удалён) | Redis-ключ старой сессии убран |
| 9 | "11" (остался) | Redis-ключ новой сессии на месте |
| 10 | Только `new-test-002` | Общий чистый результат |

**Примечание:**

*   Механизм изменения `Cleanup.intervalMs`: **уточнить** (Redis / config / env / actuator)

*   Если cleanup не удаляет Redis-ключи (только PG) — это допустимо (Redis-ключи и так истекают по TTL = 24 ч). Но желательно: cleanup удаляет и Redis.

*   Если cleanup архивирует (не удаляет, а переносит в `sessions_archive`) — проверяем архивную таблицу.


**Teardown:** `pg.query("DELETE FROM sessions WHERE id IN ('old-test-001','new-test-002')")` → `redis.del("session:new-test-002:status")` → `RESET()` (с возвратом interval к 3600 с)


### 3.9 Сохранение и воспроизведение сессии (save / play-model)

* * *

#### HY-HIST-045 — Сохранение сессии: PLAYING → SAVING → SAVED

**Требование:** R-HYDR-073
**Описание:** Оператор сохраняет текущую сессию (PLAYING) для последующего воспроизведения (play-model). Система: останавливает обработку, сохраняет текущие значения всех тегов + watermark + параметры в ClickHouse (или Blob), меняет статус PLAYING(3) → SAVING(4) → SAVED(5). После сохранения сессию можно запустить заново через `play-model` — она «проиграет» сохранённое состояние.
**Что сохраняется:**

*   Текущий watermark (до какого момента обработано)

*   Значения всех тегов на момент сохранения (snapshot)

*   Параметры сессии (processingMode, targets, speedRatio, startTime, targetTime)

*   Алармы, сработавшие до момента сохранения

*   Метаданные (sessionId, createdAt, startedAt)


**Предусловие:**

*   Сессия historical запущена (status = 3, PLAYING)

*   `watermark = "2026-11-09T09:30:00Z"` (обработано 90 мин из 240)

*   В `model_main_{id}` есть расчётные данные (Head, PressDelta, QVmomDelta)

*   Конфигурация ТУ1 загружена


**Действия:**

1.  `ws.subscribe(id)` _Подписываемся. Будем ловить SESSION_SAVING (type=15) и SESSION_SAVED (type=14)._

2.  `api.get(id)` ⚠️ _Зафиксировать исходное состояние: status=3, watermark=09:30:00. Это «нулевая точка» для проверки: после save все эти значения должны сохраниться._

3.  `api.save(id)` ⚠️ _Отправляем команду сохранения. Система: (а) меняет статус 3→4 (SAVING), (б) публикует SESSION_SAVING в WS, (в) останавливает WorkerExecutor (перестаёт публиковать в Kafka), (г) сохраняет snapshot значений в CH/Blob, (д) по завершении: 4→5 (SAVED), публикует SESSION_SAVED._

4.  `ws.wait_event(id, 15, timeout=10)` — SESSION_SAVING (type=15) _Событие: сохранение начато. Если не пришло за 10 с — команда не обработана (баг в SaveSessionController)._

5.  `api.get(id)` ⚠️ _Проверяем промежуточное:_ `status = 4` _(SAVING). Сессия «зависла» в процессе сохранения — это нормальное промежуточное состояние._

6.  `WAIT(15)` _Время на: сохранение snapshot в CH (может быть 5–30 с в зависимости от объёма данных). Для 90 мин × ~10 тегов = ~54 000 значений — записываем в CH._

7.  `ws.wait_event(id, 14, timeout=30)` — SESSION_SAVED (type=14) _Событие: сохранение завершено. В_ `data` _может быть:_ `savedAt`_,_ `dataSize`_,_ `targetCount`_._

8.  `api.get(id)` ⚠️ _Проверяем:_ `status = 5` _(SAVED)._ `savedAt` _заполнено._ `watermark` _= 09:30:00 (сохранён на момент save)._

9.  `redis.get("session:" + id + ":status")` _Кросс-проверка: Redis = 5 (SAVED). Согласуется с PG._

10.  `pg.query("SELECT status, saved_at, watermark FROM sessions WHERE id = '<id>'")` _Кросс-проверка в БД: status=5, saved_at заполнено, watermark = 09:30:00._

11.  `ch.query("SELECT count(*) FROM saved_session_data WHERE session_id = '<id>'")` _(или аналогичная таблица/таблица)_ _Проверяем, что данные реально записаны в ClickHouse. Ожидаем: > 0 (сохранены значения тегов)._

12.  `api.start(id)` ⚠️ _Попытка запустить SAVED-сессию через обычный_ `start`_. Ожидаем: 409 или 400. SAVED-сессия запускается только через_ `play-model` _(шаг 13)._

13.  `api.playModel(id)` ⚠️ _Запускаем воспроизведение сохранённой сессии. Ожидаем: система читает сохранённые данные и «проигрывает» их. Статус: 5→1 (OPENING)→3 (PLAYING)._

14.  `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED (type=1) _Событие: сессия открыта для воспроизведения._

15.  `api.watermark(id)` ⚠️ _Проверяем: watermark = 09:30:00 (начинается с сохранённого значения, не с startTime=08:00)._

16.  `WAIT(10)` — 10 с × 10× = 100 с виртуального _Даём время на обработку. Watermark должен двигаться от 09:30._

17.  `api.watermark(id)` ⚠️ → `wm_play` _Проверяем:_ `wm_play > "2026-11-09T09:30:00Z"`_. Воспроизведение идёт._


**Ожидаемый результат:**
| Шаг | Ожидание | Для локализации |
| --- | --- | --- |
| 4 | `type=15` (SAVING) | Если нет → SaveSessionController не обработал |
| 5 | `status = 4` (SAVING) | Промежуточное подтверждено |
| 7 | `type=14` (SAVED) | Если нет → сохранение зависло (проверить CH) |
| 8 | `status = 5`, `savedAt` заполнено | Основной критерий |
| 11 | CH: > 0 записей | Если 0 → данные не записаны (баг в ValueSaver) |
| 12 | HTTP 409/400 | Если 200 → SAVED запускается через start (допустимо, но не рекомендуется) |
| 15 | `watermark = 09:30:00` | Если = 08:00 → play-model начал с начала (не с сохранённого) |
| 17 | `wm_play > 09:30:00` | Если не двигается → воспроизведение не работает |

**Примечание:**

*   Если `play-model` не существует как отдельный endpoint (псевдо) — возможно, воспроизведение = `api.start(id)` ⚠️ для SAVED-сессии. В этом случае шаг 12 и 13 объединяются.

*   Таблица/структура в CH для сохранённых данных: **уточнить** по реализации (ValueSaver).


**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

* * *

#### HY-HIST-046 — Отмена сохранения: SAVING → CANCELLING → CANCELLED

**Требование:** R-HYDR-073
**Описание:** Во время сохранения (SAVING) оператор меняет мнение и отменяет. Система: прерывает запись в CH, меняет статус SAVING(4) → CANCELLING → CANCELLED. Сессия возвращается в предыдущее состояние (PLAYING) или остаётся в промежуточном.
**Предусловие:**

*   Сессия historical запущена (status = 3, PLAYING)

*   `watermark = "2026-11-09T10:00:00Z"` (большой объём данных для сохранения)


**Действия:**

1.  `ws.subscribe(id)` _Подписываемся._

2.  `api.save(id)` ⚠️ _Начинаем сохранение. Статус: 3→4 (SAVING). Начинается запись в CH._

3.  `ws.wait_event(id, 15, timeout=10)` — SESSION_SAVING _Подтверждаем: сохранение началось._

4.  `WAIT(3)` _Ждём 3 с — сохранение идёт (данные пишутся в CH). Достаточно времени, чтобы часть данных уже была записана, но не всё._

5.  `api.get(id)` ⚠️ _Проверяем:_ `status = 4` _(SAVING). Сохранение в процессе._

6.  Отмена сохранения: `POST /v2/mod-hist/sessions/{id}/save/cancel` ⚠️ _(псевдо — точный endpoint уточнить)_ _Отправляем отмену. Система: (а) прерывает запись в CH, (б) удаляет частично записанные данные (или помечает как невалидные), (в) меняет статус 4→CANCELLED (или 4→3, если CANCELLING — промежуточное)._

7.  `WAIT(5)` _Время на: завершение отмены, очистку CH._

8.  `api.get(id)` ⚠️ _Проверяем финальный статус. Допустимые варианты: (а)_ `status = 3` _(PLAYING) — сессия вернулась в работу, (б)_ `status = 5` _(SAVED) с флагом_ `cancelled = true` _— сохранение отменено, но сессия в SAVED._

9.  `ch.query("SELECT count(*) FROM saved_session_data WHERE session_id = '<id>'")` _Проверяем: частично записанные данные_ **_удалены_** _или_ **_помечены как невалидные_**_. Ожидаем: 0 записей (или все с флагом_ `valid = false`_)._

10.  `api.watermark(id)` ⚠️ _Проверяем: watermark не сбросился. Должен быть ≈ 10:00 (или чуть больше, если сессия вернулась в PLAYING)._


**Ожидаемый результат:**
| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 8 | `status = 3` (PLAYING) **ИЛИ** `status = 5` (SAVED, cancelled) | Сессия не «зависла» в SAVING |
| 9 | 0 записей в CH (или все invalid) | Частичные данные не остались |
| 10 | `watermark ≈ 10:00` | Watermark не сломан |

**Примечание:**

*   Если отмена сохранения не реализована (нет endpoint) — сценарий помечается как «не применимо». В этом случае единственный путь — дождаться завершения сохранения.

*   Если CANCELLING (3 по SaveSessionStatus) — это промежуточное: между SAVING и CANCELLED. Проверяем, что система не «зависает» в CANCELLING.


**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

* * *

### 3.10 Режим timeshift (сдвиг времени контроля)

* * *

#### HY-HIST-047 — timeshift: базовый сценарий (sourceMode = saved)

**Требование:** R-HYDR-069
**Описание:** Оператор создаёт timeshift-сессию на основе сохранённой сессии (sourceMode = saved). Смысл: «что было бы, если бы контроль начался на 2 часа раньше?» Система берёт сохранённые данные исходной сессии, сдвигает время на `shiftDuration`, и пересчитывает hydro-calculation по сдвинутым данным.
**Параметры timeshift:**

*   `sourceMode = 0` (saved) — источник: сохранённая сессия

*   `sourceSessionId` — ID исходной сессии (SAVED)

*   `startTime` — начало расчётного периода

*   `shiftDuration` — величина сдвига (в секундах, может быть отрицательной)

*   `targets` — теги для расчёта


**Предусловие:**

*   Существует сохранённая сессия (SAVED, status=5): `sourceSessionId = "abc-123"`
    *   Период: 14:00–16:00, speedRatio = 1000

    *   В сохранённых данных: Press, Ro, QVmom за 14:00–16:00

*   Конфигурация ТУ1 загружена

*   `[LU].State.Control = 1` (контроль активен в исходной сессии)


**Действия:**

1.  `api.createTimeshift({"sourceMode":0, "sourceSessionId":"abc-123", "startTime":"2026-11-09T15:00:00Z", "shiftDuration":-3600, "targets":["MT1.LU1"]})` _Создаём timeshift: (а) источник — saved-сессия "abc-123", (б) startTime = 15:00, (в) shift = -3600 с (на 1 час назад). Итог: система возьмёт данные из исходной сессии за 14:00–15:00 (сдвинутые на -1 ч от 15:00) и пересчитает._

2.  `api.start(id)` ⚠️ _Запускаем. Система: (а) загружает данные из saved-сессии "abc-123" за период 14:00–15:00, (б) публикует в_ `model_main_{id}` _с виртуальным ts (сдвинутым), (в) hydro-calculation пересчитывает._

3.  `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED _Подтверждаем: сессия запущена._

4.  `WAIT(70)` — 70 с × 1× = 70 с виртуального > 3600 с / 60 = 60 мин? Нет. _Корректировка: при speedRatio = 1000 (1×) и диапазоне 14:00–15:00 (3600 с) — реальное время = 3600 с = 60 мин. Для ускорения теста используем speedRatio = 10000 (10×): 3600/10 = 360 с = 6 мин. Пересоздаём с speedRatio = 10000._
    **Корректировка:** `api.createTimeshift({...,"speedRatio":10000})` → реальное время ≈ 6 мин. Ждём `WAIT(400)` (400 с > 360 с).

5.  `ws.wait_event(id, 9, timeout=420)` — WATERMARK_COMPLETE _Сессия завершена (timeshift — как historical: авто-complete по targetTime)._

6.  `api.get(id)` ⚠️ _Проверяем:_ `status = 8` _(DONE)._ `processingMode = 2` _(timeshift)._ `sourceMode = 0` _(saved)._

7.  `api.watermark(id)` ⚠️ _Проверяем: watermark = targetTime (15:00). Сессия обработана полностью._

8.  `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️ _Проверяем: напор рассчитан. Значение_ **_отличается_** _от исходной сессии (потому что контроль «начался» на 1 час раньше — другие граничные условия, другие данные)._

9.  `kafka.consume("model_main_" + id, timeout=10)` _Проверяем: в Kafka есть сообщения. Их ts —_ **_сдвинутые_** _(14:00–15:00, а не 15:00–16:00). Подтверждаем, что сдвиг применён._

10.  `ch.query("SELECT tag, ts, value FROM saved_session_data WHERE session_id = 'abc-123' AND ts BETWEEN '2026-11-09T14:00:00Z' AND '2026-11-09T15:00:00Z' LIMIT 5")` _Сравниваем: данные в timeshift-сессии (шаг 9) совпадают с данными исходной сессии (шаг 10) за соответствующий период. Это подтверждает, что данные взяты из saved-сессии, а не «придуманы»._


**Ожидаемый результат:**
| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 5 | WATERMARK_COMPLETE | Timeshift завершён автоматически |
| 6 | `status = 8` (DONE), `processingMode = 2` | Корректный режим |
| 7 | `watermark = 15:00:00` | Полная обработка |
| 8 | Head рассчитан, ≠ исходному | Сдвиг повлиял на расчёт |
| 9 | ts в Kafka: 14:00–15:00 | Сдвиг применён к таймстампам |
| 10 | Данные совпадают с saved-сессией | Источник подтверждён |

**Примечание:**

*   `shiftDuration = -3600` (отрицательный) — сдвиг **назад**. Положительный сдвиг (+3600) — вперёд. Оба допустимы.

*   Если `sourceSessionId` не существует или не в SAVED-статусе — ожидаем 400/404.

*   Timeshift **не** создаёт новые данные — он берёт существующие (saved/imported) и пересчитывает hydro-calculation с другими граничными условиями.


**Teardown:** `api.close(id)` ⚠️ → `RESET()`

* * *

#### HY-HIST-048 — timeshift: sourceMode = imported

**Требование:** R-HYDR-069
**Описание:** Timeshift на основе импортированных данных (sourceMode = imported). Вместо saved-сессии — данные из XLSX/ZIP_CSV. Сценарий: оператор имеет исторические данные в файле, загружает их, и делает timeshift.
**Предусловие:**

*   Файл импорта готов: `timeshift_data.xlsx` (Press, Ro, QVmom за 10:00–12:00)

*   Конфигурация ТУ1 загружена


**Действия:**

1.  `api.createModelling({"targets":["MT1.LU1"]})` _Создаём вспомогательную modelling-сессию для импорта._

2.  `api.import_(id, file=timeshift_data.xlsx)` ⚠️ _Импортируем данные. Статус → IMPORTED (7)._

3.  `api.close(id)` ⚠️ _Закрываем вспомогательную сессию. Данные импорта остаются доступные (в Redis/CH) для timeshift._

4.  `api.createTimeshift({"sourceMode":1, "sourceSessionId":"<id_импорта>", "startTime":"2026-11-09T11:00:00Z", "shiftDuration":1800, "speedRatio":10000, "targets":["MT1.LU1"]})` _Создаём timeshift: источник — imported (1), сдвиг +1800 с (30 мин вперёд). startTime = 11:00 → расчётный период: 10:30–11:30 (сдвинутый на -30 мин от 11:00... нет: 11:00 + 1800 = 11:30, источник: 10:00–12:00 из импорта)._

5.  `api.start(id2)` ⚠️

6.  `ws.wait_event(id2, 1, timeout=30)`

7.  `WAIT(200)` — 200 с × 10× = 2000 с > 7200 с / 10? Нет. Корректировка: диапазон 10:30–11:30 = 3600 с. 3600/10 = 360 с. Ждём 400 с.

8.  `ws.wait_event(id2, 9, timeout=420)` — WATERMARK_COMPLETE

9.  `api.get(id2)` ⚠️ `status = 8` _(DONE),_ `sourceMode = 1` _(imported)._


**Ожидаемый результат:**
| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 8 | WATERMARK_COMPLETE | Timeshift завершён |
| 9 | `status = 8`, `sourceMode = 1` | Корректный источник |

**Примечание:** Если `sourceSessionId` для imported — это ID сессии, в которую был сделан импорт. Если импорт привязан к глобальному буферу (не к сессии) — `sourceSessionId` может быть опциональным. **Уточнить по реализации.**
**Teardown:** `api.close(id2)` ⚠️ → `RESET()`

* * *

#### HY-HIST-049 — timeshift: невалидный sourceSessionId

**Требование:** R-HYDR-069
**Описание:** Оператор указывает `sourceSessionId`, который не существует или не в SAVED/IMPORTED-статусе. Система отклоняет с ошибкой.
**Предусловие:**

*   Сессия `non-existent-id` не существует

*   Сессия `playing-id` в статусе PLAYING (3)


**Действия:**

1.  `api.createTimeshift({"sourceMode":0, "sourceSessionId":"non-existent-id", "startTime":"2026-11-09T15:00:00Z", "shiftDuration":-3600, "targets":["MT1.LU1"]})` _Не существующая сессия. Ожидаем: 400 или 404._

2.  `api.createTimeshift({"sourceMode":0, "sourceSessionId":"playing-id", "startTime":"2026-11-09T15:00:00Z", "shiftDuration":-3600, "targets":["MT1.LU1"]})` _Сессия в PLAYING (не SAVED). Ожидаем: 400 («источник должен быть SAVED или IMPORTED»)._

3.  `api.list({})` ⚠️ _Проверяем: сессии не созданы. Ошибка на этапе валидации._


**Ожидаемый результат:**
| Шаг | Ожидание | Пояснение |
| --- | --- | --- |
| 1 | HTTP 404 или 400 | Источник не найден |
| 2 | HTTP 400 | Источник не в SAVED/IMPORTED |
| 3 | Пустой массив | Ничего не создано |

**Teardown:** `RESET()`



## 4. Правила исполнения

1.  **Изоляция:** Каждый тест стартует с начального состояния (2.3). Teardown обязателен. После каждого теста: `api.list({})` ⚠️ → пустой массив, `redis.keys("session:*")` → пусто.

2.  **Ожидание:** `WAIT(n)` с запасом 5 с. Для WS: `ws.wait_event(id, type, timeout)` с timeout = ожидаемое время + 10 с. Для Kafka: timeout = max(interval, 30) с.

3.  **Множественная проверка:** Каждый критичный результат проверяется **минимум из 2 источников**:
    *   REST (`api.get`) + WebSocket (событие)

    *   REST + Redis

    *   REST + PostgreSQL

    *   Kafka (`kafka.consume`) + Redis/REST Это позволяет локализовать проблему: если REST говорит «PLAYING», а Redis — «PAUSED» → баг в кэше.

4.  **Промежуточные состояния:** Для сценариев с длинным каскадом (create → opening → playing) — проверяем **каждое** промежуточное состояние:
    *   Kafka: команда опубликована? (`kafka.consume("mod-hist-commands", ...)`)

    *   Kafka: результат получен? (`kafka.consume("mod-hist-results", ...)`)

    *   Redis: статус обновлён? (`redis.get("session:{id}:status")`)

    *   PG: запись существует? (`pg.query(...)`)

    *   WS: событие пришло? (`ws.wait_event(...)`)

5.  **Граничные значения:** При проверке границ (speedRatio, bufferSize, maxSessions) — всегда 3 точки: ровно на границе (допустимо), за границей на 1 (недопустимо), за границей значительно (недопустимо).

6.  **Исправление:** При сбое — фиксировать **фактический** результат, не исправлять ожидаемый. Различия документировать в отчёте с указанием: какой шаг, какой источник (REST/WS/Kafka/Redis/PG), какое значение ожидалось vs полученное.

7.  **Номер сценария:** В отчёте: `HY-HIST-xxx`.

8.  **Идемпотентность:** Повторный запуск того же сценария — тот же результат (нет зависимости от порядка, от «грязного» состояния).

9.  **Время:** Для тестов с длительным ожиданием (> 2 мин) — использовать сокращённые параметры. Помечать: «Для ускорения: X временно = Y (механизм: ...)».

10.  **Локализация:** В каждом сценарии, где результат может быть неоднозначным, указывать: «Если X — значит баг в Y». Это позволяет tester'у быстро определить, где копать.


* * *



## 5. Чек-лист подготовки стенда (продолжение)

| # | Проверка | Как | Ожидаемый результат |
| --- | --- | --- | --- |
| 1 | mod-hist развёрнут, UP | `GET /actuator/health` | `{"status":"UP"}` |
| 2 | hydro-calculation развёрнут, UP | Health check hydro-calc (порт уточнить) | `{"status":"UP"}` |
| 3 | Kafka: топики существуют | `kafka-topics --list --bootstrap-server kafka:9092` | `cspa-main`, `mod-hist-commands`, `mod-hist-results` в списке |
| 4 | PostgreSQL: таблицы существуют | `pg.query("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('sessions','session_results')")` | 2 строки |
| 5 | Redis: доступен, ключи отсутствуют | `redis.keys("session:*")` | Пустой массив |
| 6 | ClickHouse: тестовая история загружена | `ch.query("SELECT count(*) FROM history WHERE tag LIKE 'MT1.LU1.%' AND ts >= now() - INTERVAL 24 HOUR")` | ≥ 10 000 |
| 7а | hmi-backend: health | `GET http://hmi-backend:8080/actuator/health` | `{"status":"UP"}` |
| 7b | hmi-backend: прогревание завершено (бизнес-эндпоинты доступны) | `GET http://hmi-backend:8080/diag/instance` | HTTP 200, тело = `evo-manager.app-id` (не 503) |
| 7c | hmi-backend: WS V2 доступен | WS-подключение к `ws://hmi-backend:8080/v2/hotlink`, отправить `{"cmd":"PING","id":"test"}` | Получен `PONG` с `id:"test"` в течение 5 с |
| 7d | hmi-backend: доступ к тестовым тегам | `GET http://hmi-backend:8080/v2/tag-get?tagName=MT1.LU1.SGLU1.KIP1.TI.Press` + заголовок `X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]` | HTTP 200, тело содержит `"tag"` и `"data"` |
| 8 | Конфигурация ТУ1 загружена в data-manager | `pg.query("SELECT count(*) FROM tu_config WHERE lu_id = 'MT1.LU1'")` или `redis.get("tu:MT1.LU1:config")` | ≠ 0 / ≠ null |
| 9 | Файлы импорта готовы (XLSX, ZIP_CSV) | Файлы в рабочей директории автотестов | `import_test.xlsx`, `import_test.zip` существуют |
| 10 | Начальное состояние подтверждено | `api.list({})` ⚠️ + `GET /actuator/health` | Пустой массив + UP |
| 11 | Kafka ACL настроен (mod-hist может писать в model_main_*) | `kafka.acls --list --topic model_main_* --authorization-principal-user mod-hist` | Allow для produce/consume |
| 12 | Hydro-calc подписан на mod-hist-commands | `kafka-consumer-groups --describe --group hydro-calc-*` | Group существует, lag = 0 |
| 13 | Для cleanup-теста: возможность менять Cleanup.intervalMs | Уточнить: Redis key / config / env / actuator | Механизм задокументирован |
| 14 | Для TTL-теста: возможность менять sessionTTL | Уточнить: Redis key / config / env | Механизм задокументирован |
| 15 | Для buffer overflow: возможность менять bufferSize | Уточнить: Redis key / config / env | Механизм задокументирован |

* * *

## 6. Допущения

| # | Допущение | Статус | Примечание |
| --- | --- | --- | --- |
| 1 | Endpoint `api.start` ⚠️ для CREATED-сессии: `POST /v2/mod-hist/sessions/{id}/start` | **Псевдо** | Реальный механизм запуска уточняется. Возможно: `play-model` для saved, отдельный endpoint для новых |
| 2 | Endpoint `api.stop` ⚠️: `POST /v2/mod-hist/sessions/{id}/stop` | **Псевдо** |  |
| 3 | Endpoint `api.pause` ⚠️ / `api.resume` ⚠️ | **Псевдо** |  |
| 4 | Endpoint `api.close` ⚠️: `DELETE /v2/mod-hist/sessions/{id}` | **Псевдо** |  |
| 5 | Endpoint `api.advance` ⚠️: `POST /v2/mod-hist/sessions/{id}/advance` | **Псевдо** | Возможно: WS-команда или часть player-controller |
| 6 | Endpoint `api.setSpeed` ⚠️: `PUT /v2/mod-hist/sessions/{id}/speed` | **Псевдо** | Возможно: WS-команда (PlayerMode = SetSpeed) |
| 7 | Endpoint `api.retry` ⚠️: `POST /v2/mod-hist/sessions/{id}/retry` | **Псевдо** | Возможно: повторный `start` для ERROR-сессии |
| 8 | Повторный `api.start` для PLAYING-сессии возвращает HTTP 200 (не 409) | **Допущение** | Требует верификации |
| 9 | При отсутствии данных в CH сессия переходит в ERROR (12), не DONE (8) | **Допущение** | Требует верификации |
| 10 | `advance(-60)` отклоняется с 400 | **Допущение** | Требует верификации |
| 11 | WS не буферизует события при отключении клиента | **Допущение** | Проверяется в HY-HIST-042 |
| 12 | При закрытии сессии Redis-ключи удаляются (не помечаются) | **Допущение** | Альтернатива: ключ остаётся со status=11 до TTL (24 ч) |
| 13 | Экспорт пустого диапазона возвращает 200 с пустым CSV | **Допущение** | Альтернатива: 404 |
| 14 | Поле `dataGaps` в ответе `api.get` при частичных данных | **Допущение** | Может не существовать |
| 15 | `closeReason = "TTL_EXCEEDED"` — формат поля | **Допущение** | Может быть enum, код, или отсутствовать |
| 16 | Cleanup удаляет сессии старше 1 дня (X = 1) | **Допущение** | Точное значение из конфигурации |
| 17 | `hmi.set` (`POST /v2/tag-set`) публикует значение в Kafka **hot topics** (конфигурируются через `CSPA_TOPICS` / `TopicRouteConfig`). Для mod-hist hot topic должен совпадать с `model_main_{sessionId}` (или mod-hist читает из того же потока) | Подтверждено документацией | Механизм привязки `model_main_{sessionId}` к hot topic hmi-backend: **уточнить** (env `CSPA_TOPICS` / `TopicRouteConfig` / отдельная конфигурация mod-hist). hmi-backend сам не знает о `model_main_*` |
| 18 | `hmi.get` (`GET /v2/tag-get`) читает текущее значение из **DataStream** (Kafka consumer → `TagValueStreamHandler` → буфер). Кэш метаданных тегов — `TagInfoService` (TTL **5 с**). Значение берётся из последнего полученного по Kafka-топику | **Допущение** | hmi-backend не читает напрямую из Redis для значений тегов. Redis используется для кэша ИМ/метаданных |
| 19 | При `POST /v2/tag-set` hmi-backend **валидирует тип** значения против типа тега (`ProtoValidator.validate()`). Несоответствие → HTTP 400 + `ValueConversionException` | **Подтверждено документацией** | В автотестах: при записи `value: "abc"` в тег типа DOUBLE — ожидаем 400 |
| 20 | До завершения **AppWarmUp** (`HmiEvoService.isReady() = true`) все бизнес-REST-эндпоинты hmi-backend возвращают **503** (`ServerReadyRestInterceptor`). Разрешены: `/actuator/*`, `/health*`, `/diag/*` | **Подтверждено документацией** | В чек-листе: после `actuator/health = UP` дождаться `diag/instance = 200` |
| 21 | WS V2 hmi-backend агрегирует подписки в окне **50 мс** (`tn-scada.hmi.sample-time`). При высокой частоте обновлений значения приходят пакетом | **Подтверждено документацией** | В автотестах: после `TAG_SET` ожидание `SUB_ANSWER` — до 100 мс (запас) |
| 22 | WS V2 hmi-backend: `Minuteman` каждые **30 с** закрывает неактивные сессии (`clientside-stale-time-s`, default **3600 с**), будит при `clientside-wake-time-s` (default **30 с**) | **Подтверждено документацией** | Для автотестов: WS-соединение без PING > 30 с → hmi-backend может разбудить/закрыть. Рекомендация: отправлять `PING` каждые 10–20 с в длительных сценариях |
| 23 | Событие SESSION_OPENED (type=1) приходит при переходе OPENING→PLAYING | **Допущение** | Может приходить при CREATED→OPENING |
| 24 | Watermark при запуске historical = startTime (не null) | **Допущение** | Может быть null до первого сообщения |
| 25 | timeshift использует `sourceMode` (saved/imported/history) для выбора источника | **Допущение** | Из Блока A, не подтверждено сценариями |
| 26 | Сессия SAVED может быть запущена только через `play-model` (не `start`) | **Допущение** | Из Блока B (PlayModelController) |

* * *
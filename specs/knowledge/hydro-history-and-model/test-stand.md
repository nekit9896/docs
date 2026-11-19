---
id: KB-HM-TESTSTAND-001
title: Тестовый стенд hydro-history-and-model: компоненты, топики Kafka, константы, начальное состояние, cleanup
service: hydro-history-and-model
group: test-plan
source: confluence/test-plan-hydro-history-and-model.md#2.ТЕСТОВЫЙ.СТЕНД, #1.3, #1.4
requires: []
related: [KB-HM-TESTPLAN-001, KB-HM-STORAGE-001, KB-HM-SESSIONS-001, KB-HM-WATERMARK-001, KB-CALC-FORMULA-001, KB-HMI-WS-001]
status: verified
---

# Тестовый стенд hydro-history-and-model (тест-план HY-HIST, §2, §1.3–1.4)

Факты — из `confluence/test-plan-hydro-history-and-model.md`. Обозначения,
правила, enum-коды и допущения — KB-HM-TESTPLAN-001. Описание самого сервиса
(§1.0–1.2, §1.5–1.7 тест-плана) дублирует repo_description (KB-HM-OVERVIEW-001,
KB-HM-SESSIONS-001 и др.) и сознательно не переносится; уникальное — здесь и в
KB-HM-TESTPLAN-001.

## Компоненты стенда (§2.1)

| Компонент | Роль | Примечание |
|---|---|---|
| **mod-hist** | Тестируемый сервис | Java Spring Boot |
| **hydro-calculation** | Расчётный сервис | Java Spring Boot |
| **hmi-backend** | Операторский API + WS | REST **8080**; WS V2 `ws://hmi-backend:8080/v2/hotlink`; WS V1 `ws://hmi-backend:8080/hotlink` |
| **Kafka** | Брокер | 9092 |
| **PostgreSQL** | Сессии, ИМ | 5432 |
| **Redis** | Кэш, watermark, буферы | 6379 |
| **ClickHouse** | История, экспорт | 8123 |

## Топики Kafka (§2.2)

| Топик | Назначение | Формат |
|---|---|---|
| `cspa-main` | Оперативный поток (вход + выход) | `{tag, ts, value, invalid}` |
| `model_main_{sessionId}` | Виртуальный поток (historical/modelling/timeshift) | `{tag, ts, value, invalid}` |
| `model_alarm_{sessionId}` | Алармы сессии | `{tag, ts, value, text, priority, state}` |
| `mod-hist-commands` | Команды → hydro-calc | `{sessionId, command, params, ts}` |
| `mod-hist-results` | Результаты → mod-hist | `{sessionId, tag, value, ts}` |

Команды mod-hist → hydro-calc: `START`, `STOP`, `CLOSE`, `SET_WATERMARK`,
`PAUSE`, `RESUME`. Данные сессии идут по **отдельному** топику
`model_main_{sessionId}` (не смешиваются с оперативным `cspa-main`);
таймстампы виртуальные (≠ реальное время); hydro-calculation не знает, что это
«модель», — просто читает топик.

## Константы и числовые значения (§1.3)

| Константа | Значение | Конфиг | Описание |
|---|---|---|---|
| Таймаут подтверждения от hydro-calculation | 30 с | `SessionWorker.confirmTimeoutMs` | Нет ответа → ERROR |
| Интервал проверки watermark | 5 с | `Watermark.checkIntervalMs` | Периодичность обновления |
| Максимум сессий одновременно | 10 | `SessionWorker.maxSessions` | Ограничение активных сессий |
| Буфер данных | 10 000 сообщений | `WorkerExecutor.bufferSize` | Кольцевой (FIFO) |
| TTL сессии в Redis | 24 часа | `SessionWorker.sessionTTL` | Автозакрытие неактивных |
| Максимальная скорость | 60× (60000) | `FastMode.maxSpeedFactor` | Максимум speedRatio |
| Минимальная скорость | 0.25× (250) | `FastMode.minSpeedFactor` | Минимум speedRatio |
| Интервал записи в CH | 60 с | `DataExchange.exportInterval` | Экспорт результатов |
| Размер страницы (пагинация CH) | 1000 | `DataExchange.pageSize` | Записей за запрос |
| Таймаут WebSocket | 60 с | `WsConfig.timeout` | Без ping → закрытие |
| Максимальный размер импорта | 50 МБ | `DataExchange.maxImportSize` | Ограничение файла |
| Интервал cleanup | 3600 с | `Cleanup.intervalMs` | Проверка устаревших сессий |
| Порог отставания watermark | 120 с | `Watermark.lagThreshold` | Предупреждение о lag |

Допустимые значения speedRatio (UI): 0.25× = 250, 0.5× = 500, 1× = 1000,
2× = 2000, 5× = 5000, 10× = 10000, 60× = 60000.

## Ключевые понятия и формулы (§1.4)

**Watermark** — отметка времени (timestamp, ms), до которой обработаны данные:

```text
Watermark = max(время последнего обработанного сообщения)
TargetWatermark = targetTime (для historical) / ∞ (для modelling)
Lag = TargetWatermark − Watermark
Progress% = ((Watermark − StartTime) / (TargetTime − StartTime)) × 100
```

**Скорость обработки (historical):**

```text
speedRatio: int, где 1000 = ×1 (реальное время)
Виртуальный шаг = 1000000 / speedRatio мс
Пример: speedRatio = 2000 (2×) → шаг 500 мс
Пример: speedRatio = 60000 (60×) → шаг ≈ 16.7 мс
```

**ETA (оценка времени до завершения):**

```text
ETA (с) = (TargetTime − Watermark) / (speedRatio / 1000)
Пример: target 08:10, wm 08:05, speedRatio 10000 (10×) → ETA = 30 с
```

**Буфер:**

```text
BufferCapacity = 10 000
BufferIndex = (BufferIndex + 1) % BufferCapacity
При переполнении: старые сообщения теряются (FIFO)
Аларм BUFFER_OVERFLOW: потеряно > 10% буфера за цикл
```

Формула напора `h = (P / ρ) × 101970 + H` живёт в KB-CALC-FORMULA-001 (единый
источник). В §1.4 тест-плана единицы P указаны как «кгс/см²» — расхождение с
KB-CALC-FORMULA-001 (МПа), см. G19 в `meta/discrepancies-2026-11-17.md`.

## Начальное состояние стенда (§2.3)

- mod-hist, hydro-calculation, hmi-backend — UP, **прогревание завершено**
  (`HmiEvoService.isReady() = true`). Проверка: `GET /actuator/health` →
  `{"status":"UP"}`. До завершения AppWarmUp бизнес-эндпоинты возвращают **503**
  (`ServerReadyRestInterceptor`); допустимы `/actuator/*`, `/health*`.
- Kafka: топики существуют.
- PostgreSQL: таблицы `sessions`, `session_results` — пусты.
- Redis: `session:*` отсутствуют.
- ClickHouse: тестовая история ≥ 24 ч для MT1.LU1 (≥ 10 000 сообщений).
- Конфигурация ТУ1 загружена в data-manager.
- `api.list()` → пустой массив.
- `LU.State.Control = 0`, все `Disable = false`.

## Cleanup после каждого кейса (§2.4)

1. Все активные сессии → `api.stop` → `api.close`.
2. Redis: `session:{id}:*` удалены.
3. PostgreSQL: записи удалены или помечены CLOSED/DELETED.
4. Kafka: consumer groups удалены.
5. ClickHouse: тестовые данные удалены.
6. hydro-calculation: буферы очищены (CLOSE).
7. hmi-backend: WS-подписки отключены (`UNSUBSCRIBE_ALL` через
   `ws://hmi-backend:8080/v2/hotlink` или закрытие сокета).
8. hmi-backend: WS-сессия закрыта (если использовалась).

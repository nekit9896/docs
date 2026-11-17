

## Часть 1. Классификация сценариев

### Из тестплана hydro-calculation (HY-CALC, 85 кейсов)

| Раздел | Кейсы | Тип | Обоснование |
| --- | --- | --- | --- |
| 3.1 Базовые расчёты | 001–013, 081–082 | Интеграционный | hydro-calc + hmi-backend (шлюз). Нет второго микросервиса |
| 3.2 Дебаланс расходов | 019–022 | Интеграционный | hydro-calc + hmi-backend (шлюз) |
| 3.3 Стационарность и автопостановка | 023–031 | Интеграционный | hydro-calc + hmi-backend (шлюз) |
| 3.4 Алармы давления | 014–018, 073–080 | **Системный** | `hmi.wait_alarm` → hydro-calc → REST alarm-service → hmi-backend WS. 2 микросервиса |
| 3.5 Алармы расхода, связи, индикаторы | 032–037 | **Системный** | `hmi.wait_alarm` → hydro-calc → alarm-service |
| 3.6 Самотеки и достоверность | 038–041 | **Системный** | `hmi.wait_alarm` (AlmFailOn, Gravity) → hydro-calc → alarm-service |
| 3.7 Дополнительные расчёты | 042–063 | Интеграционный | hydro-calc + hmi-backend (шлюз). Нет алармов через wait_alarm |
| 3.8 Каскадные эффекты | 083–085 | **Системный** | `hmi.wait_alarm` + взаимодействие алгоритмов + alarm-service |

**Итого из hydro-calculation → системные: 27 кейсов** (014–018, 032–041, 073–080, 083–085)

* * *

### Из тестплана hydro-history-and-model (HY-HIST, 49 кейсов)

| Кейс | Тип | Обоснование |
| --- | --- | --- |
| 001, 002, 003, 004, 006, 007, 008, 009, 010, 011, 012, 013 | Интеграционный | mod-hist + PG/Redis (один микросервис + хранилища) |
| **005** | **Системный** | START → Kafka → hydro-calc подтверждает |
| **014, 015, 016, 017, 018, 019, 020** | **Системный** | CH → mod-hist → Kafka → hydro-calc |
| 021, 024, 025, 028, 029 | Интеграционный | hmi-backend (шлюз) + hydro-calc или только mod-hist |
| **022, 023** | **Системный** | mod-hist advance → Kafka → hydro-calc |
| **026, 027** | **Системный** | Импорт → mod-hist → Kafka → hydro-calc |
| 030, 031, 032, 033, 035, 036, 037, 040, 041, 042, 044, 046, 049 | Интеграционный | mod-hist + хранилища |
| **034** | **Системный** | STALLED: hydro-calc не отвечает → mod-hist |
| **038** | **Системный** | SESSION_ERROR: hydro-calc не ответил |
| **039** | **Системный** | Retry: mod-hist → hydro-calc |
| **045** | **Системный** | Save → Play-model → hydro-calc |
| **047, 048** | **Системный** | Timeshift → Kafka → hydro-calc |

**Итого из hydro-history-and-model → системные: 19 кейсов**

* * *

### Сводка

| Источник | Интеграционные | Системные |
| --- | --- | --- |
| Тестплан hydro-calculation (85) | 58 | **27** |
| Тестплан hydro-history-and-model (49) | 30 | **19** |
| Тестплан системных тестов | — | **7** |
| **Итого** | — | **53** |

* * *

## Часть 2. Тестплан

## 1. Общие сведения

| Параметр | Значение |
| --- | --- |
| Объект | Гидроуклон как система (взаимодействие микросервисов) |
| Уровень | SYS-1 (двухсервисный), SYS-2 (трёхсервисный с алармами) |
| Кол-во сценариев | 53 |
| Из них: перенесённые из #1 | 27 (алармные, заглушки до получения док-ции alarm-service) |
| Из них: перенесённые из #2 | 19 |
| Из них: новые | 7 |
| Стенд | Тестовый стенд ЭВОСКАДА (все сервисы) |

### 1.1 Принципы

| # | Принцип |
| --- | --- |
| 1 | **hmi-backend — шлюз.** Его использование для установки/чтения данных не делает сценарий системным |
| 2 | **Системный = 2+ микросервисов.** mod-hist + hydro-calc, hydro-calc + alarm-service, mod-hist + data-manager |
| 3 | **Алармы через** `hmi.wait_alarm` = системный (hydro-calc → REST alarm-service → hmi-backend WS + alarm-view-service) |
| 4 | **Прямое чтение Kafka** (`kafka.consume`) = наблюдение, не делает сценарий системным |
| 5 | **Каждый сценарий самодостаточен.** Нет зависимостей между сценариями. Сложные предусловия — выполняются внутри сценария |
| 6 | **Мульти-сервисная верификация.** Результат проверяется в каждом сервисе цепочки |
| 7 | **Щупы в Kafka.** В каждом сценарии, где данные проходят через Kafka — ставим `kafka.consume` на промежуточные точки для локализации |

### 1.2 Уровни

| Уровень | Описание | Кол-во |
| --- | --- | --- |
| **SYS-1** | 2 микросервиса (mod-hist ↔ hydro-calc) | ~25 |
| **SYS-2** | 3 микросервиса (hydro-calc → alarm-service → hmi-backend) | ~28 |

> SYS-3 (E2E операторский) и SYS-4 (отказоустойчивость) — **в этот тестплан не входят**.

### 1.3 Правила верификации

| Правило | Пояснение |
| --- | --- |
| Мульти-сервисная проверка | Результат в каждом сервисе цепочки |
| Порядок событий | `ts_A < ts_B` для последовательных операций |
| Согласованность | Значение в Kafka = значению в CH = значению через hmi.get (пример) |
| "Щупы" | `kafka.consume` на промежуточных точках для быстрой локализации |



### 1.4 Обозначения мест для точечной проверки состояния пачки данных в потоке (далее щуп)

В сценариях используются точки наблюдения (щупы):
| Обозначение | Где | Что ловим |
| --- | --- | --- |
| `SPOT_K1` | Kafka `cspa-main - только через шлюз hmi-backend` | Входные данные (Press, Ro, Height, Control) |
| `SPOT_K2` | Kafka `model_main_{id}` | Виртуальный поток (вход + выход hydro-calc) |
| `SPOT_K3` | Kafka `model_alarm_{id}` | Алармы, сгенерированные hydro-calc |
| `SPOT_K4` | Kafka `mod-hist-commands` | Команды mod-hist → hydro-calc |
| `SPOT_K5` | Kafka `mod-hist-results` | Подтверждения hydro-calc → mod-hist |
| `SPOT_K6` | Kafka `cspa-main` (алармы) - только через шлюз hmi-backend или апи alarm-view-service | Алармы в оперативном потоке |
| `SPOT_REST` | REST alarm-view-service | Алармы, зафиксированные alarm-view-service |
| `SPOT_WS` | hmi-backend WS V2 | Алармы, видимые оператору |
| `SPOT_CH` | ClickHouse `history` | Исторические данные |
| `SPOT_REDIS` | Redis `session:*` | Состояние сессий, watermark |



## 2. Тестовый стенд

### 2.1 Компоненты

| Компонент | Роль | Примечание |
| --- | --- | --- |
| hydro-history-and-model (mod-hist / history-player) | Оркестратор сессий |  |
| hydro-calculation | Расчёты |  |
| hmi-backend | Шлюз (REST + WS) | Не считается микросервисом для классификации |
| alarm-service | Обработка/хранение алармов | **Док-ция уточняется** |
| alarm-view-service | Отображение алармов | **Док-ция уточняется** |
| data-manager | Конфигурация ИМ | **Док-ция уточняется** |
| Kafka | Брокер | Топики: cspa-main(только через шлюз hmi-backend), model_main__, model_alarm__, mod-hist-commands, mod-hist-results |
| ClickHouse | История | **Схема уточняется** |
| PostgreSQL | ИМ, сессии | **Схема уточняется** |
| Redis | Кэш, watermark |  |

### 2.2 Топики Kafka

| Топик | Producer | Consumer | Формат |
| --- | --- | --- | --- |
| `cspa-main`(только через шлюз hmi-backend) | Источники, hmi-backend | hydro-calc, hmi-backend, alarm-* | `{tag, ts, value, invalid}` |
| `model_main_{sessionId}` | mod-hist, hmi-backend | hydro-calc, mod-hist | `{tag, ts, value, invalid}` |
| `model_alarm_{sessionId}` | hydro-calc | alarm-service, alarm-view-service, mod-hist | `{tag, ts, value, text, priority, state}` |
| `mod-hist-commands` | mod-hist | hydro-calc | `{sessionId, command, params, ts}` |
| `mod-hist-results` | hydro-calc | mod-hist | `{sessionId, tag, value, ts}` |

### 2.3 Начальное состояние

*   Все сервисы UP, прогревание завершено

*   Kafka: топики существуют

*   PostgreSQL: `sessions` — пусто

*   Redis: `session:*` — отсутствует

*   ClickHouse: тестовая история ≥ 24ч для MT1.LU1 (≥ 10 000 сообщений)

*   Конфигурация ТУ1 загружена в data-manager

*   `api.list()` → пустой массив

*   `LU.State.Control = 0`, все `Disable = false`


### 2.4 Cleanup (после каждого сценария)

1.  Все активные сессии → stop → close

2.  Redis: `session:{id}:*` удалены

3.  PostgreSQL: записи удалены/помечены

4.  Kafka: consumer groups удалены

5.  ClickHouse: тестовые данные удалены

6.  hydro-calculation: буферы очищены

7.  hmi-backend: WS-подписки отключены

8.  `api.list({})` → пусто

9.  `redis.keys("session:*")` → пусто


* * *

## 3. Сценарии

### 3.1 Системные сценарии из тестплана hydro-calculation (алармные)

> **Статус:** Заглушки. Будут дополнены после получения документации по alarm-service / alarm-view-service.
> **Принцип дополнения:** Для каждого сценария добавляются щупы (SPOT_K3, SPOT_REST, SPOT_WS) и пошаговая проверка по всему пути: hydro-calc → Kafka → alarm-service → hmi-backend WS.

| ID (SYS) | ID (CALC) | Название | SYS-уровень | Статус |
| --- | --- | --- | --- | --- |
| HY-SYS-001 | HY-CALC-014 | Аларм давления: верхняя граница | SYS-2 | Заглушка |
| HY-SYS-002 | HY-CALC-015 | Аларм давления: нижняя граница | SYS-2 | Заглушка |
| HY-SYS-003 | HY-CALC-016 | Аларм давления: ровно на границе | SYS-2 | Заглушка |
| HY-SYS-004 | HY-CALC-017 | Аларм давления: invalid=true | SYS-2 | Заглушка |
| HY-SYS-005 | HY-CALC-018 | Аларм давления: CSPA | SYS-2 | Заглушка |
| HY-SYS-006 | HY-CALC-032 | Аларм расхода: AlmPressDev | SYS-2 | Заглушка |
| HY-SYS-007 | HY-CALC-033 | Аларм скорости | SYS-2 | Заглушка |
| HY-SYS-008 | HY-CALC-034 | Аларм расхода | SYS-2 | Заглушка |
| HY-SYS-009 | HY-CALC-035 | CounterKIP | SYS-2 | Заглушка |
| HY-SYS-010 | HY-CALC-036 | Индикаторы | SYS-2 | Заглушка |
| HY-SYS-011 | HY-CALC-037 | Индикаторы (продолжение) | SYS-2 | Заглушка |
| HY-SYS-012 | HY-CALC-038 | Saмотёк: Gravity | SYS-2 | Заглушка |
| HY-SYS-013 | HY-CALC-039 | GravityPossible | SYS-2 | Заглушка |
| HY-SYS-014 | HY-CALC-040 | AlmFailOn | SYS-2 | Заглушка |
| HY-SYS-015 | HY-CALC-041 | Достоверность | SYS-2 | Заглушка |
| HY-SYS-016 | HY-CALC-073 | Аларм: строгие неравенства (верх) | SYS-2 | Заглушка |
| HY-SYS-017 | HY-CALC-074 | Аларм: строгие неравенства (низ) | SYS-2 | Заглушка |
| HY-SYS-018 | HY-CALC-075 | Аларм: invalid + граница | SYS-2 | Заглушка |
| HY-SYS-019 | HY-CALC-076 | Аларм: CSPA (продолжение) | SYS-2 | Заглушка |
| HY-SYS-020 | HY-CALC-077 | Аларм: многократное срабатывание | SYS-2 | Заглушка |
| HY-SYS-021 | HY-CALC-078 | Аларм: снятие и повтор | SYS-2 | Заглушка |
| HY-SYS-022 | HY-CALC-079 | Аларм: переход через границу | SYS-2 | Заглушка |
| HY-SYS-023 | HY-CALC-080 | Аларм: невалидные форматы | SYS-2 | Заглушка |
| HY-SYS-024 | HY-CALC-083 | Каскад: Activity→Visible→KIP | SYS-2 | Заглушка |
| HY-SYS-025 | HY-CALC-084 | Каскад: все KIP отключены | SYS-2 | Заглушка |
| HY-SYS-026 | HY-CALC-085 | Каскад: SGLU_CONTROLON | SYS-2 | Заглушка |

> **Пример структуры дополнения (когда будет док-ция):**
>
> ```
> HY-SYS-001 — Аларм давления: верхняя граница
>
> Участники: hydro-calculation, alarm-service, hmi-backend (шлюз)
>
> Цепочка:
>   Автотест через hmi-backend (шлюз) задаёт Press = 7.5 (выше уставки 7.0)
>   → hmi-backend публикует в Kafka cspa-main
>   → hydro-calculation читает, сравнивает с уставкой, генерирует AlmHighOn
>   → hydro-calculation вызывает REST API alarm-service (отправка аларма)
>   → alarm-service фиксирует (запись в хранилище)
>   → hmi-backend получает аларм (WS или Kafka)
>   → hmi.wait_alarm ловит событие
>
> Обоснование:
>   Press = 7.5 > AlmHigh = 7.0 → строгое неравенство → AlmHighOn = true
>   Проверяем полный путь: от установки значения до появления аларма в каждом
>   сервисе цепочки. Щупы на каждом переходе позволяют локализовать, где
>   оборвалась цепочка прохождения данных через алгоритмы микросервисов.
>
> Предусловия:
>   • [KIP].State.Disable = false
>   • [LU].State.Control = 1
>   • [LU].State.AlmHigh = 7.0
>   • [KIP].TI.Press = 5.0 (начальное)
>   • alarm-service запущен
>
> Действия:
>   1. hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 7.5)
>   2. WAIT(10)
>   3. [ЩУП SPOT_K1] kafka.consume("cspa-main", {"tag":"*KIP1.TI.Press","value":"7.5"}, timeout=5)
>   4. [ЩУП SPOT_K3] kafka.consume("model_alarm_*", {"tag":"*AlmHighOn","value":"true"}, timeout=15)
>   5. [ЩУП SPOT_REST] GET [alarm-service]/api/... (формат уточнить)
>   6. hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn", timeout=20)
>   7. [ЩУП SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER
>
> Ожидаемый результат:
>   Шаг 3: сообщение в cspa-main с value=7.5
>   Шаг 4: аларм в model_alarm_*
>   Шаг 5: запись в alarm-service
>   Шаг 6: hmi.wait_alarm вернул true
>   Шаг 7: WS подтверждает
>
> Критерии провала:
>   • Шаг 3 нет → hmi-backend не опубликовал (проверить Kafka ACL)
>   • Шаг 3 есть, шаг 4 нет → hydro-calc не сгенерировал аларм (проверить: Control=1? Ustka?)
>   • Шаг 4 есть, шаг 5 нет → alarm-service не зафиксировал (проверить REST-вызов hydro-calc → alarm-service)
>   • Шаг 5 есть, шаг 6 нет → hmi-backend не транслирует (проверить WS-подписку)
>
> Teardown: hmi.set(Press, 5.0) → WAIT(15) → hmi.set(Control, 0) → RESET()
> Тайминг: ~45 с
> ```

* * *



## 3.2 Системные сценарии из тестплана hydro-history-and-model

| ID (SYS) | ID (HIST) | Название | SYS-уровень |
| --- | --- | --- | --- |
| HY-SYS-027 | HY-HIST-005 | Запуск: START → hydro-calc подтверждение | SYS-1 |
| HY-SYS-028 | HY-HIST-014 | historical: полный цикл CH → hydro-calc | SYS-1 |
| HY-SYS-029 | HY-HIST-015 | historical: смена скорости | SYS-1 |
| HY-SYS-030 | HY-HIST-016 | historical: замедление 0.25× | SYS-1 |
| HY-SYS-031 | HY-HIST-017 | historical: нет данных в CH | SYS-1 |
| HY-SYS-032 | HY-HIST-018 | historical: частичные данные | SYS-1 |
| HY-SYS-033 | HY-HIST-019 | historical: пагинация CH (5000 msg) | SYS-1 |
| HY-SYS-034 | HY-HIST-020 | historical: максимальная скорость | SYS-1 |
| HY-SYS-035 | HY-HIST-022 | modelling: advance 1 час | SYS-1 |
| HY-SYS-036 | HY-HIST-023 | modelling: пошаговый advance | SYS-1 |
| HY-SYS-037 | HY-HIST-026 | Импорт XLSX → hydro-calc считает | SYS-1 |
| HY-SYS-038 | HY-HIST-027 | Импорт ZIP_CSV → hydro-calc считает | SYS-1 |
| HY-SYS-039 | HY-HIST-034 | Watermark STALLED → восстановление | SYS-1 |
| HY-SYS-040 | HY-HIST-038 | SESSION_ERROR: hydro-calc не отвечает | SYS-1 |
| HY-SYS-041 | HY-HIST-039 | Retry после ERROR | SYS-1 |
| HY-SYS-042 | HY-HIST-045 | Save → Play-model → hydro-calc | SYS-1 |
| HY-SYS-043 | HY-HIST-047 | Timeshift (saved) → hydro-calc | SYS-1 |
| HY-SYS-044 | HY-HIST-048 | Timeshift (imported) → hydro-calc | SYS-1 |
| HY-SYS-045 | HY-HIST-049 | Timeshift: невалидный источник | SYS-1 |

> **Примечание:** Полное описание этих сценариев — в тестплане hydro-history-and-model (раздел 3). Здесь они приведены для полноты системного тестплана. При исполнении используются щупы SPOT_K4, SPOT_K5, SPOT_K2 на промежуточных точках.



### 3.3 Новые системные сценарии

* * *

#### HY-SYS-046 — E2E: historical с алармом (полный путь)

**Уровень:** SYS-2 **Участники:** mod-hist, hydro-calculation, alarm-service, hmi-backend (шлюз)
**Цепочка взаимодействия:**

```
(1) mod-hist создаёт сессию historical, загружает данные из ClickHouse
(2) mod-hist публикует пачки данных в Kafka model_main_{id} с виртуальным ts
(3) hydro-calculation читает model_main_{id}, рассчитывает напоры
(4) На определённом виртуальном моменте Press превышает уставку AlmHigh
(5) hydro-calculation генерирует аларм AlmHighOn
(6) hydro-calculation вызывает REST API alarm-service (отправка аларма)
(7) alarm-service фиксирует аларм (запись в хранилище)
(8) hmi-backend получает аларм (WS/Kafka)
(9) Оператор (в автотесте — hmi.wait_alarm) видит аларм
```

**Пояснение:** Сессия historical «проигрывает» историю из ClickHouse ускоренно. Есть момент, когда давление превышает уставку. Hydro-calculation, обрабатывая поток, на этом моменте генерирует аларм. Аларм уходит в alarm-service через REST. Мы проверяем, что аларм появился в **каждой** точке цепочки: в Kafka model_alarm, в alarm-service, и в hmi-backend WS, возможно alarm-view-service. Щупы на каждом переходе позволяют точно определить, на каком участке оборвалась цепочка.
**Требование:** _(будет дополнено)_
**Обоснование:**

*   В CH за 08:00–08:10: Press линейно растёт с 5.0 до 9.0 (выше уставки 7.0)

*   Момент превышения: Press = 7.0 → примерно 08:03:00 (5.0 + (9.0-5.0)×180/600 = 7.0)

*   Hydro-calculation на этом моменте генерирует AlmHighOn

*   Проверяем, что аларм прошёл весь путь до оператора

*   Это базовый системный сценарий: если он не работает — система не функционирует


**Предусловия:**

*   В CH: данные за 08:00–08:10 для MT1.LU1, Press линейно 5.0 → 9.0

*   `[LU].State.AlmHigh = 7.0` (уставка в data-manager)

*   `[KIP].State.Disable = false`

*   `[LU].State.Control = 1` (контроль активен в данных)

*   alarm-service запущен, подписан на model_alarm_*

*   Конфигурация ТУ1 загружена


**Действия:**
| Шаг | Действие | Щуп |
| --- | --- | --- |
| 1 | `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:10:00Z","speedRatio":10000,"targets":["MT1.LU1"]})` | — |
| 2 | `api.start(id)` ⚠️ | — |
| 3 | `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED | SPOT_K4: START в mod-hist-commands |
| 4 | `WAIT(35)` — 35с × 10× = 350с виртуального (Press ≈ 7.3, уже выше 7.0) | SPOT_K2: данные в model_main_{id} |
| 5 | `kafka.consume("model_alarm_" + id, {"tag":"*AlmHighOn"}, timeout=15)` | **SPOT_K3** |
| 6 | `GET [alarm-service]/api/...` (формат уточнить) | **SPOT_REST** |
| 7 | `hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn", timeout=20)` | **SPOT_WS** |
| 8 | `WAIT(30)` — ещё 300с виртуального (весь диапазон) | — |
| 9 | `ws.wait_event(id, 9, timeout=60)` — WATERMARK_COMPLETE | — |
| 10 | `api.get(id)` ⚠️ → `status = 8` (DONE) | — |
| 11 | `api.watermark(id)` ⚠️ → `= targetTime` | SPOT_REDIS |
| 12 | **Кросс-проверка:** значение Press в момент аларма (из SPOT_K2) ≈ 7.0–7.1 | SPOT_K2 |

**Ожидаемый результат:**
| Шаг | Ожидание | Зачем этот шаг |
| --- | --- | --- |
| 3 | SESSION_OPENED + START в Kafka | Подтверждаем, что mod-hist → hydro-calc связь работает |
| 4 | Данные в model_main_{id} | Подтверждаем, что mod-hist публикует из CH |
| 5 | Аларм в model_alarm_{id} | **Ключевой:** hydro-calc сгенерировал аларм |
| 6 | Запись в alarm-service | **Ключевой:** alarm-service зафиксировал |
| 7 | hmi.wait_alarm вернул true | **Ключевой:** оператор видит аларм |
| 10 | DONE | Сессия корректно завершена |
| 12 | Press ≈ 7.0–7.1 | Аларм сработал в правильный момент |

**Teardown:** `api.close(id)` ⚠️ → `WAIT(5)` → `RESET()`

* * *

#### HY-SYS-047 — Параллельные сессии: независимость потоков

**Уровень:** SYS-1 **Участники:** mod-hist (×2), hydro-calculation (×2 потока)
**Цепочка взаимодействия:**

```
Сессия A: mod-hist → Kafka model_main_{idA} → hydro-calc (поток A) → Head_A
Сессия B: mod-hist → Kafka model_main_{idB} → hydro-calc (поток B) → Head_B

Проверяем: данные A не попадают в поток B и наоборот
```

**Пояснение:** Две historical-сессии запускаются одновременно для разных ТУ. Каждая сессия имеет свой Kafka-топик (`model_main_{idA}` и `model_main_{idB}`). Hydro-calculation должен обрабатывать оба потока независимо. Если данные перемешаются (теги MT1.LU1 появятся в `model_main_{idB}`) — это критический баг: результаты расчётов будут неверны, алармы сработают на «чужих» данных.
**Требование:** _(будет дополнено)_
**Обоснование:**

*   MT1.LU1: Press = 5.0 → Head_A = (5.0/850)×101970 + H_A ≈ 663 + H_A

*   MT1.LU2: Press = 7.0 → Head_B = (7.0/850)×101970 + H_B ≈ 840 + H_B

*   Если Head_A = Head_B → перемешивание (баг)

*   Также проверяем: watermark каждой сессии независим


**Предусловия:**

*   В CH: данные за 08:00–08:10 для MT1.LU1 (Press=5.0) и MT1.LU2 (Press=7.0)

*   maxSessions ≥ 2

*   Конфигурация ТУ1 и ТУ2 загружена

*   Hydro-calculation запущен


**Действия:**
| Шаг | Действие | Щуп |
| --- | --- | --- |
| 1 | `api.createHistorical({...,"targets":["MT1.LU1"]})` → `idA` | — |
| 2 | `api.createHistorical({...,"targets":["MT1.LU2"]})` → `idB` | — |
| 3 | `api.start(idA)` ⚠️ | SPOT_K4: START для idA |
| 4 | `api.start(idB)` ⚠️ | SPOT_K4: START для idB |
| 5 | `ws.wait_event(idA, 1, timeout=30)` | — |
| 6 | `ws.wait_event(idB, 1, timeout=30)` | — |
| 7 | `WAIT(65)` — 65с × 10× = 650с > 600с (обе завершаются) | — |
| 8 | `api.get(idA)` ⚠️ → `status = 8` | — |
| 9 | `api.get(idB)` ⚠️ → `status = 8` | — |
| 10 | **Kafka-проверка A:** `kafka.consume("model_main_" + idA, {"tag":"MT1.LU2.*"}, timeout=5)` | **SPOT_K2** |
| 11 | **Kafka-проверка B:** `kafka.consume("model_main_" + idB, {"tag":"MT1.LU1.*"}, timeout=5)` | **SPOT_K2** |
| 12 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `HeadA` | — |
| 13 | `hmi.get("MT1.LU2.SGLU1.KIP11.TI.Head")` → `HeadB` | — |
| 14 | `api.watermark(idA)` ⚠️ → `wmA` | SPOT_REDIS |
| 15 | `api.watermark(idB)` ⚠️ → `wmB` | SPOT_REDIS |

**Ожидаемый результат:**
| Шаг | Ожидание | Зачем этот шаг |
| --- | --- | --- |
| 8, 9 | Обе DONE | Hydro-calc обработал оба потока |
| 10 | **Пусто** (нет тегов MT1.LU2 в топике A) | **Критично:** нет перемешивания |
| 11 | **Пусто** (нет тегов MT1.LU1 в топике B) | **Критично:** нет перемешивания |
| 12 | HeadA ≈ 663 + H_A | Расчёт по данным A |
| 13 | HeadB ≈ 840 + H_B | Расчёт по данным B |
| 14, 15 | wmA ≈ wmB (обе = targetTime) | Обе обработаны полностью |

## **Teardown:** `api.close(idA)` ⚠️ + `api.close(idB)` ⚠️ → `WAIT(5)` → `RESET()`

#### HY-SYS-048 — Аларм: полный путь в оперативном режиме

**Уровень:** SYS-2 **Участники:** hmi-backend (шлюз), hydro-calculation, alarm-service
**Цепочка взаимодействия:**

```
(1) hmi-backend (шлюз) пришет Press=9.0 в Kafka cspa-main
(2) hydro-calculation читает cspa-main, сравнивает с уставкой (9.0 > 7.0)
(3) hydro-calculation генерирует AlmHighOn = true
(4) hydro-calculation вызывает REST API alarm-service (отправка аларма)
(5) alarm-service фиксирует аларм
(6) hmi-backend транслирует аларм (WS)
(7) hmi.wait_alarm ловит событие
```

**Пояснение:** В отличие от HY-SYS-046, здесь — оперативный режим. Оператор через hmi-backend (шлюз) устанавливает Press выше уставки. Hydro-calculation в реальном времени генерирует аларм и отправляет его в alarm-service через REST. Мы проверяем полный путь: Kafka → hydro-calc → REST alarm-service → hmi-backend WS. Щупы позволяют определить, на каком этапе «потерялся» аларм.
**Требование:** _(будет дополнено)_
**Обоснование:**

*   Простейший системный сценарий с алармами: одно значение → один аларм → один путь

*   Если этот сценарий не работает — ни один аларм в системе не будет виден оператору

*   Проверяем и снятие аларма (Press вернул ниже уставки → AlmHighOn = false)


**Предусловия:**

*   `[LU].State.Control = 1`

*   `[KIP].TI.Press = 5.0` (ниже уставки)

*   `[LU].State.AlmHigh = 7.0`

*   `[KIP].State.Disable = false`

*   alarm-service запущен

*   WS-подключение активно


**Действия:**
| Шаг | Действие | Щуп |
| --- | --- | --- |
| 1 | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 9.0)` | — |
| 2 | `WAIT(10)` | SPOT_K1: Press=9.0 в cspa-main |
| 3 | `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn")` → `true` | SPOT_WS (через шлюз) |
| 4 | `kafka.consume("model_alarm_*" ИЛИ "cspa-main", {"tag":"*AlmHighOn","value":"true"}, timeout=15)` | **SPOT_K3/K6** |
| 5 | `GET [alarm-service]/api/...` (формат уточнить) | **SPOT_REST** |
| 6 | `WAIT(15)` | — |
| 7 | **Снятие:** `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` | — |
| 8 | `WAIT(15)` | — |
| 9 | `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn")` → `false` | SPOT_WS |
| 10 | `kafka.consume(..., {"tag":"*AlmHighOn","value":"false"}, timeout=15)` | **SPOT_K3/K6** |
| 11 | `GET [alarm-service]/api/...&status=active` → 0 | **SPOT_REST** |

**Ожидаемый результат:**
| Шаг | Ожидание | Зачем этот шаг |
| --- | --- | --- |
| 2 | Press=9.0 в Kafka | Подтверждаем, что шлюз опубликовал |
| 3 | AlmHighOn = true | Hydro-calc сработал |
| 4 | Аларм в Kafka | Hydro-calc опубликовал в alarm-топик |
| 5 | Запись в alarm-service | Alarm-service зафиксировал |
| 9 | AlmHighOn = false | Hydro-calc снял (Press < уставки) |
| 10 | false в Kafka | Снятие опубликовано |
| 11 | 0 активных в alarm-service | Alarm-service снял |

**Teardown:** `hmi.set("MT1.LU1.State.Control", 0)` → `WAIT(5)` → `RESET()`

* * *

#### HY-SYS-049 — data-manager: изменение уставки → hydro-calc реагирует

**Примечание:** Механизм смены уставки (data-manager REST vs hmi-backend как шлюз) — **допущение**. Если data-manager имеет отдельный REST API — использовать его. Если нет — через hmi-backend (шлюз, не делает сценарий системным, но data-manager + hydro-calc = 2 микросервиса).

* * *

#### HY-SYS-050 — Race condition: pause + advance одновременно

**Уровень:** SYS-1 **Участники:** mod-hist, hydro-calculation
**Цепочка взаимодействия:**

```
Параллельно (2 REST-запроса одновременно):
  Thread 1: api.pause(id)
  Thread 2: api.advance(id, 60)

Ожидаем: система обрабатывает без corruption.
Один запрос «выигрывает», другой получает 409 или игнорируется.
Watermark не отскакивает назад. Sess не переходит в ERROR.
```

**Пояснение:** Оператор может случайно нажать «Пауза» и «Продвинуть» одновременно (двойной клик, lag UI). В mod-hist это две операции, которые меняют состояние сессии. Если нет lock — может произойти: (а) сессия «зависает» в промежуточном состоянии, (б) watermark отскакивает назад, (в) сессия переходит в ERROR. Hydro-calculation при этом получает contradictory команды (PAUSE + данные для advance) и должен отреагировать корректно.
**Требование:** _(будет дополнено)_
**Обоснование:**

*   Watermark — монотонная величина. Если pause «откатил» watermark, а advance его продвинул — итоговое значение должно быть ≥ исходного

*   Status должен быть 2 (PAUSED) или 3 (PLAYING). Не 12 (ERROR)

*   Если hydro-calc получил PAUSE и сразу данные — он должен их проигнорировать (не считает в паузе)


**Предусловия:**

*   Сессия modelling запущена (status=3), `watermark = 09:00:00`

*   Hydro-calculation запущен, подписан на model_main_{id}


**Действия:**
| Шаг | Действие | Щуп |
| --- | --- | --- |
| 1 | `api.watermark(id)` ⚠️ → `wm_before` | SPOT_REDIS |
| 2 | **Параллельно:** `api.pause(id)` ⚠️ + `api.advance(id, 60)` ⚠️ | SPOT_K4: PAUSE/SET_WATERMARK в mod-hist-commands |
| 3 | `WAIT(5)` | — |
| 4 | `api.get(id)` ⚠️ → `status` | — |
| 5 | `api.watermark(id)` ⚠️ → `wm_after` | SPOT_REDIS |
| 6 | **Проверка:** `status ∈ {2, 3}` (не 12, не 1) | — |
| 7 | **Проверка:** `wm_after ≥ wm_before` | — |
| 8 | Если status=3: `WAIT(5)` → `api.watermark(id)` → должен двигаться | — |
| 9 | Если status=2: `api.resume(id)` ⚠️ → `WAIT(5)` → `api.watermark(id)` → должен двигаться | — |
| 10 | **Kafka:** `kafka.consume("model_main_" + id, timeout=10)` → нет «битых» сообщений | SPOT_K2 |

**Ожидаемый результат:**
| Шаг | Ожидание | Зачем этот шаг |
| --- | --- | --- |
| 4 | status = 2 или 3 | Сессия в корректном состоянии |
| 5 | wm_after ≥ wm_before | Watermark не отскочил |
| 8/9 | Watermark двигается | Сессия не зависла |
| 10 | Нет битых сообщений | Hydro-calc не получил contradicting data |

**Teardown:** Если status=2 → `api.resume(id)` ⚠️. `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `WAIT(5)` → `RESET()`

* * *

#### HY-SYS-051 — Моделирование: Press меняется на каждом шаге → напор меняется

**Уровень:** SYS-1 **Участники:** mod-hist, hydro-calculation, hmi-backend (шлюз)
**Цепочка взаимодействия:**

```
(1) Оператор (через hmi-backend, шлюз) задаёт Press = 5.0
(2) mod-hist: advance(60) → публикует в model_main_{id}
(3) hydro-calc: считает Head по Press=5.0 → Head_1
(4) Оператор задаёт Press = 5.5
(5) mod-hist: advance(60) → публикует в model_main_{id}
(6) hydro-calc: считает Head по Press=5.5 → Head_2
(7) Оператор задаёт Press = 6.0
(8) mod-hist: advance(60) → публикует в model_main_{id}
(9) hydro-calc: считает Head по Press=6.0 → Head_3
(10) Проверяем: Head_1 < Head_2 < Head_3 (монотонный рост)
```

**Пояснение:** Сценарий в моделировании: оператор моделирует постепенное повышение давления. На каждом шаге (advance) он меняет Press, и hydro-calculation пересчитывает напор. Ключевая проверка: напор меняется **согласованно** — если Press растёт, Head растёт. Если на каком-то шаге Head «скачет» или не меняется — hydro-calc не пересчитал (задержал старое значение, не прочитал новое из Kafka).
**Требование:** _(будет дополнено)_
**Обоснование:**

*   Head = (P/ρ) × 101970 + H

*   P: 5.0 → 5.5 → 6.0, ρ=850, H=63.5

*   Head: 663.3 → 679.7 → 696.2 (рост ≈ 16.5 м на 0.5 кгс/см²)

*   Если Head не меняется между шагами → hydro-calc не обновил

*   Если Head «скачет» (например, 663 → 750 → 680) → баг в расчёте или в чтении из Kafka


**Предусловия:**

*   Сессия modelling запущена (status=3)

*   `[KIP].TI.Ro = 850`, `[KIP].Height = 63.5`

*   `[KIP].State.Disable = false`

*   Hydro-calculation запущен


**Действия:**
| Шаг | Действие | Щуп |
| --- | --- | --- |
| 1 | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` | SPOT_K2: Press=5.0 |
| 2 | `WAIT(5)` | — |
| 3 | `api.advance(id, 60)` ⚠️ | SPOT_K4 |
| 4 | `WAIT(5)` | — |
| 5 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `Head_1` | SPOT_WS |
| 6 | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.5)` | SPOT_K2 |
| 7 | `WAIT(5)` | — |
| 8 | `api.advance(id, 60)` ⚠️ | SPOT_K4 |
| 9 | `WAIT(5)` | — |
| 10 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `Head_2` | SPOT_WS |
| 11 | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 6.0)` | SPOT_K2 |
| 12 | `WAIT(5)` | — |
| 13 | `api.advance(id, 60)` ⚠️ | SPOT_K4 |
| 14 | `WAIT(5)` | — |
| 15 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `Head_3` | SPOT_WS |
| 16 | **Проверка:** `Head_1 < Head_2 < Head_3` | — |
| 17 | **Проверка:** `Head_2 - Head_1 ≈ 16.4` (± 1) | — |
| 18 | **Проверка:** `Head_3 - Head_2 ≈ 16.4` (± 1) | — |

**Ожидаемый результат:**
| Шаг | Ожидание | Зачем этот шаг |
| --- | --- | --- |
| 5 | Head_1 ≈ 663.3 | Базовый расчёт корректен |
| 10 | Head_2 ≈ 679.7 | Hydro-calc пересчитал по новому Press |
| 15 | Head_3 ≈ 696.2 | Hydro-calc пересчитал по новому Press |
| 16 | Монотонный рост | Согласованность: Press↑ → Head↑ |
| 17, 18 | Дельта ≈ 16.4 | Линейность: ΔP = 0.5 → ΔH ≈ 16.4 м |

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `WAIT(5)` → `RESET()`

* * *

#### HY-SYS-052 — Timeshift: сравнение результатов с исходной сессией

**Уровень:** SYS-1
**Участники:** mod-hist (×2), hydro-calculation (×2 потока), ClickHouse
**Цепочка взаимодействия:**

```
Сессия A (исходная): historical 14:00–16:00 → Head_A(t) для каждого момента
Сессия B (timeshift): sourceMode=saved, shift=-3600 → использует данные A за 13:00–14:00
→ Head_B(t) для тех же данных, но с другими граничными условиями

Проверяем:
  (1) Head_B(t) ≠ Head_A(t) (разные граничные условия → разные результаты)
  (2) Данные в model_main_{idB} = данным в saved-сессии A за сдвинутый период
  (3) Hydro-calc рассчитал корректно по сдвинутым данным
```

**Пояснение:** Timeshift — «что было бы, если бы контроль начался на 1 час раньше?». Мы берём сохранённую сессию (A), сдвигаем время на -1 час, и пересчитываем. Гидро-расчёт зависит от начальных условий (давление на входе, расход на предыдущем интервале). Если контроль начался на 1 час раньше — начальные условия другие → напоры другие. Ключевая проверка: данные действительно взяты из saved-сессии, и hydro-calc **действительно пересчитал** (не скопировал результаты A).
**Требование:** _(будет дополнено)_
**Обоснование:**

*   Исходная сессия A: 14:00–16:00, данные из CH

*   Timeshift B: shift=-3600, startTime=15:00 → берёт данные A за 14:00–15:00

*   Если Head_B(t) = Head_A(t) для всех t → hydro-calc не пересчитал (скопировал)

*   Если данные в model_main_{idB} ≠ данным A за 14:00–15:00 → mod-hist взял неверные данные

*   Если Head_B(t) ≠ Head_A(t) и данные совпадают → всё работает корректно


**Предусловия:**

*   Сессия A: historical, 14:00–16:00, speedRatio=10000, завершена (DONE), сохранена (SAVED)

*   В сохранённых данных A: Press, Ro, QVmom за 14:00–16:00

*   Конфигурация ТУ1 загружена

*   `[LU].State.Control = 1` (в данных A)


**Действия:**
| Шаг | Действие | Щуп |
| --- | --- | --- |
| 1 | **Подготовка:** Запустить сессию A: `api.createHistorical({"startTime":"...14:00:00Z","targetTime":"...16:00:00Z","speedRatio":10000,"targets":["MT1.LU1"]})` → `idA` | — |
| 2 | `api.start(idA)` ⚠️ → `WAIT(130)` → DONE | — |
| 3 | `api.save(idA)` ⚠️ → `WAIT(20)` → SAVED | SPOT_CH: данные в saved_session_data |
| 4 | **Создать timeshift:** `api.createTimeshift({"sourceMode":0,"sourceSessionId":"idA","startTime":"...15:00:00Z","shiftDuration":-3600,"speedRatio":10000,"targets":["MT1.LU1"]})` → `idB` | — |
| 5 | `api.start(idB)` ⚠️ | SPOT_K4: START для idB |
| 6 | `ws.wait_event(idB, 1, timeout=30)` | — |
| 7 | `WAIT(70)` — 70с × 10× = 700с > 3600с/10=360с (завершится) | — |
| 8 | `ws.wait_event(idB, 9, timeout=90)` — WATERMARK_COMPLETE | — |
| 9 | `api.get(idB)` ⚠️ → `status = 8` (DONE) | — |
| 10 | **Сравнение данных:** `kafka.consume("model_main_" + idB, {"tag":"*KIP1.TI.Press"}, timeout=10)` → `press_B` | **SPOT_K2** |
| 11 | **Сравнение с исходной:** `ch.query("SELECT value FROM saved_session_data WHERE session_id='idA' AND tag='*KIP1.TI.Press' AND ts BETWEEN '14:00' AND '15:00' LIMIT 5")` → `press_A` | **SPOT_CH** |
| 12 | **Проверка:** `press_B ≈ press_A` (данные взяты из saved-сессии) | — |
| 13 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `Head_B` | SPOT_WS |
| 14 | **Сравнение результатов:** из сессии A (сохранённые данные): `Head_A` (за тот же момент) | SPOT_CH |
| 15 | **Проверка:** `Head_B ≠ Head_A` (пересчитано, не скопировано) | — |
| 16 | **Проверка:** `Head_B` соответствует формуле: `(press_B / 850) × 101970 + 63.5` | — |

**Ожидаемый результат:**
| Шаг | Ожидание | Зачем этот шаг |
| --- | --- | --- |
| 9 | DONE | Timeshift завершён |
| 12 | press_B ≈ press_A | **Критично:** данные взяты из saved-сессии A |
| 15 | Head_B ≠ Head_A | **Критично:** hydro-calc пересчитал (не скопировал) |
| 16 | Head_B = формула | Hydro-calc рассчитал корректно |

**Примечание:**

*   `Head_B ≠ Head_A` — потому что граничные условия разные. Если бы данные были полностью идентичны И граничные условия одинаковые — Head_B = Head_A. Но смысл timeshift менять момент начала → другие начальные условия → другие результаты

*   Если Press за 14:00–15:00 в сессии A **константен** (не меняется) — Head_B может быть ≈ Head_A (в пределах погрешности). В этом случае проверяем: `|Head_B - Head_A| < 1` (допустимо, т.к. данные одинаковые). Если данные **не** константные — `|Head_B - Head_A| > 1`


**Teardown:** `api.close(idB)` ⚠️ → `api.close(idA)` ⚠️ → `WAIT(5)` → `RESET()` **Тайминг:** ~4 мин

* * *

## 4. Сводная таблица

| Категория | Кол-во |
| --- | --- |
| Заглушки из hydro-calculation (до док-ции alarm-service) | 26 |
| Перенесённые из hydro-history-and-model полностью описаны | 19 |
| Остальные системные тесты | 7 |
| **Всего** | **52** |

## 5. Чек-лист подготовки стенда

| # | Проверка | Как | Ожидаемый результат |
| --- | --- | --- | --- |
| 1 | mod-hist UP | `GET /actuator/health` | `{"status":"UP"}` |
| 2 | hydro-calculation UP | Health check | `{"status":"UP"}` |
| 3 | alarm-service UP | Health check (порт уточнить) | `{"status":"UP"}` |
| 4 | alarm-view-service UP | Health check (порт уточнить) | `{"status":"UP"}` |
| 5 | hmi-backend UP + прогрет | `GET /actuator/health` → `GET /diag/instance` | UP + HTTP 200 (не 503) |
| 6 | hmi-backend WS V2 | WS `ws://hmi-backend:8080/v2/hotlink`, PING | PONG в течение 5с |
| 7 | Kafka: топики существуют | `kafka-topics --list` | `cspa-main`, `mod-hist-commands`, `mod-hist-results` в списке |
| 8 | Kafka: model_main_* создаются динамически | Создать сессию → проверить | Топик `model_main_{id}` появился |
| 9 | Kafka: model_alarm_* создаются динамически | Запустить сессию с алармом → проверить | Топик `model_alarm_{id}` появился |
| 10 | PostgreSQL: таблицы существуют | `SELECT tablename FROM pg_tables WHERE tablename IN ('sessions','session_results')` | ≥ 2 строки |
| 11 | Redis: доступен | `redis.ping` | PONG |
| 12 | Redis: ключи session:* отсутствуют | `redis.keys("session:*")` | Пустой массив |
| 13 | ClickHouse: доступность | `SELECT 1` | 1 |
| 14 | ClickHouse: тестовая история | `SELECT count(*) FROM history WHERE tag LIKE 'MT1.LU1.%' AND ts >= now() - INTERVAL 24 HOUR` | ≥ 10 000 |
| 15 | ClickHouse: история MT1.LU2 | `SELECT count(*) FROM history WHERE tag LIKE 'MT1.LU2.%' AND ts >= now() - INTERVAL 24 HOUR` | ≥ 10 000 (для HY-SYS-047) |
| 16 | Конфигурация ТУ1 | `hmi.get("MT1.LU1.State.AlmHigh")` | ≠ null (уставка загружена) |
| 17 | Конфигурация ТУ2 | `hmi.get("MT1.LU2.State.AlmHigh")` | ≠ null (для HY-SYS-047) |
| 18 | Fайлы импорта готовы | Файлы в рабочей директории | `import_test.xlsx`, `import_test.zip` существуют |
| 19 | Начальное состояние | `api.list({})` + `redis.keys("session:*")` | Пусто + пусто |
| 20 | Kafka ACL: mod-hist → model_main_* | `kafka.acls --list --topic model_main_*` | Allow produce/consume |
| 21 | Kafka ACL: hydro-calc → model_main_* | `kafka.acls --list --topic model_main_*` | Allow consume (вход) + produce (выход) |
| 22 | Kafka ACL: hydro-calc → model_alarm_* | `kafka.acls --list --topic model_alarm_*` | Allow produce |
| 23 | Kafka ACL: alarm-service → model_alarm_* | `kafka.acls --list --topic model_alarm_*` | Allow consume |
| 24 | hmi-backend: доступ к тестовым тегам | `GET /v2/tag-get?tagName=MT1.LU1.SGLU1.KIP1.TI.Press` + `X-USER-GET-ALLOW-PATTERNS: ["MT1..*"]` | HTTP 200 |
| 25 | hmi-backend: запись в теги | `POST /v2/tag-set` (Press=5.0) + заголовки | HTTP 200 |
| 26 | alarm-service: API доступен | `GET [alarm-service]/api/health` (формат уточнить) | HTTP 200 |
| 27 | alarm-view-service: API доступен | `GET [alarm-view-service]/api/health` (формат уточнить) | HTTP 200 |

* * *

## 6. Правила исполнения

| # | Правило | Пояснение |
| --- | --- | --- |
| 1 | **Изоляция** | Каждый сценарий стартует с начального состояния (2.3). Teardown обязателен. После: `api.list({})` → пусто, `redis.keys("session:*")` → пусто |
| 2 | **Ожидание** | `WAIT(n)` с запасом 5с. WS: timeout = ожидаемое + 10с. Kafka: max(interval, 30)с |
| 3 | **Мульти-сервисная проверка** | Результат проверяется в каждом сервисе цепочки. Минимум 2 источника для критичного результата |
| 4 | **Щупы в Kafka** | В каждом сценарии, где данные проходят через Kafka — `kafka.consume` на промежуточных точках (SPOT_K1…K6) |
| 5 | **Промежуточные состояния** | Для длинных каскадов — проверяем каждое: Kafka (команда), Redis (статус), PG (запись), WS (событие) также каждый раз фиксируется консьюмер лаг проверяемого топика |
| 6 | **Граничные значения** | 3 точки: ровно на границе, за границей на 1, за границей значительно |
| 7 | **Фиксация фактического результата** | При сбое — фиксировать фактический результат, не исправлять ожидаемый |
| 8 | **Локализация** | В каждом сценарии: «Если X не сработало → проверить Y в Z» |
| 9 | **Нет зависимостей между сценариями** | Каждый сценарий самодостаточен. Сложные предусловия — выполняются внутри сценария |
| 10 | **Кросс-сервисная согласованность** | Значение в Kafka = значению в CH = значению через hmi.get = значению в alarm-service |
| 11 | **Порядок событий** | Для последовательных операций: `ts_A < ts_B`. Если нарушено — баг в тайминге |

* * *

## 7. Допущения

| # | Допущение | Статус | Влияние |
| --- | --- | --- | --- |
| 1 | REST API alarm-service: путь, формат запроса/ответа | **Нет док-ции** | Блокирует все 26 заглушек (HY-SYS-001…026) + HY-SYS-046, 048 |
| 2 | REST API alarm-view-service: путь, формат | **Нет док-ции** | Аналогично |
| 3 | Kafka-топики alarm-service: из каких читает (model_alarm_* или cspa-main или оба) | **Нет док-ции** | Определяет, в каком топике ставить щуп SPOT_K3/K6 |
| 4 | Kafka-топики alarm-service: в какие пишет (output) | **Нет док-ции** | Для проверки «аларм дошёл до UI» |
| 5 | REST API data-manager: путь, формат для смены уставки | **Нет док-ции** | HY-SYS-049: используем hmi-backend как шлюз (допущение) |
| 6 | hmi.set публикует в hot topic, который = model_main_{sessionId} | **Доказано док-цией hmi-backend**, механизм привязки **уточнить** | Если hot topic ≠ model_main_{id} — данные не дойдут до hydro-calc |
| 7 | hmi.get читает из DataStream (Kafka consumer → буфер), не из Redis | **Доказано док-цией** | Для щупов: hmi.get — не «мгновенное» чтение, есть задержка до 50мс (агрегация) |
| 8 | `hmi.wait_alarm` — WS V2 SUBSCRIBE на тег аларма + ожидание SUB_ANSWER | **Из тестплана hydro-calculation** | Механизм: SUBSCRIBE → TAG_SET (или Kafka) → SUB_ANSWER с value=true |
| 9 | Hydro-calculation вызывает REST API alarm-service (не Kafka) для отправки аларма | **Из C4** |  |
| 10 | Конфигурация ТУ (уставки, Disable, Control) хранится в data-manager и приходит в hydro-calc через кеш редиса | **Из C4** | Для HY-SYS-049: смена уставки → Kafka → hydro-calc подхватывает |
| 11 | ClickHouse: таблица `history`, поля: tag, value, invalid, ts | **Нет схемы** | Используем как есть, уточним позже |
| 12 | PostgreSQL: таблица `sessions`, поля: id, status, watermark, processing_mode, created_at, started_at, closed_at | **Нет схемы** | Используем как есть |
| 13 | Saved-сессии хранятся в ClickHouse (таблица `saved_session_data`) | **Из тестплана hydro-history-and-model** | HY-SYS-052: сравнение с исходной |
| 14 | `api.start/stop/pause/resume/close/advance/setSpeed/retry` — псевдо-endpoint'ы | **Из тестплана hydro-history-and-model** | Верифицировать по коду перед исполнением |
| 15 | Max speedRatio = 60000 (60×) по UI, возможно 100000 в коде | **Из UI** | HY-SYS-034: используем 60000 |
| 16 | WS не буферизует события при отключении | **Доказано** | При переподключении — только новые события |
| 17 | Minuteman: WS-сессия без PING > 30с → hmi-backend будит/закрывает | **Доказано** | В длительных сценариях: PING каждые 15–20с |
| 18 | hmi-backend: 503 до AppWarmUp | **Доказано** | Чек-лист: после health=UP ждать diag/instance=200 |

* * *

## 8. Блокирующие вопросы (до начала исполнения)

| # | Вопрос | Блокирует | Приоритет |
| --- | --- | --- | --- |
| 1 | REST API alarm-service (путь, метод, body, response) | 26 заглушек + HY-SYS-046, 048 | **P0** |
| 2 | REST API alarm-view-service (путь, метод, body, response) | 26 заглушек | **P0** |
| 3 | Какие Kafka-топики читает/пишет alarm-service | Щупы SPOT_K3/K6 | **P0** |
| 4 | Верификация псевдо-endpoint'ов mod-hist (13 шт.) | HY-SYS-027…045 | **P0** |
| 5 | REST API data-manager (если существует отдельный) | HY-SYS-049 | **P1** |
| 6 | Механизм привязки hot topic hmi-backend к model_main_{sessionId} | Все сценарии с hmi.set → model_main | **P0** |
| 7 | Schema ClickHouse `history` | Подготовка тестовых данных | **P1** |
| 8 | Schema PostgreSQL `sessions` | Кросс-проверки | **P2** |

* * *

## 9. План исполнения

### Фаза 1: Разблокировка (P0)

| Шаг | Действие | Результат |
| --- | --- | --- |
| 1 | Получить док-цию alarm-service / alarm-view-service | Разблокировка 26 заглушек |
| 2 | Верификация псевдо-endpoint'ов mod-hist по коду | Разблокировка 19 перенесённых |
| 3 | Уточнить Kafka-топики alarm-service | Корректные щупы |
| 4 | Уточнить привязку hot topic → model_main_{id} | Корректная маршрутизация |

### Фаза 2: Smoke (быстрые сценарии, ~30 мин)

| Сценарий |
| --- |
| HY-SYS-048 (аларм: оперативный) |
| HY-SYS-050 (race condition) |
| HY-SYS-027 (START → hydro-calc) |
| HY-SYS-045 (timeshift: невалидный) |
| HY-SYS-035 (advance 1ч) |
| HY-SYS-047 (параллельные сессии) |

### Фаза 3: Core (основные, ~2 часа)

| Сценарий |
| --- |
| HY-SYS-028 (historical полный цикл) |
| HY-SYS-029 (смена скорости) |
| HY-SYS-046 (E2E historical с алармом) |
| HY-SYS-049 (data-manager: уставка) |
| HY-SYS-051 (Press на advance) |
| HY-SYS-037 (импорт XLSX) |
| HY-SYS-038 (импорт ZIP_CSV) |
| HY-SYS-042 (save → play-model) |
| HY-SYS-052 (timeshift: сравнение) |
| + 26 заглушек (по 45с) |

### Фаза 4: Extended (длинные, ~1.5 часа)

| Сценарий |
| --- |
| HY-SYS-039 (STALLED) |
| HY-SYS-040 (SESSION_ERROR) |
| HY-SYS-041 (Retry) |
| HY-SYS-043 (timeshift saved) |
| HY-SYS-044 (timeshift imported) |
| HY-SYS-030 (замедление 0.25×) |
| HY-SYS-031 (нет данных) |
| HY-SYS-032 (частичные) |
| HY-SYS-033 (пагинация) |
| HY-SYS-034 (макс скорость) |
| HY-SYS-036 (пошаговый advance) |

* * *

## 11. Итого

| Параметр | Значение |
| --- | --- |
| Всего сценариев | 52 |
| Готовы к исполнению (полностью описаны) | 26 (19 перенесённых + 7 новых) |
| Заглушки (ждут док-цию alarm-service) | 26 |
| Блокирующие вопросы (P0) | 4 |
| Общее время прогона (все фазы) | ~4–5 часов |
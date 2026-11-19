---
case_conflu: HY-CALC-064
title: "Перенос времени контроля (LuNewControlTimeAlg / FAST)"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-064
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-MODELLING-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-063, HY-CALC-028]
status: needs-review
---

# HY-CALC-064 — Перенос времени контроля (LuNewControlTimeAlg / FAST)

> `needs-review`: точный формат команды `SetTimeShift` (timestamp в отдельном
> теге или в том же) уточняется.

**Требование:** R-HYDR-046
**Описание:** По команде `SetTimeShift` система загружает историю значений
(Press, Head, Ro) на момент целевого времени из ClickHouse и записывает их как
текущие. Используется для FAST-режима (ускоренного перерасчёта истории при
переносе контроля).

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

- FAST-режим: диспетчер переносит контроль на момент времени в прошлом
- Система подтягивает состояние системы на тот момент и пересчитывает
- Цель: проверить, что на момент X всё было штатно / были алармы

**Предусловие:**

- Сессия моделирования создана: `model_main_{sessionId}`
- В ClickHouse есть история за последние 24 часа
- На момент T_target (например, 2 часа назад): KIP1_PRESS = 4.8, KIP1_RO = 850
- Текущее: KIP1_PRESS = 5.0

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetTimeShift", true)` + целевой timestamp (T_target)
2. `WAIT(event)` — LuNewControlTimeAlg
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Press")` — должно быть значение из истории
4. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` — пересчитано по историческим данным
5. Проверить в топике `model_main_{sessionId}`: значения записаны

**Ожидаемый результат:**

- Шаг 3: `KIP1_PRESS = 4.8` (значение из истории на T_target, а не текущее 5.0)
- Шаг 4: `KIP1_HEAD` пересчитано: `(4.8/850)×101970 + 63.5 = 573.6 + 63.5 = 637.1 м`
- В топике `model_main_{sessionId}` записаны значения с timestamp = T_target

**Примечание:**

- Тест требует данных в ClickHouse. Перед тестом: записать историю через Kafka (нормальный поток работы)
- FAST-режим работает в рамках сессии моделирования (топики `model_main_*`)
- Точный формат команды SetTimeShift (timestamp в отдельном теге или в том же) уточняется

**Teardown:** Закрыть сессию (`mod-hist` → close) → `RESET()`
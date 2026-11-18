---
case_conflu: HY-CALC-063
title: "План перекачки (PumpingPlanAlg)"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-063
requires: [KB-CALC-ALGO-LU-DATA-001, KB-CALC-MODELLING-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-080, HY-CALC-064]
status: needs-review
---

# HY-CALC-063 — План перекачки (PumpingPlanAlg)

> `needs-review`: формат JSON плана перекачки — **допущение** (№10 тест-плана).

**Требование:** R-HYDR-009
**Описание:** Система получает JSON-план перекачки с режимами и временными окнами.
Каждую минуту (planScannerInterval) проверяет актуальный режим. По событиям KIP
обновляет плановые значения. Записывает `PressSchedule`, `HeadSchedule`,
`RegimName`.

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

- Тестируем смену режима: «Нормальный» (P=5.0) → «Ночной» (P=4.5)
- planScannerInterval = 60 мин (из application.yml)
- Для ускорения теста: можно временно установить planScannerInterval = 1 мин

**Предусловие:**

- `LU1_TI.ARMTPumpPlan` содержит JSON плана (загружен ранее)
- Текущее время: 06:00 (начало режима «Нормальный»)
- `KIP1_PRESSSCHEDULE` — пуст или устаревшее значение
- `LU1_SCHEDULEREGIMNAME` — пуст

**Действия:**

1. `WAIT(60c)` — первый скан планнера (план загружен, определяет режим)
2. `hmi.get("MT1.LU1.TI.SchedulerRegimName")`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressSchedule")`
4. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.HeadSchedule")`
5. `WAIT(60min)` — переход к 07:00 (или сменить время в стенде)
6. Проверить: режим не изменился (всё ещё «Нормальный», до 22:00)
7. Сменить время на 22:00 (через системное время стенда или эмуляцию)
8. `WAIT(60c)` — следующий скан
9. `hmi.get("MT1.LU1.TI.SchedulerRegimName")`
10. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.PressSchedule")`

**Ожидаемый результат:**

- Шаг 2: `LU1_SCHEDULEREGIMNAME = "Нормальный"`
- Шаг 3: `KIP1_PRESSSCHEDULE = 5.0` МПа
- Шаг 4: `KIP1_HEADSCHEDULE = 670.0` м
- Шаг 9: `LU1_SCHEDULEREGIMNAME = "Ночной"`
- Шаг 10: `KIP1_PRESSSCHEDULE = 4.5` МПа

**Примечание:** Тест с планом перекачки — ночной (60 мин цикл). Для ускорения:

- Вариант 1: Временно установить `planScannerInterval = 60s` в application.yml
- Вариант 2: Симулировать смену системного времени стенда

**Teardown:** `RESET()`
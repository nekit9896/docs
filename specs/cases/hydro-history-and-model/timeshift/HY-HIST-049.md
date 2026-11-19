---
case_conflu: HY-HIST-049
title: timeshift: невалидный sourceSessionId
service: hydro-history-and-model
group: timeshift
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-049
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-047, HY-HIST-048, HY-HIST-041]
status: verified
---

# HY-HIST-049 — timeshift: невалидный sourceSessionId

**Требование:** R-HYDR-069
**Описание:** Оператор указывает `sourceSessionId`, который не существует или не в
SAVED/IMPORTED-статусе. Система отклоняет с ошибкой.

**Предусловие:**

- Сессия `non-existent-id` не существует
- Сессия `playing-id` в статусе PLAYING (3)

**Действия:**

1. `api.createTimeshift({"sourceMode":0, "sourceSessionId":"non-existent-id", "startTime":"2026-11-09T15:00:00Z", "shiftDuration":-3600, "targets":["MT1.LU1"]})` —
   несуществующая сессия; ожидаем: 400 или 404
2. `api.createTimeshift({"sourceMode":0, "sourceSessionId":"playing-id", "startTime":"2026-11-09T15:00:00Z", "shiftDuration":-3600, "targets":["MT1.LU1"]})` —
   сессия в PLAYING (не SAVED); ожидаем: 400 («источник должен быть SAVED или
   IMPORTED»)
3. `api.list({})` ⚠️ — сессии не созданы; ошибка на этапе валидации

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 1 | HTTP 404 или 400 | Источник не найден |
| 2 | HTTP 400 | Источник не в SAVED/IMPORTED |
| 3 | Пустой массив | Ничего не создано |

**Teardown:** `RESET()`

---
case_conflu: HY-HIST-048
title: "timeshift: sourceMode = imported"
service: hydro-history-and-model
group: timeshift
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-048
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-047, HY-HIST-049, HY-HIST-026, HY-HIST-027]
status: verified
---

# HY-HIST-048 — timeshift: sourceMode = imported

**Требование:** R-HYDR-069
**Описание:** Timeshift на основе импортированных данных (sourceMode = imported).
Вместо saved-сессии — данные из XLSX/ZIP_CSV. Сценарий: оператор имеет
исторические данные в файле, загружает их и делает timeshift.

**Предусловие:**

- Файл импорта готов: `timeshift_data.xlsx` (Press, Ro, QVmom за 10:00–12:00)
- Конфигурация ТУ1 загружена

**Действия:**

1. `api.createModelling({"targets":["MT1.LU1"]})` — вспомогательная
   modelling-сессия для импорта
2. `api.import_(id, file=timeshift_data.xlsx)` ⚠️ — импорт; статус → IMPORTED (7)
3. `api.close(id)` ⚠️ — вспомогательная сессия закрыта; данные импорта остаются
   доступными (в Redis/CH) для timeshift
4. `api.createTimeshift({"sourceMode":1, "sourceSessionId":"<id_импорта>", "startTime":"2026-11-09T11:00:00Z", "shiftDuration":1800, "speedRatio":10000, "targets":["MT1.LU1"]})` —
   источник imported (1), сдвиг +1800 с (30 мин вперёд); расчётный период
   10:30–11:30 (источник: 10:00–12:00 из импорта)
5. `api.start(id2)` ⚠️
6. `ws.wait_event(id2, 1, timeout=30)`
7. `WAIT(400)` — диапазон 10:30–11:30 = 3600 с; 3600/10 = 360 с реального;
   ждём 400 с
8. `ws.wait_event(id2, 9, timeout=420)` — WATERMARK_COMPLETE
9. `api.get(id2)` ⚠️ — `status = 8` (DONE), `sourceMode = 1` (imported)

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 8 | WATERMARK_COMPLETE | Timeshift завершён |
| 9 | `status = 8`, `sourceMode = 1` | Корректный источник |

**Примечание:** Если `sourceSessionId` для imported — ID сессии, в которую был
сделан импорт. Если импорт привязан к глобальному буферу (не к сессии) —
`sourceSessionId` может быть опциональным. **Уточнить по реализации.**

**Teardown:** `api.close(id2)` ⚠️ → `RESET()`

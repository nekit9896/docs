---
case_conflu: HY-HIST-047
title: "timeshift: базовый сценарий (sourceMode = saved)"
service: hydro-history-and-model
group: timeshift
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-047
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SAVE-001]
related: [HY-HIST-048, HY-HIST-049, HY-HIST-045]
status: verified
---

# HY-HIST-047 — timeshift: базовый сценарий (sourceMode = saved)

**Требование:** R-HYDR-069
**Описание:** Оператор создаёт timeshift-сессию на основе сохранённой
(sourceMode = saved): «что было бы, если бы контроль начался на 2 часа раньше?»
Система берёт сохранённые данные исходной сессии, сдвигает время на
`shiftDuration`, пересчитывает hydro-calculation по сдвинутым данным.

**Параметры timeshift:** `sourceMode = 0` (saved); `sourceSessionId` — ID
исходной сессии (SAVED); `startTime` — начало расчётного периода;
`shiftDuration` — величина сдвига (секунды, может быть отрицательной);
`targets` — теги для расчёта.

**Предусловие:**

- Существует сохранённая сессия (SAVED, status=5): `sourceSessionId = "abc-123"`
  (период 14:00–16:00, speedRatio = 1000; в сохранённых данных: Press, Ro, QVmom
  за 14:00–16:00)
- Конфигурация ТУ1 загружена
- `[LU].State.Control = 1` (контроль активен в исходной сессии)

**Действия:**

1. `api.createTimeshift({"sourceMode":0, "sourceSessionId":"abc-123", "startTime":"2026-11-09T15:00:00Z", "shiftDuration":-3600, "targets":["MT1.LU1"]})` —
   источник saved-сессия "abc-123", startTime = 15:00, shift = −3600 с (на 1 час
   назад). Итог: данные из исходной сессии за 14:00–15:00 (сдвинутые)
2. `api.start(id)` ⚠️ — загрузка данных из saved-сессии за 14:00–15:00,
   публикация в `model_main_{id}` с виртуальным ts (сдвинутым), пересчёт
3. `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED
4. Корректировка времени: при speedRatio = 1000 (1×) и диапазоне 14:00–15:00
   (3600 с) реальное время = 60 мин. Для ускорения пересоздаём с
   `speedRatio = 10000` (10×): 3600/10 = 360 с. `WAIT(400)` (400 с > 360 с)
5. `ws.wait_event(id, 9, timeout=420)` — WATERMARK_COMPLETE (timeshift — как
   historical: авто-complete по targetTime)
6. `api.get(id)` ⚠️ — `status = 8` (DONE), `processingMode = 2` (timeshift),
   `sourceMode = 0` (saved)
7. `api.watermark(id)` ⚠️ — watermark = targetTime (15:00)
8. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️ — напор рассчитан; значение
   **отличается** от исходной сессии (другие граничные условия)
9. `kafka.consume("model_main_" + id, timeout=10)` — сообщения есть, их ts —
   **сдвинутые** (14:00–15:00, а не 15:00–16:00)
10. `ch.query("SELECT tag, ts, value FROM saved_session_data WHERE session_id = 'abc-123' AND ts BETWEEN '2026-11-09T14:00:00Z' AND '2026-11-09T15:00:00Z' LIMIT 5")` —
    данные в timeshift-сессии (шаг 9) совпадают с данными исходной сессии за
    соответствующий период

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 5 | WATERMARK_COMPLETE | Timeshift завершён автоматически |
| 6 | `status = 8` (DONE), `processingMode = 2` | Корректный режим |
| 7 | `watermark = 15:00:00` | Полная обработка |
| 8 | Head рассчитан, ≠ исходному | Сдвиг повлиял на расчёт |
| 9 | ts в Kafka: 14:00–15:00 | Сдвиг применён к таймстампам |
| 10 | Данные совпадают с saved-сессией | Источник подтверждён |

**Примечание:**

- `shiftDuration = -3600` (отрицательный) — сдвиг **назад**; положительный
  (+3600) — вперёд. Оба допустимы
- Если `sourceSessionId` не существует или не в SAVED-статусе — ожидаем 400/404
- Timeshift **не** создаёт новые данные — берёт существующие (saved/imported) и
  пересчитывает hydro-calculation с другими граничными условиями

**Teardown:** `api.close(id)` ⚠️ → `RESET()`

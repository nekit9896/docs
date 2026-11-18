---
case_conflu: HY-HIST-045
title: Сохранение сессии: PLAYING → SAVING → SAVED
service: hydro-history-and-model
group: save-play
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-045
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SAVE-001, KB-HM-SESSIONS-001]
related: [HY-HIST-046, HY-HIST-047, HY-HIST-009]
status: verified
---

# HY-HIST-045 — Сохранение сессии: PLAYING → SAVING → SAVED

**Требование:** R-HYDR-073
**Описание:** Оператор сохраняет текущую сессию (PLAYING) для последующего
воспроизведения (play-model). Система: останавливает обработку, сохраняет текущие
значения всех тегов + watermark + параметры в ClickHouse (или Blob), меняет
статус PLAYING(3) → SAVING(4) → SAVED(5). После сохранения сессию можно запустить
через `play-model` — она «проиграет» сохранённое состояние.

**Что сохраняется:** текущий watermark; значения всех тегов на момент сохранения
(snapshot); параметры сессии (processingMode, targets, speedRatio, startTime,
targetTime); алармы, сработавшие до сохранения; метаданные (sessionId, createdAt,
startedAt).

**Предусловие:**

- Сессия historical запущена (status = 3, PLAYING)
- `watermark = "2026-11-09T09:30:00Z"` (обработано 90 мин из 240)
- В `model_main_{id}` есть расчётные данные (Head, PressDelta, QVmomDelta)
- Конфигурация ТУ1 загружена

**Действия:**

1. `ws.subscribe(id)` — будем ловить SESSION_SAVING (type=15) и SESSION_SAVED (type=14)
2. `api.get(id)` ⚠️ — исходное состояние: status=3, watermark=09:30:00
3. `api.save(id)` ⚠️ — система: 3→4 (SAVING); публикует SESSION_SAVING; останавливает
   WorkerExecutor; сохраняет snapshot в CH/Blob; по завершении 4→5 (SAVED),
   публикует SESSION_SAVED
4. `ws.wait_event(id, 15, timeout=10)` — SESSION_SAVING. Не пришло за 10 с —
   команда не обработана (баг в SaveSessionController)
5. `api.get(id)` ⚠️ — `status = 4` (SAVING) — нормальное промежуточное состояние
6. `WAIT(15)` — сохранение snapshot в CH (5–30 с; для 90 мин × ~10 тегов ≈
   54 000 значений)
7. `ws.wait_event(id, 14, timeout=30)` — SESSION_SAVED; в `data` может быть
   `savedAt`, `dataSize`, `targetCount`
8. `api.get(id)` ⚠️ — `status = 5` (SAVED), `savedAt` заполнено,
   `watermark = 09:30:00` (сохранён на момент save)
9. `redis.get("session:" + id + ":status")` — Redis = 5 (SAVED)
10. `pg.query("SELECT status, saved_at, watermark FROM sessions WHERE id = '<id>'")` —
    status=5, saved_at заполнено, watermark = 09:30:00
11. `ch.query("SELECT count(*) FROM saved_session_data WHERE session_id = '<id>'")`
    _(или аналогичная таблица — уточнить по реализации ValueSaver)_ — > 0 записей
12. `api.start(id)` ⚠️ — попытка запустить SAVED-сессию через обычный `start`:
    409 или 400 (SAVED запускается только через `play-model`)
13. `api.playModel(id)` ⚠️ — воспроизведение: читает сохранённые данные,
    статус: 5→1 (OPENING)→3 (PLAYING)
14. `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED
15. `api.watermark(id)` ⚠️ — watermark = 09:30:00 (начинается с сохранённого, не
    с startTime=08:00)
16. `WAIT(10)` — 10 с × 10× = 100 с виртуального
17. `api.watermark(id)` ⚠️ → `wm_play` — `wm_play > "2026-11-09T09:30:00Z"`

**Ожидаемый результат:**

| Шаг | Ожидание | Для локализации |
|---|---|---|
| 4 | `type=15` (SAVING) | Нет → SaveSessionController не обработал |
| 5 | `status = 4` (SAVING) | Промежуточное подтверждено |
| 7 | `type=14` (SAVED) | Нет → сохранение зависло (проверить CH) |
| 8 | `status = 5`, `savedAt` заполнено | Основной критерий |
| 11 | CH: > 0 записей | 0 → данные не записаны (баг в ValueSaver) |
| 12 | HTTP 409/400 | 200 → SAVED запускается через start (допустимо, но не рекомендуется) |
| 15 | `watermark = 09:30:00` | 08:00 → play-model начал с начала (не с сохранённого) |
| 17 | `wm_play > 09:30:00` | Не двигается → воспроизведение не работает |

**Примечание:**

- Если `play-model` не существует как отдельный endpoint — воспроизведение =
  `api.start(id)` ⚠️ для SAVED-сессии (шаги 12 и 13 объединяются; допущение 26)
- Таблица/структура в CH для сохранённых данных: **уточнить** по реализации (ValueSaver)

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

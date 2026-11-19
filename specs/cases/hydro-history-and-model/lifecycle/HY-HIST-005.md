---
case_conflu: HY-HIST-005
title: Запуск: CREATED → OPENING → PLAYING
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-005
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-SESSIONS-001]
related: [HY-HIST-001, HY-HIST-006, HY-HIST-038]
status: verified
---

# HY-HIST-005 — Запуск: CREATED → OPENING → PLAYING

**Требование:** R-HYDR-051, R-HYDR-052
**Описание:** Запуск сессии. Каскад: REST → CREATED(0) → OPENING(1) →
PLAYING(3). Система: (1) меняет статус 0→1 (OPENING) — идёт инициализация;
(2) подписывается на Kafka / начинает загрузку из CH; (3) отправляет `START` в
hydro-calculation; (4) инициализирует watermark = startTime; (5) по завершении
инициализации: 1→3 (PLAYING); (6) публикует `SESSION_OPENED` (WS, type=1).

**Обоснование:**

- OPENING — промежуточное: может занять время (загрузка из CH, подключение Kafka)
- Для historical с 4-часовым диапазоном: загрузка 144000+ сообщений → OPENING
  может быть 5–30 с
- Watermark после PLAYING = startTime

**Предусловие:** Сессия создана (HY-HIST-001), `status = 0`.

**Действия:**

1. `ws.subscribe(sessionId)`
2. `api.start(sessionId)` ⚠️
3. `ws.wait_event(sessionId, 1, timeout=60)` — SESSION_OPENED (type=1).
   > Таймаут 60 с: для большого диапазона OPENING может быть длительным
4. `api.get(sessionId)` ⚠️ — проверить статус
5. `api.watermark(sessionId)` ⚠️ — проверить watermark
6. `kafka.consume("mod-hist-commands", {"sessionId": sessionId, "command":"START"}, timeout=15)`

**Ожидаемый результат:**

- Шаг 3: событие `type=1` (SESSION_OPENED). Возможно: событие приходит после
  перехода в PLAYING (OPENING и PLAYING могут быть в одном срезе по времени)
- Шаг 4: `status = 3` (PLAYING), `startedAt` заполнен
- Шаг 5: `watermark = "2026-11-09T08:00:00Z"`, `target = "2026-11-09T12:00:00Z"`,
  `state = 1` (MOVING)
- Шаг 6: в Kafka:

```json
{"sessionId":"<id>","command":"START","params":{"processingMode":0,"startTime":1705300000000,"targetTime":1705314000000,"speedRatio":2000},"ts":...}
```

**Примечание:** Если OPENING → PLAYING происходит быстрее, чем WS-клиент успевает
подписаться, событие SESSION_OPENED может быть пропущено — проверяем по
`api.get`: status должен быть 3.

**Teardown:** `api.stop(sessionId)` ⚠️ → `api.close(sessionId)` ⚠️ → `WAIT(5)` → `RESET()`

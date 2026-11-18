---
case_conflu: HY-HIST-038
title: SESSION_ERROR: hydro-calculation не отвечает
service: hydro-history-and-model
group: fault-tolerance
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-038
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-FAULT-001, KB-HM-EXEC-001]
related: [HY-HIST-039, HY-HIST-034, HY-HIST-005]
status: verified
---

# HY-HIST-038 — SESSION_ERROR: hydro-calculation не отвечает

**Требование:** R-HYDR-072
**Описание:** Hydro-calculation не отвечает на команду START (нет подтверждения в
`mod-hist-results` за 30 с — `confirmTimeoutMs`). Mod-hist переходит в ERROR
(status=12). Оператор получает событие SESSION_ERROR (type=6) и причину:
«hydro-calculation не отвечает».

**Причинно-следственная связь:** Mod-hist отправляет START в `mod-hist-commands`.
Hydro-calculation должен: прочитать сообщение, подписаться на `model_main_{id}`,
прислать подтверждение в `mod-hist-results`. Если hydro-calc упал / не запущен /
Kafka ACL запрещает чтение — подтверждения нет. Через 30 с mod-hist считает:
«расчёты не идут» → ERROR. Без этого механизма сессия «зависла» бы в OPENING
(status=1) навсегда.

**Предусловие:**

- Hydro-calculation **остановлен** (kill процесса или отключение Kafka consumer)
- Сессия historical создана (status = 0, CREATED)

**Действия:**

1. `pg.query("SELECT status FROM sessions WHERE id = '<id>'")` — сессия в CREATED (0)
2. `ws.subscribe(id)` — будем ловить SESSION_ERROR (type=6)
3. `api.start(id)` ⚠️ — mod-hist: 0→1 (OPENING), публикует START, запускает
   таймер 30 с. Hydro-calc не читает → подтверждения нет
4. `kafka.consume("mod-hist-commands", {"sessionId": id, "command": "START"}, timeout=5)` —
   команда START **направлена** в Kafka (если нет — проблема в mod-hist)
5. `WAIT(40)` — 30 с confirmTimeout + 10 с margin
6. `ws.wait_event(id, 6, timeout=50)` — SESSION_ERROR; в `data.error`: причина
   «hydro-calculation not responding (timeout 30s)» или аналогичное
7. `api.get(id)` ⚠️ — `status = 12` (ERROR); поле `error`/`errorReason` заполнено
8. `redis.get("session:" + id + ":status")` — кросс-проверка: в Redis тоже 12.
   Если в Redis 1 (OPENING), а в PostgreSQL 12 — рассинхронизация (баг в обновлении кэша)
9. `pg.query("SELECT status, error_reason FROM sessions WHERE id = '<id>'")` —
   status = 12, error_reason заполнено (PG — источник истины)

**Ожидаемый результат:**

| Шаг | Ожидание | Для локализации |
|---|---|---|
| 4 | START есть в `mod-hist-commands` | Нет → mod-hist не опубликовал (баг в SessionWorker) |
| 6 | `type=6`, `data.error` содержит «timeout» или «not responding» | Нет события → баг в таймаут-обработчике |
| 7 | `status = 12` (ERROR) | Основной критерий |
| 8 | Redis: 12 | ≠ 12 → рассинхронизация Redis/PG |
| 9 | PG: 12, error_reason ≠ null | Источник истины |

**Примечание:**

- Если confirmTimeoutMs нельзя изменить — ждём 30 с (стандарт)
- Альтернативная эмуляция: Kafka ACL, чтобы hydro-calc не мог читать
  `mod-hist-commands` (hydro-calc не «умирает» — удобнее для retry-теста)

**Teardown:** Восстановить hydro-calculation → `api.close(id)` ⚠️ → `RESET()`

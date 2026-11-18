---
case_conflu: HY-HIST-044
title: Cleanup: автоматическая очистка устаревших сессий
service: hydro-history-and-model
group: config-edge-cases
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-044
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-CLEANUP-001]
related: [HY-HIST-013, HY-HIST-011]
status: verified
---

# HY-HIST-044 — Cleanup: автоматическая очистка устаревших сессий

**Требование:** R-HYDR-078
**Описание:** Периодически (каждый `Cleanup.intervalMs` = 3600 с) Cleanup
сканирует PostgreSQL на сессии в состоянии CLOSED (11) или DELETED (9), у которых
`closedAt < now() − X дней`. Такие записи удаляются из БД, связанные Redis-ключи
очищаются, данные в ClickHouse архивируются/удаляются.

**В тесте:**

- `Cleanup.intervalMs` временно = 10 с _(уточнить механизм; чек-лист п.13)_
- Порог удаления: X = 1 день _(из конфигурации; допущение 16)_
- Создаём «старую» сессию вручную (closedAt = now() − 2 дня)

**Предусловие:**

- `Cleanup.intervalMs` = 10 с (временно)
- В PostgreSQL: **нет** сессий со status = 11 (CLOSED)
- В Redis: **нет** ключей `session:*`

**Действия:**

1. `pg.query("INSERT INTO sessions (id, status, closed_at, processing_mode, created_at) VALUES ('old-test-001', 11, now() - INTERVAL '2 days', 0, now() - INTERVAL '3 days')")` —
   «старая» сессия: CLOSED, закрыта 2 дня назад
2. `pg.query("INSERT INTO sessions (...) VALUES ('new-test-002', 11, now() - INTERVAL '1 hour', 0, now() - INTERVAL '1 day')")` —
   «новая» сессия: CLOSED 1 час назад — **не должна** быть удалена
3. `redis.set("session:old-test-001:status", "11")` — Redis-ключ для «старой»
   (cleanup должен удалить его вместе с записью в PG)
4. `redis.set("session:new-test-002:status", "11")` — Redis-ключ для «новой»
   (должен **остаться**)
5. `WAIT(20)` — 10 с interval + 10 с margin
6. `pg.query("SELECT id FROM sessions WHERE id = 'old-test-001'")` — 0 строк (удалена)
7. `pg.query("SELECT id FROM sessions WHERE id = 'new-test-002'")` — 1 строка (осталась)
8. `redis.get("session:old-test-001:status")` — null (удалён)
9. `redis.get("session:new-test-002:status")` — "11" (остался)
10. `redis.keys("session:*")` — только `session:new-test-002:*`

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 6 | 0 строк (удалена) | Старая сессия убрана |
| 7 | 1 строка (осталась) | Новая сессия не тронута |
| 8 | null (удалён) | Redis-ключ старой сессии убран |
| 9 | "11" (остался) | Redis-ключ новой сессии на месте |
| 10 | Только `new-test-002` | Общий чистый результат |

**Примечание:**

- Механизм изменения `Cleanup.intervalMs`: **уточнить** (Redis / config / env /
  actuator)
- Если cleanup не удаляет Redis-ключи (только PG) — допустимо (ключи истекают по
  TTL = 24 ч), но желательно удалять и Redis
- Если cleanup архивирует (переносит в `sessions_archive`) — проверяем архивную таблицу

**Teardown:** `pg.query("DELETE FROM sessions WHERE id IN ('old-test-001','new-test-002')")`
→ `redis.del("session:new-test-002:status")` → `RESET()` (с возвратом interval к 3600 с)

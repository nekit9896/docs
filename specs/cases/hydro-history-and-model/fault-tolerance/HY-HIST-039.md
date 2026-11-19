---
case_conflu: HY-HIST-039
title: Retry: повторный запуск после ERROR
service: hydro-history-and-model
group: fault-tolerance
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-039
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-FAULT-001]
related: [HY-HIST-038, HY-HIST-005, HY-HIST-034]
status: needs-review
---

# HY-HIST-039 — Retry: повторный запуск после ERROR

**Требование:** R-HYDR-072
**Описание:** Сессия в ERROR (status=12) после сбоя hydro-calculation. Оператор
восстанавливает hydro-calc и делает retry. Сессия продолжает с того же watermark
(не заново).

**Причинно-следственная связь:** Отличие retry от новой сессии: retry сохраняет
(а) уже обработанные данные (не перечитываем из CH); (б) время (не ждём снова
OPENING); (в) контекст («я был на 08:03, продолжил с 08:03»).

**Предусловие:**

- Сессия historical в ERROR (status=12), `watermark = "2026-11-09T08:03:00Z"`
- Hydro-calculation **восстановлен** (запущен, готов принимать команды)
- `mod-hist-results` в Kafka доступен

**Действия:**

1. `kafka.consume("mod-hist-results", {"sessionId": id}, timeout=10)` —
   hydro-calc **жив** и отвечает (свежее сообщение есть). Если нет за 10 с —
   hydro-calc не готов, retry не имеет смысла
2. `ws.subscribe(id)` — будем ловить SESSION_OPENED (type=1)
3. `api.retry(id)` ⚠️ _(или `api.start(id)` ⚠️ — зависит от реализации:
   отдельный endpoint retry или повторный start для ERROR-сессии)_ — ожидаем:
   12→1 (OPENING)→3 (PLAYING), START публикуется в `mod-hist-commands`
4. `kafka.consume("mod-hist-commands", {"sessionId": id, "command": "START"}, timeout=10)` —
   **второй** START опубликован (если нет — баг в retry-логике)
5. `WAIT(15)` — hydro-calc прочитал START → подписался → подтвердил → PLAYING
6. `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED (type=1)
7. `api.get(id)` ⚠️ — `status = 3` (PLAYING); `startedAt` **не перезаписан**
   (время первого запуска); поле `error` очищено
8. `api.watermark(id)` ⚠️ — **критично**: `watermark = "2026-11-09T08:03:00Z"`,
   НЕ сбросился на startTime (08:00)
9. `WAIT(10)` — 10 с × 10× = 100 с виртуального
10. `api.watermark(id)` ⚠️ → `wm_after` — `wm_after > "2026-11-09T08:03:00Z"`
    (обработка идёт)
11. `redis.get("session:" + id + ":status")` — Redis = 3 (PLAYING), согласуется с PG

**Ожидаемый результат:**

| Шаг | Ожидание | Для локализации |
|---|---|---|
| 1 | Hydro-calc отвечает в `mod-hist-results` | Нет → hydro-calc не восстановлен, тест не валиден |
| 4 | Второй START в `mod-hist-commands` | Нет → retry не публикует команду (баг) |
| 6 | `type=1` (SESSION_OPENED) | Нет → hydro-calc снова не ответил (повторный ERROR) |
| 7 | `status = 3`, `error` очищен | error не очищен → UI покажет старую ошибку |
| 8 | `watermark = 08:03:00` (не сбросился) | **Критично**: 08:00 → retry начал заново (баг) |
| 10 | `wm_after > 08:03:00` | = 08:03 → обработка не идёт |

**Примечание:**

- Если отдельный endpoint `retry` не существует (псевдо) — используем
  `api.start(id)` ⚠️ для сессии в ERROR (допущение 7)
- Если mod-hist **не** позволяет start для ERROR (409) — допустимо: оператор
  создаёт новую сессию; сценарий помечается «не применимо к текущей реализации»
  и требует обсуждения — см. G24 в meta/discrepancies

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

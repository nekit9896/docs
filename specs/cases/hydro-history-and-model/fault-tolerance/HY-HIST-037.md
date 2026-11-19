---
case_conflu: HY-HIST-037
title: Buffer Overflow: переполнение буфера
service: hydro-history-and-model
group: fault-tolerance
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-037
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-EXEC-001]
related: [HY-HIST-038, HY-HIST-033, HY-HIST-019]
status: verified
---

# HY-HIST-037 — Buffer Overflow: переполнение буфера

**Требование:** R-HYDR-070
**Описание:** Если входящий поток быстрее, чем WorkerExecutor обрабатывает,
кольцевой буфер (10 000 сообщений) переполняется. Старые сообщения теряются
(FIFO). Система генерирует событие `BUFFER_OVERFLOW` (type=12) и фиксирует
счётчик потерянных (`messagesDropped`).

**Причинно-следственная связь:** Буфер — между «приёмом из CH/Kafka» и
«публикацией в `model_main_{id}`». При переполнении старые вытесняются новыми.
Оператор должен знать: «данные потеряны, расчёт за этот период неполный». Если
буфер переполняется **тихо** (без аларма) — расчёт будет неверен, а оператор не
узнает.

**Предусловие:**

- Сессия historical запущена, `speedRatio = 10000` (10×)
- `bufferSize` временно = 100 _(уточнить механизм: Redis key / config / env —
  переполнение за ~2 с; чек-лист п.15)_
- Поток данных: 50 msg/с (быстрее обработки при уменьшенном буфере)

**Действия:**

1. `ws.subscribe(id)` — будем ловить BUFFER_OVERFLOW (type=12). Если событие не
   придёт — переполнение не детектировано (баг в детекции)
2. `api.get(id)` ⚠️ — исходное состояние: `messagesDropped = 0`, `bufferUsed` —
   нулевая точка
3. `kafka.consume("model_main_" + id, timeout=5)` → `count_before`
4. `WAIT(5)` — 5 с × 50 msg/с = 250 сообщений > 100 (буфер) → 150 потеряны
5. `ws.wait_event(id, 12, timeout=15)` — BUFFER_OVERFLOW; в `data`:
   `dropped` (число потерянных) или `bufferUsed = 100`. Если события нет за 15 с —
   **баг**: переполнение не детектировано
6. `api.get(id)` ⚠️ — `messagesDropped > 0` (≈ 150, ± 30 из-за асинхронности),
   `bufferUsed = 100`
7. `kafka.consume("model_main_" + id, timeout=10)` → `count_after` — ожидаем:
   `count_after < count_before + 250`. Если равен — буфер не переполнялся
8. `redis.get("session:" + id + ":watermark")` — watermark **не сломан**: не
   должен «отскочить» назад

**Ожидаемый результат:**

| Шаг | Ожидание | Для локализации |
|---|---|---|
| 5 | `type=12` (BUFFER_OVERFLOW), `data.dropped ≈ 150` | Нет события → баг в детекции (Watermark/WorkerExecutor) |
| 6 | `messagesDropped ≈ 150`, `bufferUsed = 100` | 0 → буфер не переполнялся (эмуляция не сработала) |
| 7 | `count_after < count_before + 250` | Равен → сообщения не терялись |
| 8 | Watermark не отскочил назад | Отскочил → баг в логике max() |

**Примечание:**

- Механизм уменьшения bufferSize: **уточнить** (Redis / config / env)
- Если уменьшить буфер нельзя — используем стандартные 10 000 и ускоряем
  producer (`kafka.send` 10 000+ сообщений за 1 с, минуя DataExchange)
- Событие BUFFER_OVERFLOW должно прийти **до** потери всех 150 сообщений
  (детекция на пороге 90% или при первом вытеснении)

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()` (с возвратом bufferSize к 10 000)

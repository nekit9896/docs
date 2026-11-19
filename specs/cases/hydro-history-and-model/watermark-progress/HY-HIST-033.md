---
case_conflu: HY-HIST-033
title: Watermark: монотонность
service: hydro-history-and-model
group: watermark-progress
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-033
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-WATERMARK-001]
related: [HY-HIST-034, HY-HIST-024, HY-HIST-037]
status: verified
---

# HY-HIST-033 — Watermark: монотонность

**Требование:** R-HYDR-059
**Описание:** Watermark — монотонно неубывающая величина. Она никогда не может
уменьшиться (в пределах одной сессии). Если watermark «отскочил» назад — это баг:
дубли в данных, неверные расчёты, ложные алармы.

**Причинно-следственная связь:** Watermark = max(ts всех обработанных сообщений).
Математически: max(A, B) ≥ A всегда. Если в коде есть `watermark = message.ts`
(без max) — при неупорядоченной доставке Kafka watermark может «отскочить».
Сценарий ловит именно этот баг.

**Предусловие:**

- Сессия historical запущена, `speedRatio = 2000` (2×), `watermark ≈ 08:05:00`
- Сессия стабильно работает (не в ERROR, не PAUSED)

**Действия:**

1. `api.watermark(id)` ⚠️ → `wm1`
2. `WAIT(10)` — 10 с реального × 2× = 20 с виртуального
3. `api.watermark(id)` ⚠️ → `wm2`; `wm2 ≥ wm1`, разница ≈ 20 с (± 20%)
4. `WAIT(10)`
5. `api.watermark(id)` ⚠️ → `wm3`; `wm3 ≥ wm2`
6. `WAIT(10)`
7. `api.watermark(id)` ⚠️ → `wm4`; `wm4 ≥ wm3`
8. Итог: `wm1 ≤ wm2 ≤ wm3 ≤ wm4` (строгая неубывающая последовательность).
   Если хотя бы одно нарушение (wm2 < wm1) — **баг**: watermark отскочил назад

**Ожидаемый результат:**

| Пара | Ожидание | Допустимая дельта |
|---|---|---|
| wm2 − wm1 | > 0 (вырос) | ≈ 20 с ± 4 с |
| wm3 − wm2 | > 0 | ≈ 20 с ± 4 с |
| wm4 − wm3 | > 0 | ≈ 20 с ± 4 с |
| Монотонность | wm1 ≤ wm2 ≤ wm3 ≤ wm4 | Без исключений |

**Примечание:** Равенство (wm2 = wm1) допустимо, если за 10 с не было новых
сообщений (пауза в потоке). Но **уменьшение** — никогда.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

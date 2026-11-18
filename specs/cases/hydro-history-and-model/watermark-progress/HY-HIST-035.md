---
case_conflu: HY-HIST-035
title: Прогресс: расчёт по формуле
service: hydro-history-and-model
group: watermark-progress
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-035
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-WATERMARK-001]
related: [HY-HIST-036, HY-HIST-014]
status: verified
---

# HY-HIST-035 — Прогресс: расчёт по формуле

**Требование:** R-HYDR-061
**Описание:** Проверяем, что `progress` рассчитывается по формуле
`((watermark − startTime) / (targetTime − startTime)) × 100` (KB-HM-TESTSTAND-001).
Снимаем 3 точки через равные интервалы и проверяем линейный рост.

**Формула:** `progress% = ((wm − start) / (target − start)) × 100`

**Предусловие:**

- Сессия historical: `start = 08:00`, `target = 08:10` (600 с), `speedRatio = 10000` (10×)
- Сессия запущена, watermark движется

**Действия:**

1. `api.start(id)` ⚠️ _(если ещё не запущена)_ — watermark начинает с 08:00
2. `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED
3. `WAIT(3)` — 3 с реального × 10× = 30 с виртуального
4. `api.progress(id)` ⚠️ → `p1`, `api.watermark(id)` ⚠️ → `wm1` — ожидаем:
   progress ≈ 5% (30/600×100), watermark ≈ 08:00:30
5. `WAIT(3)` — ещё 30 с виртуального
6. `api.progress(id)` ⚠️ → `p2`, `api.watermark(id)` ⚠️ → `wm2` — ожидаем:
   progress ≈ 10% (60/600×100), watermark ≈ 08:01:00
7. `WAIT(3)` — ещё 30 с виртуального
8. `api.progress(id)` ⚠️ → `p3`, `api.watermark(id)` ⚠️ → `wm3` — ожидаем:
   progress ≈ 15% (90/600×100), watermark ≈ 08:01:30
9. Проверить линейность: `(p2 − p1) ≈ (p3 − p2) ≈ 5%`. Если прогресс «скачет»
   (например, p1=5%, p2=12%, p3=14%) — неравномерная обработка, возможный баг в
   WorkerExecutor

**Ожидаемый результат:**

| Захват | Progress (ожид.) | Watermark (ожид.) | Дельта progress |
|---|---|---|---|
| p1 | ≈ 5% | 08:00:30 | — |
| p2 | ≈ 10% | 08:01:00 | ≈ 5% |
| p3 | ≈ 15% | 08:01:30 | ≈ 5% |

Допустимое отклонение: ± 2% (задержки Kafka, округление).

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

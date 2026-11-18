---
case_conflu: HY-HIST-036
title: "Прогресс: ETA"
service: hydro-history-and-model
group: watermark-progress
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-036
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-WATERMARK-001]
related: [HY-HIST-035, HY-HIST-014]
status: verified
---

# HY-HIST-036 — Прогресс: ETA

**Требование:** R-HYDR-061
**Описание:** `etaSeconds` — оценка, сколько реального времени осталось до
завершения.

**Формула:** `ETA (с) = (target − wm) / (speedRatio / 1000)`
(альтернативно: `(target − wm) / speedRatio × 1000` в мс; KB-HM-TESTSTAND-001).

**Пример:** target = 08:10, wm = 08:05, speedRatio = 10000 (10×) →
ETA = 300 / 10 = 30 с реального.

**Предусловие:**

- Сессия historical: `start = 08:00`, `target = 08:10`, `speedRatio = 10000`
- Сессия запущена, `watermark ≈ 08:05:00` (300 с из 600 с)

**Действия:**

1. `api.progress(id)` ⚠️ — ожидаем: progress = 50%, etaSeconds ≈ 30
2. `WAIT(10)` — 10 с реального × 10× = 100 с виртуального; осталось:
   600 − 400 = 200 с виртуального; ETA = 200/10 = 20 с
3. `api.progress(id)` ⚠️ — ожидаем: progress ≈ 66.7%, etaSeconds ≈ 20

**Ожидаемый результат:**

| Шаг | Progress | ETA (ожид.) | Пояснение |
|---|---|---|---|
| 1 | 50% | ≈ 30 с | 300 с ост. / 10× |
| 3 | ≈ 67% | ≈ 20 с | 200 с ост. / 10× |

Допустимое отклонение ETA: ± 5 с (задержки, округление).

**Примечание:** Если ETA = 0 при progress < 100% — баг (система думает, что всё
уже обработано).

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

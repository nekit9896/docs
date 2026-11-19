---
case_conflu: HY-HIST-023
title: modelling: пошаговое advance (по 1 минуте × 3)
service: hydro-history-and-model
group: modelling
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-023
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-CALC-FORMULA-001]
related: [HY-HIST-022, HY-HIST-024, HY-HIST-021]
status: verified
---

# HY-HIST-023 — modelling: пошаговое advance (по 1 минуте × 3)

**Требование:** R-HYDR-065
**Описание:** Оператор двигает время по 1 минуте за шаг (`advance(60)`) —
«медленное воспроизведение». Проверяем: watermark увеличивается ровно на 60 с за
каждый вызов, нет накопления ошибок (drift), последовательные advance без
конфликтов.

**Причинно-следственная связь:** При пошаговом advance hydro-calculation получает
значение (или пакет) за 1 минуту и пересчитывает. В сценарии Press не меняем —
проверяем только механику advance.

**Предусловие:**

- Сессия modelling запущена (status = 3)
- `watermark = "2026-11-09T09:00:00Z"`
- Значение Press задано: `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` (чтобы
  hydro-calc имел данные для расчёта)

**Действия:**

1. `api.advance(id, 60)` ⚠️ — 09:00 → 09:01
2. `api.watermark(id)` ⚠️ — ожидаем `09:01:00` (задержка ≤ 2 с)
3. `WAIT(3)` — hydro-calculation успевает пересчитать по предыдущему состоянию
4. `api.advance(id, 60)` ⚠️ — 09:01 → 09:02
5. `api.watermark(id)` ⚠️ — ожидаем `09:02:00`, разница с шагом 2: ровно 60 с
6. `WAIT(3)`
7. `api.advance(id, 60)` ⚠️ — 09:02 → 09:03
8. `api.watermark(id)` ⚠️ — ожидаем `09:03:00`, разница с шагом 5: ровно 60 с
9. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️ — напор рассчитан: при Press=5.0,
   Ro=850, H=63.5: Head = (5.0/850)×101970 + 63.5 = 599.8 + 63.5 = **663.3 м**

**Ожидаемый результат:**

| Шаг | Watermark | Дельта | Пояснение |
|---|---|---|---|
| 2 | 09:01:00 | +60 с | Шаг 1 |
| 5 | 09:02:00 | +60 с | Шаг 2, drift = 0 |
| 8 | 09:03:00 | +60 с | Шаг 3, drift = 0 |
| 9 | Head ≈ 663.3 м | — | Hydro-calc работает |

**Критично:** Если на шаге 8 watermark = 09:03:01 или 09:02:59 — это накопление
ошибок (drift). Допустимое отклонение: ± 1 с на 3 шага.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

---
case_conflu: HY-HIST-002
title: Создание: валидация speedRatio
service: hydro-history-and-model
group: lifecycle
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-002
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-001, HY-HIST-020, HY-HIST-015]
status: needs-review
---

# HY-HIST-002 — Создание: валидация speedRatio

**Требование:** R-HYDR-050
**Описание:** Некорректные значения speedRatio отклоняются. Допустимый диапазон
по UI/конфигурации: 250–60000 (KB-HM-TESTSTAND-001).

**Обоснование:**

- `speedRatio = 0` → деление на ноль → крах
- `speedRatio = 249` → ниже минимума (0.25×)
- `speedRatio = 60001` → выше максимума (60×) — сценарий под фронт; **по факту
  в коде максимум 100 000** (расхождение, см. G21 в meta/discrepancies)
- Граничные допустимые: 250 (0.25×) и 60000 (60×)

**Предусловие:** Стенд в начальном состоянии.

**Действия:**

_Часть 1: speedRatio = 0 (недопустимо)_

1. `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T12:00:00Z","speedRatio":0,"targets":["MT1.LU1"]})`
2. Проверить: HTTP 400

_Часть 2: speedRatio = 249 (ниже минимума)_
3. `api.createHistorical({..., "speedRatio":249, ...})`
4. Проверить: HTTP 400

_Часть 3: speedRatio = 60001 (выше максимума)_
5. `api.createHistorical({..., "speedRatio":60001, ...})`
6. Проверить: HTTP 400

_Часть 4: speedRatio = 250 (граничный, допустимо)_
7. `api.createHistorical({..., "speedRatio":250, ...})`
8. Проверить: HTTP 201

_Часть 5: speedRatio = 60000 (граничный, допустимо)_
9. `api.createHistorical({..., "speedRatio":60000, ...})`
10. Проверить: HTTP 201

**Ожидаемый результат:**

- Шаги 2, 4, 6: HTTP 400, `{"error":"speedRatio must be between 250 and 60000"}`
- Шаги 8, 10: HTTP 201, сессия создана

**Teardown:** `api.close` ⚠️ для созданных → `RESET()`

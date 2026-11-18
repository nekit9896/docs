---
case_conflu: HY-CALC-082
title: "Фильтрация конфигурации: некорректные массивы"
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-082
requires: [KB-CALC-CONFIG-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-044, HY-CALC-068, HY-CALC-081]
status: verified
---

# HY-CALC-082 — Фильтрация конфигурации: некорректные массивы

**Требование:** R-HYDR-014
**Описание:** Проверка обработки некорректной конфигурации ТУ. Приоритет: средний.

**Предусловие:**

- hydro-calculation запущен

**Действия и ожидаемые результаты:**

| # | Настройка | Ожидаемое |
|---|---|---|
| 1 | `LU_KM = [0, 50, 100]`, `LU_HEIGHT = [60, 62]` (разная длина) | `KipHeightAlg` → `KIP_HEIGHT.invalid = true`. Лог ошибка. Система не упала |
| 2 | `LU_KM = [0, 100, 50]`, `LU_HEIGHT = [60, 68, 65]` (не отсортирован) | `KipHeightAlg` → интерполяция не определена или по убыванию. `KIP_HEIGHT` корректен или invalid |
| 3 | `LU_HEIGHT = [60, NaN, 65]` (NaN) | `KipHeightAlg` → `KIP_HEIGHT.invalid = true` на интервалы с NaN |
| 4 | `LU_KM = []`, `LU_HEIGHT = []` (пустые) | `KipHeightAlg` → `KIP_HEIGHT` не рассчитывается (invalid) |
| 5 | `LU_PMAXDEFAULT = [6.0, 6.1, 6.2, 6.3, 6.4]`, `LU_KM = [0, 50, 100]` (несогласованные) | `LuMaxAllowablePAlg` → `CarrierDef` по минимальной длине или invalid |

**Примечание:** Фиксируем фактическое поведение (invalid / лог / graceful
degradation). Критерий: **сервис не падает, не уходит в бесконечный цикл**.

**Teardown:** Восстановить корректную конфигурацию в data-manager → `WAIT(60c)` → `RESET()`
---
case_conflu: HY-SYS-038
title: "Импорт ZIP_CSV → hydro-calc считает"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-038
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-027, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-038 — Импорт ZIP_CSV → hydro-calc считает

## Требование
Системная проверка импорта ZIP_CSV: архив → mod-hist → Kafka → hydro-calc считает.
Полное описание сценария — HY-HIST-027.

## Описание
Системная специфика добавляет к HY-HIST-027 щупы SPOT_K2 (`model_main_{id}`) и
SPOT_K5 (`mod-hist-results`): значения из архива доходят до hydro-calc.
Файл импорта: `import_test.zip` (чек-лист п.18 §5).
Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-027 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-027 (импорт `import_test.zip`).
2. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — значения из архива.
3. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — расчётные результаты hydro-calc.

## Ожидаемый результат
Результат HY-HIST-027 + щупы: значения в потоке; hydro-calc вернул расчёт;
согласованность данных (правило 10 §6).

**Локализация:** как в HY-SYS-037.

## Teardown
Teardown HY-HIST-027 → `RESET()`.

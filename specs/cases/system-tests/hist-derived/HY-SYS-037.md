---
case_conflu: HY-SYS-037
title: "Импорт XLSX → hydro-calc считает"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-037
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-026, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-037 — Импорт XLSX → hydro-calc считает

## Требование
Системная проверка импорта XLSX: файл → mod-hist → Kafka → hydro-calc считает по
импортированным данным. Полное описание сценария — HY-HIST-026.

## Описание
Системная специфика добавляет к HY-HIST-026 щупы SPOT_K2 (`model_main_{id}`) и
SPOT_K5 (`mod-hist-results`): импортированные значения доходят до hydro-calc.
Файл импорта: `import_test.xlsx` (чек-лист п.18 §5).
Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-026 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-026 (импорт `import_test.xlsx`).
2. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — значения из файла.
3. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — расчётные результаты hydro-calc.

## Ожидаемый результат
Результат HY-HIST-026 + щупы: импортированные значения в потоке; hydro-calc вернул
расчёт (согласованность — правило 10 §6).

**Локализация:** данных в потоке нет → импорт не прошёл в mod-hist; расчёта нет →
hydro-calc.

## Teardown
Teardown HY-HIST-026 → `RESET()`.

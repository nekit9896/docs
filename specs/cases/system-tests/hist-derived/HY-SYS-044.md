---
case_conflu: HY-SYS-044
title: "Timeshift (imported) → hydro-calc"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-044
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-048, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-044 — Timeshift (imported) → hydro-calc

## Требование
Системная проверка timeshift по импортированным данным: импорт → mod-hist →
Kafka → hydro-calc считает по сдвинутому периоду. Полное описание — HY-HIST-048.

## Описание
Системная специфика добавляет к HY-HIST-048 щупы SPOT_K2 (`model_main_{id}`),
SPOT_K4 (`mod-hist-commands`), SPOT_K5 (`mod-hist-results`): START, поток
импортированных данных, расчёты hydro-calc.
Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-048 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-048 (timeshift sourceMode=imported).
2. [SPOT_K4] `kafka.consume("mod-hist-commands", …)` — START для idB.
3. [SPOT_K2] `kafka.consume("model_main_" + idB, …)` — импортированные данные.
4. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — результаты hydro-calc.

## Ожидаемый результат
Результат HY-HIST-048 + щупы: данные в потоке = импортированным (правило 10 §6);
hydro-calc рассчитал.

**Локализация:** как в HY-SYS-043.

## Teardown
Teardown HY-HIST-048 → `RESET()`.

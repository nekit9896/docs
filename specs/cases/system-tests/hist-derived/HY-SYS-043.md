---
case_conflu: HY-SYS-043
title: "Timeshift (saved) → hydro-calc"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-043
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-047, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-043 — Timeshift (saved) → hydro-calc

## Требование
Системная проверка timeshift по сохранённой сессии: saved-данные → mod-hist →
Kafka → hydro-calc считает по сдвинутому периоду. Полное описание — HY-HIST-047.

## Описание
Системная специфика добавляет к HY-HIST-047 щупы SPOT_K2 (`model_main_{id}`),
SPOT_K4 (`mod-hist-commands`), SPOT_K5 (`mod-hist-results`): START timeshift-сессии,
поток сдвинутых данных, расчёты hydro-calc.
Зависимость от псевдо-endpoint'ов `api.createTimeshift` (⚠️, G22); допущение 13 §7.

## Предусловие
Предусловия HY-HIST-047 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-047 (timeshift sourceMode=saved).
2. [SPOT_K4] `kafka.consume("mod-hist-commands", …)` — START для idB.
3. [SPOT_K2] `kafka.consume("model_main_" + idB, …)` — данные из saved-сессии.
4. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — результаты hydro-calc.

## Ожидаемый результат
Результат HY-HIST-047 + щупы: данные в потоке = saved-данным (правило 10 §6);
hydro-calc рассчитал по сдвинутым данным.

**Локализация:** пусто на SPOT_K2 → mod-hist не берёт saved-данные.

## Teardown
Teardown HY-HIST-047 → `RESET()`.

---
case_conflu: HY-SYS-027
title: "Запуск: START → hydro-calc подтверждение"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-027
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-005, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-027 — Запуск: START → hydro-calc подтверждение

## Требование
Системная проверка цепочки mod-hist → Kafka → hydro-calc: команда START доходит до
hydro-calc и подтверждается. Полное описание сценария — HY-HIST-005.

## Описание
Системная специфика добавляет к HY-HIST-005 щупы на промежуточные точки:
SPOT_K4 (`mod-hist-commands`), SPOT_K5 (`mod-hist-results`), SPOT_K2 (`model_main_{id}`).
Зависимость от псевдо-endpoint'ов `api.*` (⚠️, G22).

## Предусловие
Предусловия HY-HIST-005 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-005.
2. [SPOT_K4] `kafka.consume("mod-hist-commands", {"sessionId":id,"command":"START"}, timeout=…)` — команда.
3. [SPOT_K5] `kafka.consume("mod-hist-results", {"sessionId":id}, timeout=…)` — подтверждение hydro-calc.
4. [SPOT_K2] `kafka.consume("model_main_" + id, timeout=…)` — поток данных.

## Ожидаемый результат
Результат HY-HIST-005 + щупы: команда в `mod-hist-commands` (ts_A) и подтверждение
в `mod-hist-results` (ts_B > ts_A); поток в `model_main_{id}`.

**Локализация:** нет команды → mod-hist не выслал; команда есть, нет подтверждения →
hydro-calc не обработал; подтверждение есть, нет потока → публикация данных.

## Teardown
Teardown HY-HIST-005 → `RESET()`.

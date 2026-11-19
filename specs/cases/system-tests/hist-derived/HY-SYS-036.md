---
case_conflu: HY-SYS-036
title: "modelling: пошаговый advance"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-036
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-023, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-036 — modelling: пошаговый advance

## Требование
Системная проверка серии мелких advance: каждая команда mod-hist → Kafka →
hydro-calc подтверждается. Полное описание сценария — HY-HIST-023.

## Описание
Системная специфика добавляет к HY-HIST-023 щупы SPOT_K4 (`mod-hist-commands`),
SPOT_K2 (`model_main_{id}`), SPOT_K5 (`mod-hist-results`): проверка серии шагов
без потери команд. Зависимость от псевдо-endpoint'ов `api.advance` (⚠️, G22).

## Предусловие
Предусловия HY-HIST-023 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-023 (серия мелких advance).
2. [SPOT_K4] `kafka.consume("mod-hist-commands", …)` — каждая команда ADVANCE.
3. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — данные каждого шага.
4. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — подтверждения по шагам.

## Ожидаемый результат
Результат HY-HIST-023 + щупы: число команд = числу подтверждений; порядок событий
`ts_A < ts_B` для каждого шага.

**Локализация:** пропущен шаг → потеря команды в Kafka или обработка hydro-calc.

## Teardown
Teardown HY-HIST-023 → `RESET()`.

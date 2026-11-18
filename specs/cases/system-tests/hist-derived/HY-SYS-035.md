---
case_conflu: HY-SYS-035
title: "modelling: advance 1 час"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-035
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-022, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-035 — modelling: advance 1 час

## Требование
Системная проверка advance на 1 час: команда mod-hist → Kafka → hydro-calc
обрабатывает шаг моделирования. Полное описание сценария — HY-HIST-022.

## Описание
Системная специфика добавляет к HY-HIST-022 щупы SPOT_K4 (`mod-hist-commands`),
SPOT_K2 (`model_main_{id}`), SPOT_K5 (`mod-hist-results`): команда ADVANCE, данные
шага, подтверждение. Зависимость от псевдо-endpoint'ов `api.advance` (⚠️, G22).

## Предусловие
Предусловия HY-HIST-022 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-022 (`api.advance(id, 3600)`).
2. [SPOT_K4] `kafka.consume("mod-hist-commands", {"command":"ADVANCE"}, …)`.
3. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — данные шага.
4. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — подтверждение.

## Ожидаемый результат
Результат HY-HIST-022 + щупы: команда → данные → подтверждение; `ts_A < ts_B`;
watermark сдвинулся на 1 час.

**Локализация:** команды нет → mod-hist; данных нет → шаг не проигран; подтверждения
нет → hydro-calc не обработал.

## Teardown
Teardown HY-HIST-022 → `RESET()`.

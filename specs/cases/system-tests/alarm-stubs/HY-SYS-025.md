---
case_conflu: HY-SYS-025
title: "Каскад: все KIP отключены"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-025
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-084, HY-SYS-024]
status: placeholder
---

# HY-SYS-025 — Каскад: все KIP отключены

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Каскад при отключении всех KIP (HY-CALC-084) проходит полный системный путь:
hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS → `hmi.wait_alarm`.

## Описание
Системная верификация каскада с Disable=true на всех KIP (см. HY-CALC-084):
алармы/индикаторы каскада фиксируются в каждой точке цепочки.

## Предусловие
1. Предусловия HY-CALC-084 (все KIP отключены).
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-084 (через шлюз hmi-backend).
2. [SPOT_K1/K2] `kafka.consume(…)` — входные данные каждого перехода каскада.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — итоговые алармы.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` — по ожиданию HY-CALC-084.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Поведение каскада соответствует ожиданию HY-CALC-084; каждая точка цепочки проверена.

## Teardown
Teardown HY-CALC-084 → `RESET()`.

---
case_conflu: HY-SYS-018
title: "Аларм: invalid + граница"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-018
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-075, HY-SYS-004, HY-SYS-003]
status: placeholder
---

# HY-SYS-018 — Аларм: invalid + граница

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Комбинация invalid=true и значения на границе уставки (HY-CALC-075) проходит полный
системный путь: hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS.

## Описание
Системная верификация комбинации недостоверности и граничного значения
(см. HY-CALC-075): поведение цепочки проверяется в каждой точке.

## Предусловие
1. Предусловия HY-CALC-075.
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-075 (через шлюз hmi-backend).
2. [SPOT_K1] `kafka.consume("cspa-main", …)` — значение на границе + invalid.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — реакция hydro-calc.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` — по ожиданию HY-CALC-075.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Поведение цепочки соответствует ожиданию HY-CALC-075; каждая точка проверена.

## Teardown
Teardown HY-CALC-075 → `RESET()`.

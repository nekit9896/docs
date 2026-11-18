---
case_conflu: HY-SYS-004
title: "Аларм давления: invalid=true"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-004
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-017, HY-SYS-001]
status: placeholder
---

# HY-SYS-004 — Аларм давления: invalid=true

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Недостоверное значение давления (HY-CALC-017, invalid=true) проходит полный системный
путь: hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS.

## Описание
Системная верификация: недостоверный вход (invalid=true) обрабатывается алгоритмом
(см. HY-CALC-017); соответствующий аларм/поведение фиксируется в каждой точке цепочки.

## Предусловие
1. Предусловия HY-CALC-017 (invalid=true при установке значения).
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-017 (через шлюз hmi-backend).
2. [SPOT_K1] `kafka.consume("cspa-main", {"invalid":true}, …)` — недостоверность дошла до шины.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — реакция hydro-calc.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` — по ожиданию HY-CALC-017.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Поведение цепочки соответствует ожиданию HY-CALC-017; каждая точка проверена.

## Teardown
Teardown HY-CALC-017 → `RESET()`.

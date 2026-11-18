---
case_conflu: HY-SYS-017
title: "Аларм: строгие неравенства (низ)"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-017
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-074, HY-SYS-016]
status: placeholder
---

# HY-SYS-017 — Аларм: строгие неравенства (низ)

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Проверка строгого неравенства для нижней уставки (HY-CALC-074) проходит полный
системный путь: hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS.

## Описание
Системная верификация граничных условий для нижней уставки (см. HY-CALC-074):
результат фиксируется в каждой точке цепочки.

## Предусловие
1. Предусловия HY-CALC-074 (3 граничные точки).
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-074 (через шлюз hmi-backend).
2. [SPOT_K1] `kafka.consume("cspa-main", …)` — входные значения по точкам.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — срабатывание по ожиданию строгих неравенств.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` — по ожиданию HY-CALC-074.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Системная цепочка согласована с ожиданием строгих неравенств HY-CALC-074.

## Teardown
Teardown HY-CALC-074 → `RESET()`.

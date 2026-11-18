---
case_conflu: HY-SYS-016
title: "Аларм: строгие неравенства (верх)"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-016
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-073, HY-SYS-001, HY-SYS-003]
status: placeholder
---

# HY-SYS-016 — Аларм: строгие неравенства (верх)

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Проверка строгого неравенства для верхней уставки (HY-CALC-073) проходит полный
системный путь: hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS.

## Описание
Системная верификация граничных условий (строгое `>` vs `>=`, см. HY-CALC-073):
результат фиксируется в каждой точке цепочки.

## Предусловие
1. Предусловия HY-CALC-073 (3 точки: ровно на границе, +1, значительно — правило 6 §6).
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-073 (через шлюз hmi-backend).
2. [SPOT_K1] `kafka.consume("cspa-main", …)` — входные значения по точкам.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — срабатывание только для точек с `>`.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` — по ожиданию HY-CALC-073.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Системная цепочка согласована с ожиданием строгих неравенств HY-CALC-073.

## Teardown
Teardown HY-CALC-073 → `RESET()`.

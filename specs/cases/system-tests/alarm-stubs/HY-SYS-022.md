---
case_conflu: HY-SYS-022
title: "Аларм: переход через границу"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-022
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-079, HY-SYS-021]
status: placeholder
---

# HY-SYS-022 — Аларм: переход через границу

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Плавный переход через границу уставки (HY-CALC-079) проходит полный системный путь:
hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS → `hmi.wait_alarm`.

## Описание
Системная верификация динамического перехода через уставку (см. HY-CALC-079):
срабатывание происходит ровно на переходе; фиксация в каждой точке цепочки.

## Предусловие
1. Предусловия HY-CALC-079 (плавное изменение значения через уставку).
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-079 (через шлюз hmi-backend).
2. [SPOT_K1] `kafka.consume("cspa-main", …)` — последовательность значений через границу.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — момент срабатывания.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` → true.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Срабатывание ровно на переходе; аларм зафиксирован в каждой точке цепочки;
критерии провала — как в HY-SYS-001.

## Teardown
Teardown HY-CALC-079 → `RESET()`.

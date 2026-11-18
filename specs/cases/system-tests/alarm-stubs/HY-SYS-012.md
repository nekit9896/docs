---
case_conflu: HY-SYS-012
title: "Самотёк: Gravity"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-012
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-038, HY-SYS-001]
status: placeholder
---

# HY-SYS-012 — Самотёк: Gravity

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.
> В источнике название с опечаткой «Saмотёк» (G30).

## Требование
Аларм самотёка Gravity (HY-CALC-038) проходит полный системный путь: hydro-calc →
Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS → `hmi.wait_alarm`.

## Описание
Системная верификация: после срабатывания AlmGravity (см. HY-CALC-038) аларм
фиксируется в каждой точке цепочки (SPOT_K3 → SPOT_REST → SPOT_WS).

## Предусловие
1. Предусловия HY-CALC-038.
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-038 (через шлюз hmi-backend).
2. [SPOT_K1] `kafka.consume("cspa-main", …)` — входные данные.
3. [SPOT_K3] `kafka.consume("model_alarm_*", {"tag":"*Gravity*"}, timeout=15)` — тег уточнить по HY-CALC-038.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` → true.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Аларм зафиксирован в каждой точке цепочки; критерии провала — как в HY-SYS-001.

## Teardown
Teardown HY-CALC-038 → `RESET()`.

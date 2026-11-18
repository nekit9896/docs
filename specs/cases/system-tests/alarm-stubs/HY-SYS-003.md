---
case_conflu: HY-SYS-003
title: "Аларм давления: ровно на границе"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-003
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-016, HY-SYS-001]
status: placeholder
---

# HY-SYS-003 — Аларм давления: ровно на границе

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Граничное значение давления (HY-CALC-016): поведение на ровно уставке проходит полный
системный путь: hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS.

## Описание
Системная верификация граничного случая (строгое неравенство — см. HY-CALC-016):
аларм НЕ срабатывает ровно на уставке либо срабатывает — по ожиданию базового кейса;
результат фиксируется в каждой точке цепочки.

## Предусловие
1. Предусловия HY-CALC-016.
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-016 (Press = ровно уставка, через шлюз).
2. [SPOT_K1] `kafka.consume("cspa-main", …)` — входное значение.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — есть/нет аларма по ожиданию HY-CALC-016.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` — результат по ожиданию базового кейса.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Системная цепочка согласована с ожиданием HY-CALC-016 (граничное неравенство);
каждая точка либо содержит аларм, либо его нет — синхронно.

## Teardown
Teardown HY-CALC-016 → `RESET()`.

---
case_conflu: HY-SYS-023
title: "Аларм: невалидные форматы"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-023
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-080, HY-SYS-004]
status: placeholder
---

# HY-SYS-023 — Аларм: невалидные форматы

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Невалидные форматы данных (HY-CALC-080) обрабатываются без разрыва цепочки:
hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS.

## Описание
Системная верификация устойчивости к невалидным форматам (см. HY-CALC-080):
система не падает; поведение (аларм/игнор) фиксируется в каждой точке цепочки.

## Предусловие
1. Предусловия HY-CALC-080 (набор невалидных значений/форматов).
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-080 (через шлюз hmi-backend).
2. [SPOT_K1] `kafka.consume("cspa-main", …)` — невалидные сообщения.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — реакция hydro-calc по ожиданию.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` — по ожиданию HY-CALC-080.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Поведение цепочки соответствует ожиданию HY-CALC-080; сервисы доступны после прогона.

## Teardown
Teardown HY-CALC-080 → `RESET()`.

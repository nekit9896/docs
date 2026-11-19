---
case_conflu: HY-SYS-020
title: "Аларм: многократное срабатывание"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-020
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-077, HY-SYS-021]
status: placeholder
---

# HY-SYS-020 — Аларм: многократное срабатывание

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Многократное срабатывание аларма (HY-CALC-077) проходит полный системный путь:
hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS → `hmi.wait_alarm`.

## Описание
Системная верификация серии срабатываний (см. HY-CALC-077): каждое срабатывание
доходит до alarm-service и WS; проверяется отсутствие потерь/дублей в цепочке.

## Предусловие
1. Предусловия HY-CALC-077.
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-077 (серия пересечений уставки, через шлюз).
2. [SPOT_K1] `kafka.consume("cspa-main", …)` — входные значения.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — все события серии.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28) — число записей.
5. `hmi.wait_alarm(...)` — по каждому срабатыванию.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Каждое срабатывание зафиксировано в каждой точке цепочки; число событий на щупах
согласовано; критерии провала — как в HY-SYS-001.

## Teardown
Teardown HY-CALC-077 → `RESET()`.

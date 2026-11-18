---
case_conflu: HY-SYS-021
title: "Аларм: снятие и повтор"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-021
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-078, HY-SYS-020]
status: placeholder
---

# HY-SYS-021 — Аларм: снятие и повтор

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Снятие аларма и его повторное срабатывание (HY-CALC-078) проходят полный системный
путь: hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS.

## Описание
Системная верификация цикла «срабатывание → снятие → повтор» (см. HY-CALC-078):
снятие фиксируется в alarm-service (активных нет), повтор — новой записью; каждая
точка цепочки проверяется.

## Предусловие
1. Предусловия HY-CALC-078.
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-078 (через шлюз hmi-backend).
2. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — срабатывание, затем снятие (value=false).
3. [SPOT_REST] `GET [alarm-service]/api/...&status=active` — 0 активных после снятия.
4. [SPOT_K3] повтор: `{"tag":"*Alm*","value":"true"}` — новое срабатывание.
5. [SPOT_REST] — новая активная запись.
6. `hmi.wait_alarm(...)` → true на повторе; [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Снятие и повтор зафиксированы в каждой точке цепочки; активные записи в alarm-service
соответствуют фазе аларма; критерии провала — как в HY-SYS-001.

## Teardown
Teardown HY-CALC-078 → `RESET()`.

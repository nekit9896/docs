---
case_conflu: HY-SYS-024
title: "Каскад: Activity→Visible→KIP"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-024
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-083, HY-SYS-025]
status: placeholder
---

# HY-SYS-024 — Каскад: Activity→Visible→KIP

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.
> Каскадный сценарий: взаимодействие алгоритмов + `hmi.wait_alarm` + alarm-service.

## Требование
Каскад Activity→Visible→KIP (HY-CALC-083) проходит полный системный путь:
hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS → `hmi.wait_alarm`.

## Описание
Системная верификация каскада из нескольких алгоритмов (см. HY-CALC-083): на каждом
переходе каскада ставится щуп (правило 5 §6 — промежуточные состояния); итоговый
аларм фиксируется в каждой точке цепочки.

## Предусловие
1. Предусловия HY-CALC-083.
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-083 (через шлюз hmi-backend).
2. [SPOT_K1/K2] `kafka.consume(…)` — входные данные каждого перехода каскада.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — итоговый аларм.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` → true.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Каждое звено каскада подтверждено щупом; аларм зафиксирован в каждой точке
цепочки; критерии провала — как в HY-SYS-001.

## Teardown
Teardown HY-CALC-083 → `RESET()`.

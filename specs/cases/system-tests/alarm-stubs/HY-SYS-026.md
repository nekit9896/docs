---
case_conflu: HY-SYS-026
title: "Каскад: SGLU_CONTROLON"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-026
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-085, HY-SYS-024]
status: placeholder
---

# HY-SYS-026 — Каскад: SGLU_CONTROLON

> Статус источника: **заглушка** (G28). Структура дополнения — как в HY-SYS-001.

## Требование
Каскад с управлением SGLU_CONTROLON (HY-CALC-085) проходит полный системный путь:
hydro-calc → Kafka `model_alarm_{id}` → alarm-service → hmi-backend WS → `hmi.wait_alarm`.

## Описание
Системная верификация каскада с переключением `SGLU_CONTROLON` (см. HY-CALC-085):
каждое звено каскада подтверждается щупом; итоговые алармы — в каждой точке цепочки.

## Предусловие
1. Предусловия HY-CALC-085.
2. alarm-service запущен; чек-лист KB-SYS-TESTPLAN-001 §5.

## Действия
1. Выполнить шаги HY-CALC-085 (через шлюз hmi-backend).
2. [SPOT_K1/K2] `kafka.consume(…)` — входные данные каждого перехода каскада.
3. [SPOT_K3] `kafka.consume("model_alarm_*", …, timeout=15)` — итоговые алармы.
4. [SPOT_REST] `GET [alarm-service]/api/...` (формат уточнить — G28).
5. `hmi.wait_alarm(...)` — по ожиданию HY-CALC-085.
6. [SPOT_WS] WS V2 SUBSCRIBE → SUB_ANSWER.

## Ожидаемый результат
Поведение каскада соответствует ожиданию HY-CALC-085; каждая точка цепочки проверена.

## Teardown
Teardown HY-CALC-085 → `RESET()`.

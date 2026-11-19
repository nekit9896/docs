---
case_conflu: HY-SYS-049
title: "data-manager: изменение уставки → hydro-calc реагирует"
service: system-tests
group: new-scenarios
source: confluence/test-plan-of-system-tests.md#HY-SYS-049
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [KB-HM-TESTSTAND-001]
status: placeholder
---

# HY-SYS-049 — data-manager: изменение уставки → hydro-calc реагирует

> В источнике сценарий не описан — только примечание (G27). Ниже — содержимое
> источника; построение шагов требует документации.

## Требование
Смена уставки в data-manager подхватывается hydro-calc (уставка приходит в hydro-calc
через кеш Redis — допущение 10 §7).

## Описание
**Примечание источника:** механизм смены уставки (data-manager REST vs hmi-backend
как шлюз) — **допущение**. Если data-manager имеет отдельный REST API — использовать
его. Если нет — через hmi-backend (шлюз, не делает сценарий системным, но
data-manager + hydro-calc = 2 микросервиса — принцип 2 §1.1).

## Предусловие
Требует документации: REST API data-manager (блокирующий вопрос 5, P1, G29).

## Действия
Не описаны в источнике (G27).

## Ожидаемый результат
Не описан в источнике (G27).

## Teardown
Не описан в источнике (G27).

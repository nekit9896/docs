---
case_conflu: HY-SYS-040
title: "SESSION_ERROR: hydro-calc не отвечает"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-040
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-038, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-040 — SESSION_ERROR: hydro-calc не отвечает

## Требование
Системная проверка перехода сессии в SESSION_ERROR при полном отказе hydro-calc
(нет ответа на команды). Полное описание сценария — HY-HIST-038.

## Описание
Системная специфика добавляет к HY-HIST-038 щупы SPOT_K4 (`mod-hist-commands`),
SPOT_K5 (`mod-hist-results`, пусто) и SPOT_REDIS: команды уходят, подтверждений нет →
SESSION_ERROR. Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-038 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-038 (hydro-calc не отвечает).
2. [SPOT_K4] `kafka.consume("mod-hist-commands", …)` — команды отправляются.
3. [SPOT_K5] `kafka.consume("mod-hist-results", timeout=…)` — пусто.
4. [SPOT_REDIS] состояние сессии → SESSION_ERROR.

## Ожидаемый результат
Результат HY-HIST-038 + щупы: сессия переходит в SESSION_ERROR; команды в Kafka
есть, подтверждений нет — локализация обрыва на hydro-calc.

## Teardown
Teardown HY-HIST-038 → `RESET()`.

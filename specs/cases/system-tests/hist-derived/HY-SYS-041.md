---
case_conflu: HY-SYS-041
title: "Retry после ERROR"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-041
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-039, KB-HM-TESTPLAN-001]
status: needs-review
---

# HY-SYS-041 — Retry после ERROR

## Требование
Системная проверка retry: после ERROR сессия перезапускается и hydro-calc получает
команды заново. Полное описание сценария — HY-HIST-039.

## Описание
Системная специфика добавляет к HY-HIST-039 щупы SPOT_K4 (`mod-hist-commands`),
SPOT_K5 (`mod-hist-results`) и SPOT_REDIS: повторный START после ERROR.
⚠️ Базовый кейс HY-HIST-039 помечен в источнике как неприменимый (G24) — кейс требует
уточнения у разработки. Зависимость от псевдо-endpoint'ов `api.retry` (⚠️, G22).

## Предусловие
Предусловия HY-HIST-039 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-039 (довести сессию до ERROR, выполнить retry).
2. [SPOT_K4] `kafka.consume("mod-hist-commands", …)` — повторная команда START.
3. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — hydro-calc отвечает снова.
4. [SPOT_REDIS] статус сессии выходит из ERROR.

## Ожидаемый результат
Результат HY-HIST-039 (статус после retry — уточнить, G24) + щупы: цепочка
mod-hist → hydro-calc восстановлена; подтверждения приходят.

## Teardown
Teardown HY-HIST-039 → `RESET()`.

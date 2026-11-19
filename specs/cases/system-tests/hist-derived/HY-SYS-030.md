---
case_conflu: HY-SYS-030
title: "historical: замедление 0.25×"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-030
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-016, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-030 — historical: замедление 0.25×

## Требование
Системная проверка замедления до 0.25×: темп потока соответствует замедлению.
Полное описание сценария — HY-HIST-016.

## Описание
Системная специфика добавляет к HY-HIST-016 щупы SPOT_K2 (`model_main_{id}`) и
SPOT_K4 (`mod-hist-commands`): команда замедления и измерение интервала сообщений.
Зависимость от псевдо-endpoint'ов `api.*` (⚠️, G22).

## Предусловие
Предусловия HY-HIST-016 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-016 (смена speedRatio на 0.25×).
2. [SPOT_K4] `kafka.consume("mod-hist-commands", …)` — команда setSpeed.
3. [SPOT_K2] `kafka.consume("model_main_" + id, timeout=…)` — интервал сообщений до/после.

## Ожидаемый результат
Результат HY-HIST-016 + щупы: интервал сообщений в `model_main_{id}` вырос
соответственно замедлению; порядок событий `ts_A < ts_B`.

**Локализация:** интервал не изменился → mod-hist публикует прежним темпом.

## Teardown
Teardown HY-HIST-016 → `RESET()`.

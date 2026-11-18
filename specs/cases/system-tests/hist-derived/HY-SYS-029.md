---
case_conflu: HY-SYS-029
title: "historical: смена скорости"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-029
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-015, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-029 — historical: смена скорости

## Требование
Системная проверка смены скорости воспроизведения: команда setSpeed доходит до
hydro-calc и влияет на поток. Полное описание сценария — HY-HIST-015.

## Описание
Системная специфика добавляет к HY-HIST-015 щупы SPOT_K2 (`model_main_{id}`) и
SPOT_K4 (`mod-hist-commands`): команда смены скорости и изменение темпа публикации.
Зависимость от псевдо-endpoint'ов `api.*` (⚠️, G22).

## Предусловие
Предусловия HY-HIST-015 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-015.
2. [SPOT_K4] `kafka.consume("mod-hist-commands", …)` — команда смены скорости.
3. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — темп публикации до/после.

## Ожидаемый результат
Результат HY-HIST-015 + щупы: команда в `mod-hist-commands`; темп данных в
`model_main_{id}` соответствует новой скорости.

**Локализация:** команды нет → mod-hist; темп не изменился → hydro-calc игнорирует.

## Teardown
Teardown HY-HIST-015 → `RESET()`.

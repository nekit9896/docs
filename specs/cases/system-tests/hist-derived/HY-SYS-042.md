---
case_conflu: HY-SYS-042
title: "Save → Play-model → hydro-calc"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-042
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-045, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-042 — Save → Play-model → hydro-calc

## Требование
Системная проверка цикла «сохранение → проигрывание play-model → hydro-calc»:
данные сохранённой сессии проигрываются заново. Полное описание сценария — HY-HIST-045.

## Описание
Системная специфика добавляет к HY-HIST-045 щупы SPOT_CH (`saved_session_data`),
SPOT_K2 (`model_main_{id}`) и SPOT_K5 (`mod-hist-results`): сохранённые данные
попадают в поток и обрабатываются hydro-calc.
Зависимость от псевдо-endpoint'ов `api.save` (⚠️, G22); допущение 13 §7.

## Предусловие
Предусловия HY-HIST-045 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-045 (save сессии, запуск play-model).
2. [SPOT_CH] `ch.query(...)` — данные в `saved_session_data`.
3. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — проигранные данные.
4. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — результаты hydro-calc.

## Ожидаемый результат
Результат HY-HIST-045 + щупы: данные из `saved_session_data` = данным в
`model_main_{id}` (правило 10 §6); hydro-calc рассчитал.

**Локализация:** нет в CH → save не сохранил; нет в потоке → play-model.

## Teardown
Teardown HY-HIST-045 → `RESET()`.

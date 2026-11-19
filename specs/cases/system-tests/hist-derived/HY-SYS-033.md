---
case_conflu: HY-SYS-033
title: "historical: пагинация CH (5000 msg)"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-033
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-019, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-033 — historical: пагинация CH (5000 msg)

## Требование
Системная проверка пагинации чтения CH (5000 сообщений): mod-hist → Kafka →
hydro-calc получает все пачки без потерь. Полное описание сценария — HY-HIST-019.

## Описание
Системная специфика добавляет к HY-HIST-019 щупы SPOT_K2 (`model_main_{id}`) и
SPOT_K5 (`mod-hist-results`): контроль числа пачек и отсутствия потерь на границах
страниц. Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-019 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-019 (объём ≥ 5000 сообщений).
2. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — суммарно все пачки, ts монотонны.
3. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — подтверждения по пачкам.

## Ожидаемый результат
Результат HY-HIST-019 + щупы: количество сообщений сходится; на границах страниц
нет пропусков/дублей (правило 11 §6 — `ts_A < ts_B`).

**Локализация:** пропуск на границе → пагинация mod-hist.

## Teardown
Teardown HY-HIST-019 → `RESET()`.

---
case_conflu: HY-SYS-032
title: "historical: частичные данные"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-032
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-018, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-032 — historical: частичные данные

## Требование
Системная проверка частичных данных в CH: mod-hist → Kafka → hydro-calc
пропускает дыры без ошибок. Полное описание сценария — HY-HIST-018.

## Описание
Системная специфика добавляет к HY-HIST-018 щупы SPOT_K2 (`model_main_{id}`) и
SPOT_K5 (`mod-hist-results`): поток не содержит интерполяции там, где данных нет.
Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-018 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-018 (период с «дырами» в данных).
2. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — пачки без ложных значений.
3. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — подтверждения hydro-calc.

## Ожидаемый результат
Результат HY-HIST-018 + щупы: пропуски данных не заполняются выдуманными значениями;
порядок событий `ts_A < ts_B`.

**Локализация:** появились ложные значения → mod-hist интерполирует (не должно).

## Teardown
Teardown HY-HIST-018 → `RESET()`.

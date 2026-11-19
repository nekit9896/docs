---
case_conflu: HY-SYS-028
title: "historical: полный цикл CH → hydro-calc"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-028
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-014, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-028 — historical: полный цикл CH → hydro-calc

## Требование
Системная проверка полного цикла historical: ClickHouse → mod-hist → Kafka →
hydro-calc. Полное описание сценария — HY-HIST-014.

## Описание
Системная специфика добавляет к HY-HIST-014 щупы SPOT_K2 (`model_main_{id}`),
SPOT_K4 (`mod-hist-commands`), SPOT_K5 (`mod-hist-results`) на промежуточных точках.
Зависимость от псевдо-endpoint'ов `api.*` (⚠️, G22).

## Предусловие
Предусловия HY-HIST-014 + чек-лист стенда KB-SYS-TESTPLAN-001 §5
(тестовая история CH ≥ 24ч, ≥ 10 000 сообщений).

## Действия
1. Шаги HY-HIST-014.
2. [SPOT_K4] `kafka.consume("mod-hist-commands", …)` — команды START/SET_WATERMARK.
3. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — пачки данных из CH.
4. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — подтверждения hydro-calc.

## Ожидаемый результат
Результат HY-HIST-014 + щупы: данные из CH прошли весь путь; порядок событий
`ts_A < ts_B` (правило 11 §6).

**Локализация:** пусто на SPOT_K2 → mod-hist не читает CH; есть SPOT_K2, нет SPOT_K5 →
hydro-calc не отвечает.

## Teardown
Teardown HY-HIST-014 → `RESET()`.

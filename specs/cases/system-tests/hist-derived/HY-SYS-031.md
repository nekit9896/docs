---
case_conflu: HY-SYS-031
title: "historical: нет данных в CH"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-031
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-017, KB-HM-TESTPLAN-001]
status: needs-review
---

# HY-SYS-031 — historical: нет данных в CH

## Требование
Системная проверка поведения при отсутствии данных в ClickHouse: mod-hist →
Kafka → hydro-calc обходится без зависаний. Полное описание сценария — HY-HIST-017.

## Описание
Системная специфика добавляет к HY-HIST-017 щупы SPOT_K2 (`model_main_{id}`) и
SPOT_K5 (`mod-hist-results`): проверка отсутствия «мусорного» потока и корректного
статуса. Нужно уточнить у разработки: ожидаемый статус — ERROR или DONE (HY-HIST-017
в источнике противоречив, G23). Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-017 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-017 (диапазон времени без данных).
2. [SPOT_K2] `kafka.consume("model_main_" + id, timeout=…)` — поток пуст либо нет «битых» сообщений.
3. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — ответ hydro-calc.

## Ожидаемый результат
Результат HY-HIST-017 (статус — уточнить, G23) + щупы: нет перемешанных/битых
сообщений; сессия завершается корректно.

**Локализация:** сессия зависла → mod-hist; ошибки в потоке → hydro-calc.

## Teardown
Teardown HY-HIST-017 → `RESET()`.

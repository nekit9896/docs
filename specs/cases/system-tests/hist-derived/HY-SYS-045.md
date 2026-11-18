---
case_conflu: HY-SYS-045
title: "Timeshift: невалидный источник"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-045
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-049, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-045 — Timeshift: невалидный источник

## Требование
Системная проверка timeshift с невалидным источником: mod-hist отклоняет создание
сессии без разрыва цепочки остальных сервисов. Полное описание — HY-HIST-049.

## Описание
Системная специфика добавляет к HY-HIST-049 щупы SPOT_K2 (`model_main_{id}` — пусто)
и SPOT_K5 (`mod-hist-results` — пусто): после отказа в создании потоковых данных быть
не должно. Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-049 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-049 (создание timeshift с невалидным sourceSessionId/источником).
2. [SPOT_K2] `kafka.consume("model_main_" + idB, timeout=…)` — пусто (топика/данных нет).
3. [SPOT_K5] `kafka.consume("mod-hist-results", timeout=…)` — пусто.
4. `api.list({})` — сессия не создана/закрыта.

## Ожидаемый результат
Результат HY-HIST-049 + щупы: ошибка создания корректно обработана; «мусорных»
сообщений в Kafka нет; система работоспособна.

## Teardown
Teardown HY-HIST-049 → `RESET()`.

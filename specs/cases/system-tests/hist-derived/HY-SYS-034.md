---
case_conflu: HY-SYS-034
title: "historical: максимальная скорость"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-034
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-020, KB-HM-TESTPLAN-001]
status: needs-review
---

# HY-SYS-034 — historical: максимальная скорость

## Требование
Системная проверка воспроизведения на максимальной скорости: mod-hist → Kafka →
hydro-calc успевает обрабатывать поток. Полное описание сценария — HY-HIST-020.

## Описание
Системная специфика добавляет к HY-HIST-020 щупы SPOT_K2 (`model_main_{id}`) и
SPOT_K5 (`mod-hist-results`): контроль потерь под нагрузкой.
⚠️ Допущение 15 §7 (G21): max speedRatio = 60000 (60×) по UI, возможно 100000 в коде —
используем 60000; базовый кейс HY-HIST-020 в источнике требует уточнения.
Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-020 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-020 (speedRatio=60000).
2. [SPOT_K2] `kafka.consume("model_main_" + id, …)` — поток без потерь.
3. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — hydro-calc успевает отвечать.

## Ожидаемый результат
Результат HY-HIST-020 + щупы: все пачки обработаны; watermark доходит до targetTime;
нет сообщений о переполнении/потерях.

**Локализация:** потери в потоке → mod-hist не успевает; отставание подтверждений →
hydro-calc перегружен.

## Teardown
Teardown HY-HIST-020 → `RESET()`.

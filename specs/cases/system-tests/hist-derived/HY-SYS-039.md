---
case_conflu: HY-SYS-039
title: "Watermark STALLED → восстановление"
service: system-tests
group: hist-derived
source: confluence/test-plan-of-system-tests.md#HY-SYS-039
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-034, KB-HM-WATERMARK-001, KB-HM-TESTPLAN-001]
status: verified
---

# HY-SYS-039 — Watermark STALLED → восстановление

## Требование
Системная проверка зависания watermark (hydro-calc не отвечает → mod-hist) и
восстановления после отклика. Полное описание сценария — HY-HIST-034.

## Описание
Системная специфика добавляет к HY-HIST-034 щупы SPOT_K5 (`mod-hist-results`) и
SPOT_REDIS (`session:*`, watermark): отсутствие подтверждений → STALLED; после
восстановления — watermark догоняет. Зависимость от псевдо-endpoint'ов (⚠️, G22).

## Предусловие
Предусловия HY-HIST-034 + чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
1. Шаги HY-HIST-034 (искусственное зависание hydro-calc).
2. [SPOT_K5] `kafka.consume("mod-hist-results", …)` — подтверждения прекращаются.
3. [SPOT_REDIS] `redis.keys("session:*")` — watermark замирает → статус STALLED.
4. После восстановления — [SPOT_K5]/[SPOT_REDIS] — watermark двигается.

## Ожидаемый результат
Результат HY-HIST-034 + щупы: STALLED при отсутствии подтверждений; после
восстановления hydro-calc — догоняющий прогресс (монотонность watermark, G18).

**Локализация:** STALLED без остановки hydro-calc → потеря сообщений в Kafka.

## Teardown
Teardown HY-HIST-034 → `RESET()`.

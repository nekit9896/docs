---
case_conflu: HY-SYS-001
title: "Аларм давления: верхняя граница"
service: system-tests
group: alarm-stubs
source: confluence/test-plan-of-system-tests.md#HY-SYS-001
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-CALC-014]
status: placeholder
---

# HY-SYS-001 — Аларм давления: верхняя граница

> Статус источника: **заглушка** — будет дополнена после получения документации
> alarm-service / alarm-view-service (допущения 1–4, G28). Ниже — пример структуры
> дополнения, приведённый в источнике (§3.1).

## Требование
Аларм верхней границы давления (HY-CALC-014) проходит полный системный путь:
`hmi.set` (шлюз) → Kafka `cspa-main` → hydro-calc → REST alarm-service →
hmi-backend WS → `hmi.wait_alarm`.

## Описание
Полный путь: автотест через hmi-backend задаёт Press = 7.5 (выше уставки 7.0) →
hmi-backend публикует в `cspa-main` → hydro-calc считает, сравнивает с уставкой,
генерирует AlmHighOn → вызывает REST API alarm-service → alarm-service фиксирует →
hmi-backend получает аларм (WS/Kafka) → `hmi.wait_alarm` ловит событие.

Обоснование: Press = 7.5 > AlmHigh = 7.0 → строгое неравенство → AlmHighOn = true.
Щупы на каждом переходе позволяют локализовать обрыв цепочки.

## Предусловие
1. `[KIP].State.Disable = false`; `[LU].State.Control = 1`; `[LU].State.AlmHigh = 7.0`;
   `[KIP].TI.Press = 5.0` (начальное) — см. HY-CALC-014.
2. alarm-service запущен, подписан на `model_alarm_*` (допущение 3).
3. Чек-лист стенда KB-SYS-TESTPLAN-001 §5.

## Действия
| Шаг | Действие | Щуп |
|---|---|---|
| 1 | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 7.5)` | — |
| 2 | `WAIT(10)` | — |
| 3 | `kafka.consume("cspa-main", {"tag":"*KIP1.TI.Press","value":"7.5"}, timeout=5)` | SPOT_K1 |
| 4 | `kafka.consume("model_alarm_*", {"tag":"*AlmHighOn","value":"true"}, timeout=15)` | SPOT_K3 |
| 5 | `GET [alarm-service]/api/...` (формат уточнить — G28) | SPOT_REST |
| 6 | `hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn", timeout=20)` | SPOT_WS |
| 7 | WS V2 SUBSCRIBE → SUB_ANSWER | SPOT_WS |

## Ожидаемый результат
Шаг 3: сообщение в `cspa-main` с value=7.5; шаг 4: аларм в `model_alarm_*`;
шаг 5: запись в alarm-service; шаг 6: `hmi.wait_alarm` вернул true; шаг 7: WS подтверждает.

**Критерии провала:** шаг 3 нет → hmi-backend не опубликовал (проверить Kafka ACL);
шаг 3 есть, шаг 4 нет → hydro-calc не сгенерировал аларм (проверить Control=1, уставку);
шаг 4 есть, шаг 5 нет → alarm-service не зафиксировал (REST-вызов hydro-calc → alarm-service);
шаг 5 есть, шаг 6 нет → hmi-backend не транслирует (WS-подписка).

## Teardown
`hmi.set(Press, 5.0)` → `WAIT(15)` → `hmi.set(Control, 0)` → `RESET()`.

Тайминг: ~45 с.

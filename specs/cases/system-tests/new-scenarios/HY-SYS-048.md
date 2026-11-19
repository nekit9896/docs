---
case_conflu: HY-SYS-048
title: "Аларм: полный путь в оперативном режиме"
service: system-tests
group: new-scenarios
source: confluence/test-plan-of-system-tests.md#HY-SYS-048
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-SYS-046, HY-CALC-014, KB-HMI-WS-001]
status: needs-review
---

# HY-SYS-048 — Аларм: полный путь в оперативном режиме

**Уровень:** SYS-2. **Участники:** hmi-backend (шлюз), hydro-calculation, alarm-service.

## Требование
_(будет дополнено — в источнике не заполнено)_

## Описание
В отличие от HY-SYS-046, здесь — оперативный режим. Оператор через hmi-backend
(шлюз) устанавливает Press выше уставки. Hydro-calculation в реальном времени
генерирует аларм и отправляет его в alarm-service через REST. Проверяется полный
путь: Kafka → hydro-calc → REST alarm-service → hmi-backend WS. Щупы определяют,
на каком этапе «потерялся» аларм.

**Цепочка:**
1. hmi-backend (шлюз) шлёт Press=9.0 в Kafka `cspa-main`.
2. hydro-calculation читает `cspa-main`, сравнивает с уставкой (9.0 > 7.0).
3. hydro-calculation генерирует AlmHighOn = true.
4. hydro-calculation вызывает REST API alarm-service.
5. alarm-service фиксирует аларм.
6. hmi-backend транслирует аларм (WS).
7. `hmi.wait_alarm` ловит событие.

**Обоснование:** простейший системный сценарий с алармами: одно значение → один
аларм → один путь. Если он не работает — ни один аларм в системе не будет виден
оператору. Проверяем и снятие аларма (Press вернул ниже уставки → AlmHighOn = false).

## Предусловие
1. `[LU].State.Control = 1`; `[KIP].TI.Press = 5.0` (ниже уставки);
   `[LU].State.AlmHigh = 7.0`; `[KIP].State.Disable = false`.
2. alarm-service запущен.
3. WS-подключение активно.

## Действия
| Шаг | Действие | Щуп |
|---|---|---|
| 1 | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 9.0)` | — |
| 2 | `WAIT(10)` | SPOT_K1: Press=9.0 в `cspa-main` |
| 3 | `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn")` → `true` | SPOT_WS (через шлюз) |
| 4 | `kafka.consume("model_alarm_*"` ИЛИ `"cspa-main", {"tag":"*AlmHighOn","value":"true"}, timeout=15)` | **SPOT_K3/K6** |
| 5 | `GET [alarm-service]/api/...` (формат уточнить — G28) | **SPOT_REST** |
| 6 | `WAIT(15)` | — |
| 7 | **Снятие:** `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` | — |
| 8 | `WAIT(15)` | — |
| 9 | `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn")` → `false` | SPOT_WS |
| 10 | `kafka.consume(..., {"tag":"*AlmHighOn","value":"false"}, timeout=15)` | **SPOT_K3/K6** |
| 11 | `GET [alarm-service]/api/...&status=active` → 0 | **SPOT_REST** |

## Ожидаемый результат
| Шаг | Ожидание | Зачем этот шаг |
|---|---|---|
| 2 | Press=9.0 в Kafka | Шлюз опубликовал |
| 3 | AlmHighOn = true | Hydro-calc сработал |
| 4 | Аларм в Kafka | Hydro-calc опубликовал в alarm-топик |
| 5 | Запись в alarm-service | Alarm-service зафиксировал |
| 9 | AlmHighOn = false | Hydro-calc снял (Press < уставки) |
| 10 | false в Kafka | Снятие опубликовано |
| 11 | 0 активных в alarm-service | Alarm-service снял |

**Критерии провала:** как в HY-SYS-046 (локализация по щупам).

## Teardown
`hmi.set("MT1.LU1.State.Control", 0)` → `WAIT(5)` → `RESET()`.

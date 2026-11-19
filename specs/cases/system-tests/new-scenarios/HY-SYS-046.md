---
case_conflu: HY-SYS-046
title: "E2E: historical с алармом (полный путь)"
service: system-tests
group: new-scenarios
source: confluence/test-plan-of-system-tests.md#HY-SYS-046
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [HY-HIST-014, KB-HM-TESTPLAN-001, KB-CALC-FORMULA-001]
status: needs-review
---

# HY-SYS-046 — E2E: historical с алармом (полный путь)

**Уровень:** SYS-2. **Участники:** mod-hist, hydro-calculation, alarm-service,
hmi-backend (шлюз).

## Требование
_(будет дополнено — в источнике не заполнено)_

## Описание
Сессия historical «проигрывает» историю из ClickHouse ускоренно. Есть момент, когда
давление превышает уставку. Hydro-calculation, обрабатывая поток, на этом моменте
генерирует аларм и отправляет его в alarm-service через REST. Аларм проверяется в
**каждой** точке цепочки: Kafka `model_alarm`, alarm-service, hmi-backend WS
(возможно, alarm-view-service). Щупы на каждом переходе локализуют обрыв.

**Цепочка:**
1. mod-hist создаёт сессию historical, загружает данные из ClickHouse.
2. mod-hist публикует пачки в Kafka `model_main_{id}` с виртуальным ts.
3. hydro-calculation читает `model_main_{id}`, рассчитывает напоры (KB-CALC-FORMULA-001).
4. На определённом виртуальном моменте Press превышает уставку AlmHigh.
5. hydro-calculation генерирует AlmHighOn.
6. hydro-calculation вызывает REST API alarm-service (допущение 9 §7).
7. alarm-service фиксирует аларм.
8. hmi-backend получает аларм (WS/Kafka).
9. Оператор (в автотесте — `hmi.wait_alarm`) видит аларм.

**Обоснование:** в CH за 08:00–08:10 Press линейно растёт с 5.0 до 9.0 (выше уставки
7.0); момент превышения Press = 7.0 — примерно 08:03:00 (5.0 + (9.0−5.0)×180/600 = 7.0).
Проверяем, что аларм прошёл весь путь до оператора. Это базовый системный сценарий:
если он не работает — система не функционирует.

## Предусловие
1. В CH: данные за 08:00–08:10 для MT1.LU1, Press линейно 5.0 → 9.0.
2. `[LU].State.AlmHigh = 7.0` (уставка в data-manager).
3. `[KIP].State.Disable = false`; `[LU].State.Control = 1`.
4. alarm-service запущен, подписан на `model_alarm_*`.
5. Конфигурация ТУ1 загружена.

## Действия
| Шаг | Действие | Щуп |
|---|---|---|
| 1 | `api.createHistorical({"startTime":"2026-11-09T08:00:00Z","targetTime":"2026-11-09T08:10:00Z","speedRatio":10000,"targets":["MT1.LU1"]})` | — |
| 2 | `api.start(id)` ⚠️ | — |
| 3 | `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED | SPOT_K4: START в `mod-hist-commands` |
| 4 | `WAIT(35)` — 35с × 10× = 350с виртуального (Press ≈ 7.3, уже выше 7.0) | SPOT_K2: данные в `model_main_{id}` |
| 5 | `kafka.consume("model_alarm_" + id, {"tag":"*AlmHighOn"}, timeout=15)` | **SPOT_K3** |
| 6 | `GET [alarm-service]/api/...` (формат уточнить — G28) | **SPOT_REST** |
| 7 | `hmi.wait_alarm("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn", timeout=20)` | **SPOT_WS** |
| 8 | `WAIT(30)` — ещё 300с виртуального (весь диапазон) | — |
| 9 | `ws.wait_event(id, 9, timeout=60)` — WATERMARK_COMPLETE | — |
| 10 | `api.get(id)` ⚠️ → `status = 8` (DONE) | — |
| 11 | `api.watermark(id)` ⚠️ → `= targetTime` | SPOT_REDIS |
| 12 | **Кросс-проверка:** значение Press в момент аларма (из SPOT_K2) ≈ 7.0–7.1 | SPOT_K2 |

## Ожидаемый результат
| Шаг | Ожидание | Зачем этот шаг |
|---|---|---|
| 3 | SESSION_OPENED + START в Kafka | mod-hist → hydro-calc связь работает |
| 4 | Данные в `model_main_{id}` | mod-hist публикует из CH |
| 5 | Аларм в `model_alarm_{id}` | **Ключевой:** hydro-calc сгенерировал аларм |
| 6 | Запись в alarm-service | **Ключевой:** alarm-service зафиксировал |
| 7 | `hmi.wait_alarm` вернул true | **Ключевой:** оператор видит аларм |
| 10 | DONE | Сессия корректно завершена |
| 12 | Press ≈ 7.0–7.1 | Аларм сработал в правильный момент |

**Критерии провала:** шаг 5 нет → hydro-calc не сгенерировал (Control=1? уставка?);
шаг 5 есть, шаг 6 нет → alarm-service не зафиксировал; шаг 6 есть, шаг 7 нет →
hmi-backend не транслирует.

## Teardown
`api.close(id)` ⚠️ → `WAIT(5)` → `RESET()`.

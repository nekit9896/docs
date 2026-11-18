---
case_conflu: HY-SYS-047
title: "Параллельные сессии: независимость потоков"
service: system-tests
group: new-scenarios
source: confluence/test-plan-of-system-tests.md#HY-SYS-047
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [KB-HM-TESTPLAN-001, KB-CALC-FORMULA-001]
status: verified
---

# HY-SYS-047 — Параллельные сессии: независимость потоков

**Уровень:** SYS-1. **Участники:** mod-hist (×2), hydro-calculation (×2 потока).

## Требование
_(будет дополнено — в источнике не заполнено)_

## Описание
Две historical-сессии запускаются одновременно для разных ТУ. Каждая сессия имеет
свой Kafka-топик (`model_main_{idA}` и `model_main_{idB}`). Hydro-calculation должен
обрабатывать оба потока независимо. Если данные перемешаются (теги MT1.LU1 появятся в
`model_main_{idB}`) — это критический баг: результаты расчётов будут неверны,
алармы сработают на «чужих» данных.

**Цепочка:**
- Сессия A: mod-hist → Kafka `model_main_{idA}` → hydro-calc (поток A) → Head_A.
- Сессия B: mod-hist → Kafka `model_main_{idB}` → hydro-calc (поток B) → Head_B.
- Проверяем: данные A не попадают в поток B и наоборот.

**Обоснование:** MT1.LU1: Press = 5.0 → Head_A = (5.0/850)×101970 + H_A ≈ 663 + H_A;
MT1.LU2: Press = 7.0 → Head_B = (7.0/850)×101970 + H_B ≈ 840 + H_B
(формула — KB-CALC-FORMULA-001). Если Head_A = Head_B → перемешивание (баг).
Также проверяем: watermark каждой сессии независим.

## Предусловие
1. В CH: данные за 08:00–08:10 для MT1.LU1 (Press=5.0) и MT1.LU2 (Press=7.0).
2. maxSessions ≥ 2.
3. Конфигурация ТУ1 и ТУ2 загружена.
4. Hydro-calculation запущен.

## Действия
| Шаг | Действие | Щуп |
|---|---|---|
| 1 | `api.createHistorical({..., "targets":["MT1.LU1"]})` → `idA` | — |
| 2 | `api.createHistorical({..., "targets":["MT1.LU2"]})` → `idB` | — |
| 3 | `api.start(idA)` ⚠️ | SPOT_K4: START для idA |
| 4 | `api.start(idB)` ⚠️ | SPOT_K4: START для idB |
| 5 | `ws.wait_event(idA, 1, timeout=30)` | — |
| 6 | `ws.wait_event(idB, 1, timeout=30)` | — |
| 7 | `WAIT(65)` — 65с × 10× = 650с > 600с (обе завершаются) | — |
| 8 | `api.get(idA)` ⚠️ → `status = 8` | — |
| 9 | `api.get(idB)` ⚠️ → `status = 8` | — |
| 10 | **Kafka-проверка A:** `kafka.consume("model_main_" + idA, {"tag":"MT1.LU2.*"}, timeout=5)` | **SPOT_K2** |
| 11 | **Kafka-проверка B:** `kafka.consume("model_main_" + idB, {"tag":"MT1.LU1.*"}, timeout=5)` | **SPOT_K2** |
| 12 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `HeadA` | — |
| 13 | `hmi.get("MT1.LU2.SGLU1.KIP11.TI.Head")` → `HeadB` | — |
| 14 | `api.watermark(idA)` ⚠️ → `wmA` | SPOT_REDIS |
| 15 | `api.watermark(idB)` ⚠️ → `wmB` | SPOT_REDIS |

## Ожидаемый результат
| Шаг | Ожидание | Зачем этот шаг |
|---|---|---|
| 8, 9 | Обе DONE | Hydro-calc обработал оба потока |
| 10 | **Пусто** (нет тегов MT1.LU2 в топике A) | **Критично:** нет перемешивания |
| 11 | **Пусто** (нет тегов MT1.LU1 в топике B) | **Критично:** нет перемешивания |
| 12 | HeadA ≈ 663 + H_A | Расчёт по данным A |
| 13 | HeadB ≈ 840 + H_B | Расчёт по данным B |
| 14, 15 | wmA ≈ wmB (обе = targetTime) | Обе обработаны полностью |

## Teardown
`api.close(idA)` ⚠️ + `api.close(idB)` ⚠️ → `WAIT(5)` → `RESET()`.

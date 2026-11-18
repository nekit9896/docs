---
case_conflu: HY-SYS-051
title: "Моделирование: Press меняется на каждом шаге → напор меняется"
service: system-tests
group: new-scenarios
source: confluence/test-plan-of-system-tests.md#HY-SYS-051
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [KB-HM-TESTPLAN-001, KB-CALC-FORMULA-001]
status: verified
---

# HY-SYS-051 — Моделирование: Press меняется на каждом шаге → напор меняется

**Уровень:** SYS-1. **Участники:** mod-hist, hydro-calculation, hmi-backend (шлюз).

## Требование
_(будет дополнено — в источнике не заполнено)_

## Описание
Сценарий в моделировании: оператор моделирует постепенное повышение давления. На
каждом шаге (advance) он меняет Press, и hydro-calculation пересчитывает напор.
Ключевая проверка: напор меняется **согласованно** — если Press растёт, Head растёт.
Если на каком-то шаге Head «скачет» или не меняется — hydro-calc не пересчитал
(задержал старое значение, не прочитал новое из Kafka).

**Цепочка:**
1. Оператор (через hmi-backend, шлюз) задаёт Press = 5.0.
2. mod-hist: `advance(60)` → публикует в `model_main_{id}`.
3. hydro-calc: считает Head по Press=5.0 → Head_1.
4. Оператор задаёт Press = 5.5 → шаг advance → Head_2.
5. Оператор задаёт Press = 6.0 → шаг advance → Head_3.
6. Проверяем: Head_1 < Head_2 < Head_3 (монотонный рост).

**Обоснование:** Head = (P/ρ)×101970 + H (KB-CALC-FORMULA-001). P: 5.0 → 5.5 → 6.0,
ρ=850, H=63.5 → Head: 663.3 → 679.7 → 696.2 (рост ≈ 16.5 м на 0.5 кгс/см²).
Если Head не меняется между шагами → hydro-calc не обновил. Если Head «скачет»
(например, 663 → 750 → 680) → баг в расчёте или в чтении из Kafka.

## Предусловие
1. Сессия modelling запущена (status=3).
2. `[KIP].TI.Ro = 850`, `[KIP].Height = 63.5`; `[KIP].State.Disable = false`.
3. Hydro-calculation запущен.

## Действия
| Шаг | Действие | Щуп |
|---|---|---|
| 1 | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.0)` | SPOT_K2: Press=5.0 |
| 2 | `WAIT(5)` | — |
| 3 | `api.advance(id, 60)` ⚠️ | SPOT_K4 |
| 4 | `WAIT(5)` | — |
| 5 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `Head_1` | SPOT_WS |
| 6 | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 5.5)` | SPOT_K2 |
| 7 | `WAIT(5)` | — |
| 8 | `api.advance(id, 60)` ⚠️ | SPOT_K4 |
| 9 | `WAIT(5)` | — |
| 10 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `Head_2` | SPOT_WS |
| 11 | `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 6.0)` | SPOT_K2 |
| 12 | `WAIT(5)` | — |
| 13 | `api.advance(id, 60)` ⚠️ | SPOT_K4 |
| 14 | `WAIT(5)` | — |
| 15 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `Head_3` | SPOT_WS |
| 16 | **Проверка:** `Head_1 < Head_2 < Head_3` | — |
| 17 | **Проверка:** `Head_2 - Head_1 ≈ 16.4` (± 1) | — |
| 18 | **Проверка:** `Head_3 - Head_2 ≈ 16.4` (± 1) | — |

## Ожидаемый результат
| Шаг | Ожидание | Зачем этот шаг |
|---|---|---|
| 5 | Head_1 ≈ 663.3 | Базовый расчёт корректен |
| 10 | Head_2 ≈ 679.7 | Hydro-calc пересчитал по новому Press |
| 15 | Head_3 ≈ 696.2 | Hydro-calc пересчитал по новому Press |
| 16 | Монотонный рост | Согласованность: Press↑ → Head↑ |
| 17, 18 | Дельта ≈ 16.4 | Линейность: ΔP = 0.5 → ΔH ≈ 16.4 м |

## Teardown
`api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `WAIT(5)` → `RESET()`.

---
case_conflu: HY-SYS-052
title: "Timeshift: сравнение результатов с исходной сессией"
service: system-tests
group: new-scenarios
source: confluence/test-plan-of-system-tests.md#HY-SYS-052
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [KB-HM-TESTPLAN-001, KB-CALC-FORMULA-001, HY-SYS-043]
status: verified
---

# HY-SYS-052 — Timeshift: сравнение результатов с исходной сессией

**Уровень:** SYS-1. **Участники:** mod-hist (×2), hydro-calculation (×2 потока), ClickHouse.

## Требование
_(будет дополнено — в источнике не заполнено)_

## Описание
Timeshift — «что было бы, если бы контроль начался на 1 час раньше?». Берём
сохранённую сессию (A), сдвигаем время на −1 час, пересчитываем. Гидро-расчёт зависит
от начальных условий; если контроль начался раньше — начальные условия другие →
напоры другие. Ключевая проверка: данные действительно взяты из saved-сессии, и
hydro-calc **действительно пересчитал** (не скопировал результаты A).

**Цепочка:** сессия A (исходная): historical 14:00–16:00 → Head_A(t); сессия B
(timeshift): sourceMode=saved, shift=−3600 → данные A за 13:00–14:00 → Head_B(t).
Проверяем: (1) Head_B(t) ≠ Head_A(t) при неконстантных данных; (2) данные в
`model_main_{idB}` = данным saved-сессии A за сдвинутый период; (3) hydro-calc
рассчитал корректно.

**Обоснование:** исходная сессия A: 14:00–16:00, данные из CH; timeshift B:
shift=−3600, startTime=15:00 → берёт данные A за 14:00–15:00. Если
Head_B(t) = Head_A(t) для всех t → hydro-calc не пересчитал (скопировал). Если данные
в `model_main_{idB}` ≠ данным A за 14:00–15:00 → mod-hist взял неверные данные.
Если Head_B(t) ≠ Head_A(t) и данные совпадают → всё работает корректно.

## Предусловие
1. Сессия A: historical, 14:00–16:00, speedRatio=10000, завершена (DONE), сохранена (SAVED).
2. В сохранённых данных A: Press, Ro, QVmom за 14:00–16:00.
3. Конфигурация ТУ1 загружена; `[LU].State.Control = 1` (в данных A).

## Действия
| Шаг | Действие | Щуп |
|---|---|---|
| 1 | **Подготовка:** `api.createHistorical({"startTime":"...14:00:00Z","targetTime":"...16:00:00Z","speedRatio":10000,"targets":["MT1.LU1"]})` → `idA` | — |
| 2 | `api.start(idA)` ⚠️ → `WAIT(130)` → DONE | — |
| 3 | `api.save(idA)` ⚠️ → `WAIT(20)` → SAVED | SPOT_CH: данные в `saved_session_data` |
| 4 | **Создать timeshift:** `api.createTimeshift({"sourceMode":0,"sourceSessionId":"idA","startTime":"...15:00:00Z","shiftDuration":-3600,"speedRatio":10000,"targets":["MT1.LU1"]})` → `idB` | — |
| 5 | `api.start(idB)` ⚠️ | SPOT_K4: START для idB |
| 6 | `ws.wait_event(idB, 1, timeout=30)` | — |
| 7 | `WAIT(70)` — 70с × 10× = 700с > 3600с/10 = 360с (завершится) | — |
| 8 | `ws.wait_event(idB, 9, timeout=90)` — WATERMARK_COMPLETE | — |
| 9 | `api.get(idB)` ⚠️ → `status = 8` (DONE) | — |
| 10 | **Сравнение данных:** `kafka.consume("model_main_" + idB, {"tag":"*KIP1.TI.Press"}, timeout=10)` → `press_B` | **SPOT_K2** |
| 11 | **Сравнение с исходной:** `ch.query("SELECT value FROM saved_session_data WHERE session_id='idA' AND tag='*KIP1.TI.Press' AND ts BETWEEN '14:00' AND '15:00' LIMIT 5")` → `press_A` | **SPOT_CH** |
| 12 | **Проверка:** `press_B ≈ press_A` (данные взяты из saved-сессии) | — |
| 13 | `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` → `Head_B` | SPOT_WS |
| 14 | **Сравнение результатов:** из сессии A (сохранённые данные): `Head_A` (за тот же момент) | SPOT_CH |
| 15 | **Проверка:** `Head_B ≠ Head_A` (пересчитано, не скопировано) | — |
| 16 | **Проверка:** `Head_B` соответствует формуле: `(press_B / 850) × 101970 + 63.5` (KB-CALC-FORMULA-001) | — |

## Ожидаемый результат
| Шаг | Ожидание | Зачем этот шаг |
|---|---|---|
| 9 | DONE | Timeshift завершён |
| 12 | press_B ≈ press_A | **Критично:** данные взяты из saved-сессии A |
| 15 | Head_B ≠ Head_A | **Критично:** hydro-calc пересчитал (не скопировал) |
| 16 | Head_B = формула | Hydro-calc рассчитал корректно |

**Примечание:** `Head_B ≠ Head_A` — потому что граничные условия разные. Если Press за
14:00–15:00 в сессии A **константен** — Head_B может быть ≈ Head_A (в пределах
погрешности): проверяем `|Head_B − Head_A| < 1`. Если данные **не** константные —
`|Head_B − Head_A| > 1`.

## Teardown
`api.close(idB)` ⚠️ → `api.close(idA)` ⚠️ → `WAIT(5)` → `RESET()`.
Тайминг: ~4 мин.

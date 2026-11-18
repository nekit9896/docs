---
case_conflu: HY-SYS-050
title: "Race condition: pause + advance одновременно"
service: system-tests
group: new-scenarios
source: confluence/test-plan-of-system-tests.md#HY-SYS-050
requires: [KB-SYS-TESTSTAND-001, KB-SYS-TESTPLAN-001]
related: [KB-HM-TESTPLAN-001, KB-HM-WATERMARK-001]
status: verified
---

# HY-SYS-050 — Race condition: pause + advance одновременно

**Уровень:** SYS-1. **Участники:** mod-hist, hydro-calculation.

## Требование
_(будет дополнено — в источнике не заполнено)_

## Описание
Оператор может случайно нажать «Пауза» и «Продвинуть» одновременно (двойной клик,
lag UI). В mod-hist это две операции, меняющие состояние сессии. Если нет lock —
может произойти: (а) сессия «зависает» в промежуточном состоянии, (б) watermark
отскакивает назад, (в) сессия переходит в ERROR. Hydro-calculation при этом получает
contradictory команды (PAUSE + данные для advance) и должен отреагировать корректно.

**Цепочка:** параллельно (2 REST-запроса одновременно): Thread 1 — `api.pause(id)` ⚠️,
Thread 2 — `api.advance(id, 60)` ⚠️. Ожидаем: система обрабатывает без corruption.
Один запрос «выигрывает», другой получает 409 или игнорируется. Watermark не
отскакивает назад. Sess не переходит в ERROR.

**Обоснование:** watermark — монотонная величина (G18): если pause «откатил»
watermark, а advance его продвинул — итоговое значение должно быть ≥ исходного.
Status должен быть 2 (PAUSED) или 3 (PLAYING). Не 12 (ERROR). Если hydro-calc получил
PAUSE и сразу данные — он должен их проигнорировать (не считает в паузе).

## Предусловие
1. Сессия modelling запущена (status=3), `watermark = 09:00:00`.
2. Hydro-calculation запущен, подписан на `model_main_{id}`.

## Действия
| Шаг | Действие | Щуп |
|---|---|---|
| 1 | `api.watermark(id)` ⚠️ → `wm_before` | SPOT_REDIS |
| 2 | **Параллельно:** `api.pause(id)` ⚠️ + `api.advance(id, 60)` ⚠️ | SPOT_K4: PAUSE/SET_WATERMARK в `mod-hist-commands` |
| 3 | `WAIT(5)` | — |
| 4 | `api.get(id)` ⚠️ → `status` | — |
| 5 | `api.watermark(id)` ⚠️ → `wm_after` | SPOT_REDIS |
| 6 | **Проверка:** `status ∈ {2, 3}` (не 12, не 1) | — |
| 7 | **Проверка:** `wm_after ≥ wm_before` | — |
| 8 | Если status=3: `WAIT(5)` → `api.watermark(id)` → должен двигаться | — |
| 9 | Если status=2: `api.resume(id)` ⚠️ → `WAIT(5)` → `api.watermark(id)` → должен двигаться | — |
| 10 | **Kafka:** `kafka.consume("model_main_" + id, timeout=10)` → нет «битых» сообщений | SPOT_K2 |

## Ожидаемый результат
| Шаг | Ожидание | Зачем этот шаг |
|---|---|---|
| 4 | status = 2 или 3 | Сессия в корректном состоянии |
| 5 | wm_after ≥ wm_before | Watermark не отскочил |
| 8/9 | Watermark двигается | Сессия не зависла |
| 10 | Нет битых сообщений | Hydro-calc не получил contradicting data |

## Teardown
Если status=2 → `api.resume(id)` ⚠️. `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ →
`WAIT(5)` → `RESET()`.

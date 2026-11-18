---
case_conflu: HY-CALC-008
title: "Режим контроля перехода (TransitionControlOn)"
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-008
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-005, HY-CALC-013, HY-CALC-030]
status: needs-review
---

# HY-CALC-008 — Режим контроля перехода (TransitionControlOn)

> `needs-review`: тег `LU1_TU_TRANSITIONCONTROLON` — **допущение** (№9 тест-плана).
> В коде механизм перехода в Control=2 реализован в `LuControlSetAlg` (при
> определённых условиях Control устанавливается в 2 вместо 1). Точный триггер
> уточняется.

**Требование:** R-HYDR-024
**Описание:** После остановки и перезапуска перекачки давления не стабилизируются
сразу. Режим перехода (Control=2) фиксирует новую точку отсчёта, но подавляет
большинство алармов. **Критическая особенность:** `AlmDevHeadCarrier` НЕ
подавляется даже при Control=2 — это последний рубеж защиты.

**Что происходит при TransitionControlOn:**

| Параметр | Значение |
|---|---|
| `LU1_CONTROL` | 2 |
| `LU1_INDICATORCONTROL` | 5 |
| `KIP1_PRESSSTATION` | Зафиксировано |
| `UR1_QVMOMSTATION` | Зафиксировано |
| Алармы давления (AlmDevMax/MinRange) | **НЕ генерируются** |
| Алармы расхода (AlmQVmomRange) | **НЕ генерируются** |
| Аларм дебаланса (AlmDevQmom) | **НЕ генерируется** |
| Аларм скорости (AlmRateLimitPress) | **НЕ генерируется** |
| `LU1_ALMDEVHEADCARRIER` | **Генерируется** (не подавляется) |

**Предусловие:**

- `LU1_CONTROL = 0`
- Конфигурация ТУ загружена, давления нестабильны (переходный процесс)
- `KIP1_PRESS = 5.0`, `KIP1_RO = 850`, `KIP1_HEIGHT = 63.5`
- `LU1_CARRIERHEADDEF[km_75] = 793.6 м` (несущая для данного км)
- `KIP1_HEAD = 663.2 м` (ниже несущей — штатно)

**Действия:**

1. `hmi.set("MT1.LU1.TU.TransitionControlOn", true)`
2. `WAIT(event)`
3. Проверить `LU1_CONTROL`, `LU1_INDICATORCONTROL`
4. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 7.0)` — повысить давление (но ниже несущей)
5. `WAIT(event)`
6. Проверить: `KIP1_ALMDEVMAXRANGE` — должен быть false (подавлен)
7. Проверить: `LU1_ALMDEVHEADCARRIER` — должен быть false (Head < несущей)

**Ожидаемый результат:**

1. `LU1_CONTROL = 2`
2. `LU1_INDICATORCONTROL = 5`
3. `KIP1_PRESSSTATION`, `UR1_QVMOMSTATION` зафиксированы
4. При Press = 7.0 (выше базового, вне диапазона): `KIP1_ALMDEVMAXRANGE = false` (подавлен)
5. `LU1_ALMDEVHEADCARRIER = false` (напор 739.3 м < несущей 793.6 м)
6. Алармы дебаланса, скорости — не генерируются

**Дополнительные проверки (переходы из Control=2):**

| # | Действие | Ожидаемое |
|---|---|---|
| A | `hmi.set("MT1.LU1.TU.SetControlOff", true)` при Control=2 | `LU1_CONTROL = 0`. Базовые значения → invalid |
| B | `hmi.set("MT1.LU1.TU.SetControlOn", true)` при Control=2 | **Определить фактическое поведение**: Control=1 (повторная постановка) или игнор. Зафиксировать |
| C | `hmi.set("MT1.LU1.TU.TransitionControlOn", true)` повторно при Control=2 | Игнор (уже в режиме перехода) или сброс базовых. Зафиксировать |

**Примечание:** Точное поведение переходов из Control=2 определяется при первом
прогоне и уточняется у коллег. Критерий: система не уходит в неопределённое состояние.

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-005
title: Расчёт диапазона давления при постановке на контроль
service: hydro-calculation
group: base-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-005
requires: [KB-CALC-ALGO-LU-CTRL-001, KB-CALC-STATE-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-006, HY-CALC-007, HY-CALC-009, HY-CALC-014, HY-CALC-015]
status: verified
---

# HY-CALC-005 — Расчёт диапазона давления при постановке на контроль

**Требование:** R-HYDR-022, R-HYDR-006
**Описание:** Диспетчер фиксирует текущее состояние ТУ как базовое. После этого
система сравнивает живые данные с базовыми и генерирует алармы при отклонениях.
До постановки — пассивный мониторинг, после — активный контроль.

**Формулы:**

```
PressStation = фактическое давление в момент постановки
PressRangeMax = PressStation + PressDeltaRangeMax
PressRangeMin = PressStation − PressDeltaRangeMin
```

**Обоснование выбора значений:**

- `PressDeltaRangeMax = 0.2 МПа` — типичное значение из ИМ для данного ТУ. Демонстрационное: достаточно для визуализации на графике, но не настолько большое, чтобы пропустить реальную утечку
- `PressDeltaRangeMin = 0.1 МПа` — асимметрия осознанная: давление ниже базового опаснее (кавитация, воздух), поэтому нижняя граница уже
- P = 5.0 МПа — стабильное рабочее давление
- Расчёт: `RangeMax = 5.0 + 0.2 = 5.2`, `RangeMin = 5.0 − 0.1 = 4.9`

**Полный список выходных параметров при постановке:**

| Тег | Описание | Ожидаемое |
|---|---|---|
| `LU1_CONTROL` | Состояние контроля | 1 |
| `KIP1_PRESSSTATION` | Базовое давление | 5.0 МПа |
| `UR1_QVMOMSTATION` | Базовый расход | Зафиксировано (текущее значение UR1) |
| `LU1_GRAVITYSEGSREG` | Слепок самотеков | Копия текущего `LU1_GRAVITYSEGS` |
| `SGLU1_CONTROLON` | Сегмент на контроле | true |
| `KIP1_PRESSRANGEMAX` | Верхняя граница | 5.2 МПа |
| `KIP1_PRESSRANGEMIN` | Нижняя граница | 4.9 МПа |
| `LU1_TU_SETCONTROLON` | Команда сброшена | false |

**Предусловие:**

- `LU1_CONTROL = 0`
- `KIP1_PRESS = 5.0` МПа (стабильно)
- `KIP1_PRESSDELTARANGEMAX = 0.2` (из ИМ)
- `KIP1_PRESSDELTARANGEMIN = 0.1` (из ИМ)
- `UR1_QVMOM = 120.0` м³/ч
- `LU1_GRAVITYSEGS` заполнен (конфигурация ТУ рассчитана)
- `SGLU1_CONTROLON = false`
- `LU1_TU_SETCONTROLON = false`

**Действия:**

1. `hmi.set("MT1.LU1.TU.SetControlOn", true)` — команда постановки на контроль
2. `WAIT(event)` — LuControlSetAlg срабатывает
3. `hmi.get(...)` — проверить все выходные теги

**Ожидаемый результат:**

1. `LU1_CONTROL = 1`
2. `KIP1_PRESSSTATION = 5.0` (зафиксировано)
3. `UR1_QVMOMSTATION = 120.0` (зафиксировано)
4. `LU1_GRAVITYSEGSREG = копия LU1_GRAVITYSEGS`
5. `SGLU1_CONTROLON = true`
6. `LU1_TU_SETCONTROLON = false` (сброшен)
7. `KIP1_PRESSRANGEMAX = 5.2 МПа`
8. `KIP1_PRESSRANGEMIN = 4.9 МПа`

**Teardown:** `hmi.set("MT1.LU1.TU.SetControlOff", true)` → `WAIT(event)` → `RESET()`
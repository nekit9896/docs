---
case_conflu: HY-CALC-047
title: "Видимость сегмента"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-047
requires: [KB-CALC-ALGO-SGLU-UR-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-045, HY-CALC-046, HY-CALC-083]
status: verified
---

# HY-CALC-047 — Видимость сегмента

**Требование:** R-HYDR-040
**Описание:** На участках с лупингом (две параллельные нитки) отображается
только приоритетный сегмент. Priority=0 (подкачка) всегда скрыт.

**Формула:**

```
Priority = 0 → Visible = false (всегда)
Priority > 0:
  Visible = (ControlOn = false AND Activity = true) OR (ControlOn = true AND Priority = 1)
```

**Таблица всех комбинаций:**

| Priority | ControlOn | Activity | Visible | Пояснение |
|---|---|---|---|---|
| 0 | любое | любое | **false** | Подкачка всегда скрыта |
| 1 | true | любое | **true** | Лупинг на контроле — виден |
| 1 | false | true | **true** | Лупинг без контроля, но активен — виден |
| 1 | false | false | **false** | Неактивен и без контроля — скрыт |
| 2 | true | любое | **false** | Приоритет ≠ 1 и на контроле — скрыт |

**Предусловие:**

- `SGLU1_PRIORITY = 1` (лупинг)
- `SGLU2_PRIORITY = 0` (подкачка)

**Действия (проверка всех строк таблицы):**

| Шаг | Настройка | Ожидаемый Visible |
|---|---|---|
| 1 | SGLU1: Priority=1, ControlOn=true, Activity=true | **true** |
| 2 | SGLU1: Priority=1, ControlOn=false, Activity=true | **true** |
| 3 | SGLU1: Priority=1, ControlOn=false, Activity=false | **false** |
| 4 | SGLU2: Priority=0, ControlOn=true, Activity=true | **false** |

**Ожидаемый результат:**

- Каждый шаг даёт соответствующее `SGLU_VISIBLE`

**Teardown:** `RESET()`
---
case_conflu: HY-CALC-018
title: "Аларм давления не генерируется при отключённом датчике"
service: hydro-calculation
group: pressure-alarms
source: confluence/test-plan-hydro-calculation.md#HY-CALC-018
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-SIDEFX-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-014, HY-CALC-017, HY-CALC-040, HY-CALC-041]
status: verified
---

# HY-CALC-018 — Аларм давления не генерируется при отключённом датчике

**Требование:** R-HYDR-028, R-HYDR-043
**Описание:** Отключённый датчик (`Disable = true`) не участвует в генерации
алармов давления. Дополнительно: `KipAlarmsAlg` проверяет противоречие
Disable/invalid → `AlmFailOn`.

**Два варианта AlmFailOn:**

| Disable | invalid | AlmFailOn | Пояснение |
|---|---|---|---|
| true | false | **true** | Противоречие: отключён, но получает валидные данные (ошибка конфигурации) |
| true | true | **false** | Штатно: отключён и данных нет |
| false | true | **true** | Сигнал пропал (обрыв, ошибка АЦП) |
| false | false | **false** | Штатная работа |

**Предусловие:**

- `LU1_CONTROL = 1`
- `SGLU1_CONTROLON = true`
- `KIP1_DISABLE = true` (отключён)
- `KIP1_PRESS = 5.5` (приходит, валидный — противоречие)

**Действия:**

1. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")` — проверить, что аларма давления нет
2. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")` — проверить диагностический
3. `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", false)` — восстановить
4. `WAIT(event)`
5. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmDevMaxRange")` — теперь должен быть (5.5 > 5.2)
6. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")`

**Ожидаемый результат:**

- Шаг 1: `KIP1_ALMDEVMAXRANGE = false` (датчик отключён, не участвует)
- Шаг 2: `KIP1_ALMFAILON = true` (Disable=true, invalid=false → противоречие)
- Шаг 5: `KIP1_ALMDEVMAXRANGE = true` (датчик активен, 5.5 > 5.2)
- Шаг 6: `KIP1_ALMFAILON = false` (противоречие устранено)

**Teardown:** `RESET()`
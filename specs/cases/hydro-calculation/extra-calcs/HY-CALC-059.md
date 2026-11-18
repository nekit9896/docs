---
case_conflu: HY-CALC-059
title: "Самотеки: проверка алармов в топике alarm"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-059
requires: [KB-CALC-SIDEFX-001, KB-CALC-ALGO-LU-GRAV-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-038, HY-CALC-039, HY-CALC-058]
status: verified
---

# HY-CALC-059 — Самотеки: проверка алармов в топике alarm

**Требование:** R-HYDR-035
**Описание:** E2E-проверка алармов самотеков в топике `alarm`.

**Три аларма:**

| Тег | Описание |
|---|---|
| `LU1_ALMGRAVITY` | Обнаружен самотечный сегмент |
| `LU1_ALMGRAVITYPOSSIBLE` | Риск перехода в самотёк |
| `KIP1_ALMGRAVITYPOSSIBLE` | Напор на конкретном датчике близок к конфигурации |

**Предусловие:**

- Конфигурация ТУ1: пик км 65, H = 400 м (как в HY-CALC-038)
- KIP1 (км 50): Press = 3.0 (Head = 722 > 400)
- KIP2 (км 80): Press = 0.5 (Head = 359.9 < 400)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 3.0)`
2. `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.5)`
3. `WAIT(event)`
4. `hmi.wait_alarm("MT1.LU1.Alm.AlmGravity", timeout=10s)` — подтвердить доставку
5. `hmi.history("MT1.LU1.Alm.AlmGravity", from=ts_start, to=ts_now)` — проверить: value=true, text содержит «самотечный», «перевальная точка»

**Ожидаемый результат:**

- `hmi.wait_alarm` подтверждает value=true
- `hmi.history` возвращает: value=true, text содержит «самотечный участок км 50–80, перевальная точка на км 65»

**Teardown:** `RESET()`
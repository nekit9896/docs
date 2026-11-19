---
case_conflu: HY-CALC-069
title: "Расширение: самотёки — плато на конфигурации ТУ"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-069
requires: [KB-CALC-ALGO-LU-GRAV-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-038, HY-CALC-039]
status: verified
---

# HY-CALC-069 — Расширение: самотёки — плато на конфигурации ТУ

**Требование:** R-HYDR-018
**Описание:** На конфигурации ТУ может быть плато (несколько точек с одинаковой
высотой). Алгоритм должен корректно обрабатывать: перевальная точка — не одна, а
диапазон.

**Логика:**

```
Плато: точки (50, 400), (60, 400), (70, 400) — все с H = 400
Перевальная точка: не одна координата, а диапазон [50, 70]
Сегмент самотечный, если Head < 400 на любом участке плато
```

**Предусловие:**

- Конфигурация: `LU_KM = [0, 50, 60, 70, 80, 100]`, `LU_HEIGHT = [300, 400, 400, 400, 300, 280]`
- Плато: км 50–70, H = 400
- KIP1 (км 40): Press = 3.0 → Head = 722 (высоко)
- KIP2 (км 80): Press = 0.5 → Head = 359.9 (< 400 → самотек)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 3.0)`
2. `hmi.set("MT1.LU1.SGLU2.KIP2.TI.Press", 0.5)`
3. `WAIT(event)`
4. `hmi.get("MT1.LU1.Alm.AlmGravity")`
5. `hmi.get("MT1.LU1.TI.PassPoints")`
6. `hmi.get("MT1.LU1.TI.GravitySegs")`

**Ожидаемый результат:**

- `LU1_ALMGRAVITY = true`
- `LU1_PASSPOINTS` содержит диапазон или точку плато: [50] или [50, 60, 70] (зависит от реализации)
- `LU1_GRAVITYSEGS = ["40,80"]` или ["50,80"] (сегмент ниже плато)

**Teardown:** `RESET()`
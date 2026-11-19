---
case_conflu: HY-CALC-061
title: "Видимость датчика (KipVisibleAlg)"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-061
requires: [KB-CALC-ALGO-KIP-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-047, HY-CALC-060]
status: verified
---

# HY-CALC-061 — Видимость датчика (KipVisibleAlg)

**Требование:** R-HYDR-041
**Описание:** Датчик видим, если:

1. `Disable = false` (не отключён)
2. Родительский SGLU видим (`SGLU_VISIBLE = true`)

Если датчик отключён **или** сегмент скрыт — датчик невидим.

**Формула:**

```
KIP_VISIBLE = (KIP_DISABLE = false) AND (SGLU_VISIBLE = true)
```

**Предусловие:**

- `KIP1_DISABLE = false`
- `SGLU1_VISIBLE = true`
- `KIP1_VISIBLE = true` (штатно)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", true)` — отключить датчик
2. `WAIT(event)`
3. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")`
4. `hmi.set("MT1.LU1.SGLU1.KIP1.State.Disable", false)` — включить
5. `WAIT(event)`
6. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")`
7. `hmi.set("MT1.LU1.SGLU1.State.Visible", false)` — скрыть сегмент
8. `WAIT(event)`
9. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")`
10. `hmi.set("MT1.LU1.SGLU1.State.Visible", true)` — показать сегмент
11. `WAIT(event)`
12. `hmi.get("MT1.LU1.SGLU1.KIP1.State.Visible")`

**Ожидаемый результат:**

- Шаг 3: `KIP1_VISIBLE = false` (отключён)
- Шаг 6: `KIP1_VISIBLE = true` (включён, сегмент видим)
- Шаг 9: `KIP1_VISIBLE = false` (сегмент скрыт)
- Шаг 12: `KIP1_VISIBLE = true` (всё штатно)

**Teardown:** `RESET()`
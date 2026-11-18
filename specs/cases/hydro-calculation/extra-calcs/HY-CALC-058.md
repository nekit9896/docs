---
case_conflu: HY-CALC-058
title: "Дебаланс: проверка алармов в топике alarm"
service: hydro-calculation
group: extra-calcs
source: confluence/test-plan-hydro-calculation.md#HY-CALC-058
requires: [KB-CALC-SIDEFX-001, KB-CALC-ALGO-LU-DATA-001, KB-CALC-TESTSTAND-001]
related: [HY-CALC-020, HY-CALC-059, HY-CALC-070]
status: verified
---

# HY-CALC-058 — Дебаланс: проверка алармов в топике alarm

**Требование:** R-HYDR-033
**Описание:** E2E-проверка: алармы дебаланса записаны в топик Kafka `alarm` с
правильным форматом.

**Формат события:**

```json
{
  "tag": "MT1.LU1.Alm.AlmDevQmom",
  "ts": 1700000000000,
  "value": true,
  "text": "Дебаланс расходов превышает допустимый: 2.0 м³/ч при лимите ±1.5 м³/ч",
  "priority": "WARNING",
  "state": "ACTIVE"
}
```

**Четыре аларма дебаланса:**

| Тег | Описание |
|---|---|
| `LU1_ALMDEVQMOM` | Мгновенный |
| `LU1_ALMDEVQAVG` | Средний за час |
| `LU1_ALMDEVQAVGSTATION` | Стационарный средний |
| `LU1_ALMDEVQAVGSTATION2` | Стационарный мгновенный |

**Предусловие:**

- `LU1_CONTROL = 1`
- `LU1_DIFFQMOMLIMITMAX = 1.5`, `LU1_DIFFQMOMLIMITMIN = −1.5`
- UR1 (выходной): QVmom = 120.0
- UR2 (входной): QVmom = 122.0

**Действия:**

1. `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 122.0)`
2. `WAIT(60c)`
3. `hmi.wait_alarm("MT1.LU1.Alm.AlmDevQmom", timeout=30s)` — подтвердить доставку
4. `hmi.history("MT1.LU1.Alm.AlmDevQmom", from=ts_start, to=ts_now)` — проверить полный формат (value, text, priority, state)
5. `hmi.set("MT1.LU1.SGLU2.UR2.TI.QVmom", 120.3)`
6. `WAIT(60c)`
7. `hmi.wait_alarm("MT1.LU1.Alm.AlmDevQmom", timeout=30s)` — подтвердить сброс
8. `hmi.history("MT1.LU1.Alm.AlmDevQmom", from=ts_start, to=ts_now)` — проверить: value=false, state="CLEARED"

**Ожидаемый результат:**

- Шаг 3: `hmi.wait_alarm` подтверждает value=true
- Шаг 4: `hmi.history` возвращает: value=true, priority="WARNING", state="ACTIVE", text содержит «2.0 м³/ч», «±1.5»
- Шаг 7: `hmi.wait_alarm` подтверждает value=false (сброс)
- Шаг 8: `hmi.history` возвращает: value=false, state="CLEARED"

**Teardown:** `RESET()`
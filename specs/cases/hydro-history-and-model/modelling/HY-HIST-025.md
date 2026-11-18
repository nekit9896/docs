---
case_conflu: HY-HIST-025
title: modelling: невалидные данные (invalid=true)
service: hydro-history-and-model
group: modelling
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-025
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-CALC-FORMULA-001]
related: [HY-HIST-021, HY-CALC-004]
status: verified
---

# HY-HIST-025 — modelling: невалидные данные (invalid=true)

**Требование:** R-HYDR-064
**Описание:** Оператор записывает значение с флагом `invalid = true` (имитация
сбоя датчика). Hydro-calculation реагирует как в реальном времени: напор помечен
как invalid, алармы по несущей не срабатывают, но `AlmFailOn` (неисправность
датчика) — срабатывает.

**Причинно-следственная связь:** В hydro-calculation (KB-CALC-FORMULA-001): если
`invalid = true` → `Head.invalid = true`. В логике алармов: `invalid = true` →
алармы по давлению/напору **не генерируются**, но `AlmFailOn = true`. Оператор
видит «датчик сломан», но не получает ложных алармов по несущей.

**Предусловие:**

- Сессия modelling запущена
- До этого Press = 7.0 (валидное), Head = 903.3 м (валидный)
- `[KIP].State.Disable = false` (датчик не отключён)

**Действия:**

1. `hmi.set("MT1.LU1.SGLU1.KIP1.TI.Press", 7.0, invalid=true)` ⚠️ — то же
   значение (7.0) с флагом invalid=true; hydro-calculation получит
   `{tag, value:7.0, invalid:true}`
2. `WAIT(5)` — публикация в Kafka → расчёт → запись в `model_main_{id}` →
   доступность через hmi-backend
3. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️ — значение рассчитано по формуле,
   НО `invalid = true` (7.0/850)×101970 + 63.5 = 903.3, но помечено невалидным
4. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmFailOn")` ⚠️ — ожидаем `AlmFailOn = true`
   (логика: `Disable=false AND invalid=true → AlmFailOn=true`)
5. `hmi.get("MT1.LU1.SGLU1.KIP1.Alm.AlmHighOn")` ⚠️ _(если существует)_ —
   **не сработал** (false): `invalid=true` блокирует генерацию алармов по значению

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 3 | `Head.value ≈ 903.3`, `Head.invalid = true` | Рассчитан, но помечен невалидным |
| 4 | `AlmFailOn = true` | Датчик «неисправен» |
| 5 | `AlmHighOn = false` (или не сработал) | Алармы по значению заблокированы invalid |

**Примечание:** Если `AlmHighOn` не существует как отдельный тег — проверяем
через `model_alarm_{id}`: в Kafka не должно быть аларма по несущей за этот момент.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

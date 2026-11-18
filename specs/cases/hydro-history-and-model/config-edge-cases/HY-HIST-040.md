---
case_conflu: HY-HIST-040
title: Список сессий: фильтрация
service: hydro-history-and-model
group: config-edge-cases
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-040
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-041, HY-HIST-001]
status: verified
---

# HY-HIST-040 — Список сессий: фильтрация

**Требование:** R-HYDR-074
**Описание:** `api.list` ⚠️ поддерживает фильтрацию по `status`,
`processingMode`, `targets`. Проверяем каждую комбинацию фильтров и их пересечение.

**Предусловие:** Созданы 3 сессии с разными параметрами:

- **S1:** `processingMode = 0` (historical), `status = 3` (PLAYING), `targets = ["MT1.LU1"]`
- **S2:** `processingMode = 1` (modelling), `status = 2` (PAUSED), `targets = ["MT1.LU2"]`
- **S3:** `processingMode = 2` (timeshift), `status = 8` (DONE), `targets = ["MT1.LU1"]`

**Действия:**

1. `api.list({status: 3})` ⚠️ — только PLAYING: S1. S2 (PAUSED=2) и S3 (DONE=8) отфильтрованы
2. `api.list({processingMode: 1})` ⚠️ — только modelling: S2
3. `api.list({status: 3, processingMode: 0})` ⚠️ — пересечение: S1
4. `api.list({targets: "MT1.LU1"})` ⚠️ — с MT1.LU1: S1 и S3
5. `api.list({})` ⚠️ — без фильтров: S1, S2, S3 (3 сессии)
6. `api.list({status: 3, processingMode: 2})` ⚠️ — пустое пересечение (PLAYING + timeshift): пустой массив
7. `api.list({status: 99})` ⚠️ — невалидный статус: пустой массив (не 500)

**Ожидаемый результат:**

| Шаг | Фильтр | Ожидаемый результат | Кол-во |
|---|---|---|---|
| 1 | status=3 | S1 | 1 |
| 2 | processingMode=1 | S2 | 1 |
| 3 | status=3, mode=0 | S1 | 1 |
| 4 | targets="MT1.LU1" | S1, S3 | 2 |
| 5 | (без фильтров) | S1, S2, S3 | 3 |
| 6 | status=3, mode=2 | (пусто) | 0 |
| 7 | status=99 | (пусто) | 0 |

**Teardown:** `api.stop` ⚠️ + `api.close` ⚠️ для всех 3 → `RESET()`

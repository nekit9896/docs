---
case_conflu: HY-HIST-029
title: Импорт: превышение максимального размера
service: hydro-history-and-model
group: import
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-029
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-028, HY-HIST-026]
status: verified
---

# HY-HIST-029 — Импорт: превышение максимального размера

**Требование:** R-HYDR-067
**Описание:** Файл импорта превышает `maxImportSize = 50 МБ`
(KB-HM-TESTSTAND-001). Система отклоняет с 413 (Payload Too Large). Сессия не
повреждена.

**Предусловие:**

- Сессия modelling создана (status = 0)
- Подготовлен файл размером 51 МБ (XLSX с миллионами строк)

**Действия:**

1. `api.import_(id, file=huge_file.xlsx)` ⚠️ _(51 МБ)_ — сервер отклоняет **до**
   парсинга (по размеру), не тратя ресурсы на разбор 51 МБ
2. `api.get(id)` ⚠️ — сессия не повреждена, status = 0

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 1 | HTTP 413, `{"error":"File exceeds maximum size (50 MB)"}` | Превышен лимит |
| 2 | `status = 0` (CREATED) | Не повреждена |

**Teardown:** `api.close(id)` ⚠️ → `RESET()`

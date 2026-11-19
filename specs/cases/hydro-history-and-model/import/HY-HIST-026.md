---
case_conflu: HY-HIST-026
title: Импорт XLSX (modelling)
service: hydro-history-and-model
group: import
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-026
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-CALC-FORMULA-001]
related: [HY-HIST-027, HY-HIST-028, HY-HIST-021]
status: verified
---

# HY-HIST-026 — Импорт XLSX (modelling)

**Требование:** R-HYDR-066
**Описание:** Оператор загружает XLSX-файл с временной шкалой входных параметров
для моделирования. Файл содержит 1 тег (Press) и 3 временных точки. После импорта
данные попадают в буфер сессии. При последующем `advance` система подставляет
значения из буфера по таймстампам и публикует в `model_main_{id}`.

**Формат XLSX (один лист):**

| tag | timestamp | value | invalid |
|---|---|---|---|
| MT1.LU1.SGLU1.KIP1.TI.Press | 2026-11-09T09:00:00Z | 5.0 | false |
| MT1.LU1.SGLU1.KIP1.TI.Press | 2026-11-09T09:01:00Z | 5.1 | false |
| MT1.LU1.SGLU1.KIP1.TI.Press | 2026-11-09T09:02:00Z | 5.2 | false |

**Причинно-следственная связь:** Импорт — способ загрузить «сценарий». После
импорта сессия получает статус IMPORTED (7) — данные в буфере, готовы к
использованию.

**Предусловие:**

- Сессия modelling создана (status = 0, CREATED), **не запущена**
- XLSX-файл подготовлен (3 строки данных, 1 тег)
- Конфигурация ТУ1 загружена

**Действия:**

1. `api.import_(id, file=import.xlsx)` ⚠️ — multipart/form-data. Система:
   парсит файл, валидирует формат (колонки: tag, timestamp, value, invalid),
   сохраняет данные в буфер (Redis/память), меняет статус сессии на IMPORTED (7)
2. `WAIT(5)` — парсинг и запись в буфер
3. `api.get(id)` ⚠️ — `status = 7` (IMPORTED); поле `importStatus` (или
   аналогичное): `2` (DONE по HistoryImportStatus)
4. `api.start(id)` ⚠️ — CREATED → OPENING → PLAYING
5. `ws.wait_event(id, 1, timeout=30)` — SESSION_OPENED
6. `api.advance(id, 120)` ⚠️ — взять из буфера значения с ts ≤ 09:02:00 (все 3),
   опубликовать в `model_main_{id}`. VirtualTime: 09:00 → 09:02
7. `WAIT(5)` — публикация, расчёт hydro-calculation
8. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Press")` ⚠️ — `5.2` (последнее значение в
   диапазоне 09:00–09:02)
9. `hmi.get("MT1.LU1.SGLU1.KIP1.TI.Head")` ⚠️ — Head = (5.2/850)×101970 + 63.5 =
   623.8 + 63.5 = **687.3 м**

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 3 | `status = 7` (IMPORTED) | Импорт завершён, данные в буфере |
| 6 | HTTP 200 | Advance принят |
| 8 | `Press = 5.2` | Последнее значение из файла |
| 9 | `Head ≈ 687.3 м` | Рассчитано по импортированному Press |

**Примечание:** Если advance на 120 с публикует все 3 сообщения одновременно (а
не по одному на минуту) — допустимо. Главное: итоговое значение = 5.2, и в
`model_main_{id}` есть 3 сообщения с ts 09:00, 09:01, 09:02.

**Teardown:** `api.stop(id)` ⚠️ → `api.close(id)` ⚠️ → `RESET()`

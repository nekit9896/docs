---
case_conflu: HY-HIST-027
title: Импорт ZIP_CSV (historical)
service: hydro-history-and-model
group: import
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-027
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001, KB-HM-ZIP-001]
related: [HY-HIST-026, HY-HIST-028, HY-HIST-048]
status: verified
---

# HY-HIST-027 — Импорт ZIP_CSV (historical)

**Требование:** R-HYDR-066
**Описание:** Импорт ZIP_CSV для historical-сессии. ZIP содержит CSV-файлы с
историческими данными (внешний инструмент/резервная копия/спец-версия). Данные
заменяют (или дополняют) данные ClickHouse.

**Формат ZIP:**

```text
import.zip
├── MT1_LU1_KIP1_Press.csv
│   tag,timestamp,value,invalid
│   MT1.LU1.SGLU1.KIP1.TI.Press,2026-11-09T08:00:00Z,5.0,false
│   MT1.LU1.SGLU1.KIP1.TI.Press,2026-11-09T08:00:01Z,5.01,false
│   ...
├── MT1_LU1_UR1_QVmom.csv
│   tag,timestamp,value,invalid
│   MT1.LU1.UR1.TI.QVmom,2026-11-09T08:00:00Z,120.0,false
│   ...
```

**Предусловие:**

- Сессия historical создана (status = 0), период 08:00–08:05, speedRatio = 10000
- ZIP-файл подготовлен (2 CSV: Press и QVmom, по 5 строк)
- В ClickHouse данные **отсутствуют** за этот период (чтобы убедиться, что
  используются именно импортированные)

**Действия:**

1. `api.import_(id, file=import.zip, format="ZIP_CSV")` ⚠️ — распаковка, парсинг
   каждого CSV, валидация (колонки, формат ts, числовые значения), сохранение в
   буфер. Статус сессии → IMPORTED (7)
2. `WAIT(10)` — распаковка ZIP, парсинг 2 CSV, запись в буфер/БД
3. `api.get(id)` ⚠️ — `status = 7` (IMPORTED); поле `importedTags` (или
   аналогичное): `["MT1.LU1.SGLU1.KIP1.TI.Press", "MT1.LU1.UR1.TI.QVmom"]`
4. `api.start(id)` ⚠️ — система использует данные из импорта вместо CH
5. `ws.wait_event(id, 1, timeout=30)`
6. `WAIT(40)` — 40 с × 10× = 400 с виртуального > 300 с (5 мин = весь диапазон)
7. `ws.wait_event(id, 9, timeout=60)` — WATERMARK_COMPLETE
8. `api.get(id)` ⚠️ — финальный статус и количество обработанных сообщений

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 3 | `status = 7` (IMPORTED), 2 тега | Импорт успешен |
| 7 | WATERMARK_COMPLETE | Сессия завершена |
| 8 | `status = 8` (DONE), `messagesProcessed ≈ 10` | 5 строк Press + 5 строк QVmom |

**Примечание:** _(Допущение: импорт заменяет данные из CH. Если реализация
смешивает — уточнить. В тесте CH пуст, поэтому результат одинаков.)_

**Teardown:** `api.close(id)` ⚠️ → `RESET()`

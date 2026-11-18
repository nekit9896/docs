---
case_conflu: HY-HIST-030
title: Экспорт результатов в CSV
service: hydro-history-and-model
group: export
source: confluence/test-plan-hydro-history-and-model.md#HY-HIST-030
requires: [KB-HM-TESTSTAND-001, KB-HM-TESTPLAN-001]
related: [HY-HIST-031, HY-HIST-032, HY-HIST-014]
status: verified
---

# HY-HIST-030 — Экспорт результатов в CSV

**Требование:** R-HYDR-068
**Описание:** После завершения historical-сессии оператор экспортирует расчётные
результаты в CSV. Файл содержит все рассчитанные значения (напоры, перепады,
расход) за период сессии. Формат: стандартный CSV с заголовком.

**Формат CSV (результат):**

```csv
tag,timestamp,value,invalid
MT1.LU1.SGLU1.KIP1.TI.Head,2026-11-09T08:00:00Z,663.2,false
MT1.LU1.SGLU1.KIP1.TI.Head,2026-11-09T08:00:01Z,663.3,false
MT1.LU1.SGLU1.KIP1.TI.PressDelta,2026-11-09T08:00:00Z,0.0,false
MT1.LU1.UR1.TI.QVmomDelta,2026-11-09T08:00:00Z,5.0,false
```

**Предусловие:**

- Сессия historical завершена (status = 8, DONE)
- Период: 08:00–08:10, speedRatio = 10000
- В `model_main_{id}` есть результаты (≥ 600 сообщений)
- Расчётные теги присутствуют: Head, PressDelta, QVmomDelta

**Действия:**

1. `api.export_(id, format="csv", startTime="2026-11-09T08:00:00Z", endTime="2026-11-09T08:05:00Z")` ⚠️ —
   экспорт за 5 минут (для ускорения). Система читает результаты из
   `model_main_{id}` (или CH) за диапазон, формирует CSV, возвращает body.
   Метод: GET или POST — зависит от реализации
2. `WAIT(10)` — чтение, формирование CSV (~1500 строк)
3. Проверить HTTP-ответ: статус 200, `Content-Type: text/csv`
4. Парсить CSV: подсчитать строки (без заголовка). Ожидаем: ≥ 500 строк
   (5 мин × 60 с × ~2–3 расчётных тега)
5. Проверить: в CSV есть строки для `KIP1.TI.Head`, `KIP1.TI.PressDelta`,
   `UR1.TI.QVmomDelta`
6. Проверить выборочно: строка `Head` за `08:00:30Z` сравнивается с данными в
   `model_main_{id}` (через `kafka.consume`) — совпадение ± 0.01

**Ожидаемый результат:**

| Шаг | Ожидание | Пояснение |
|---|---|---|
| 3 | HTTP 200, Content-Type: text/csv | Файл сформирован |
| 4 | ≥ 500 строк | Данные за 5 минут |
| 5 | Есть Head, PressDelta, QVmomDelta | Базовые теги присутствуют |
| 6 | Значения совпадают с Kafka | Нет расхождения |

**Teardown:** `api.close(id)` ⚠️ → `RESET()`

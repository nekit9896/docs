# Contract: JSON-отчёт прогона

**Date**: 2026-11-18 | Формат отчёта (FR-004, FR-007, FR-008, SC-005)

Машиночитаемый отчёт прогона; потребители — TestOps (наряду с JUnit XML), качества-гейт (FR-013), карта покрытия (FR-012).

## Пример

```json
{
  "run_id": "20261118-143000",
  "env": "test-stand",
  "catalog_snapshot": "cases@2026-11-18",
  "started_at": "2026-11-18T14:30:00Z",
  "finished_at": "2026-11-18T15:12:00Z",
  "status": "completed",
  "totals": {"passed": 40, "failed": 2, "skipped": 1, "infra_error": 0},
  "results": [
    {
      "case_id": "HY-CALC-012",
      "suite": "hy_calc",
      "verdict": "failed",
      "duration_s": 84.2,
      "mismatches": [
        {"checkpoint": "напор", "expected": 21.5, "actual": 20.9, "tolerance": 0.1}
      ],
      "skip_reason": null,
      "infra_reason": null
    }
  ]
}
```

## Правила

- Обязательные поля: `run_id`, `status`, `totals`, в каждом результате — `case_id`, `suite`, `verdict`, `duration_s`
- `verdict` — enum: `passed` / `failed` / `skipped` / `infra_error` (FR-004)
- `mismatches` обязателен и непуст для `failed` — инженер видит причину без чтения кода проверки (SC-005)
- `skip_reason` обязателен для `skipped`; `infra_reason` обязателен для `infra_error`
- каждый `case_id` существует в каталоге и уникален внутри `results` (FR-007)
- `totals` обязан совпадать с агрегатом по `results`
- `catalog_snapshot` фиксирует версию каталога на момент запуска (edge case: изменение каталога во время прогона)

## Версионирование

Поля только добавляются; удаление/переименование полей — новая мажорная версия схемы с уведомлением потребителей.

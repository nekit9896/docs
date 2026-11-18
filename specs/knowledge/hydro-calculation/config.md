---
id: KB-CALC-CONFIG-001
title: Конфигурация hydro-calculation (application.yml, MtProps, PlanScannerProps)
service: hydro-calculation
group: config
source: confluence/repo_description_hydro-calculation#3.Application Configuration, #13.Resources, «Конфигурация», #2.Configuration Layer
requires: [KB-CALC-OVERVIEW-001]
related: [KB-CALC-ALGO-LU-DATA-001]
status: verified
---

# application.yml

```yaml
hydro-calculation:
  mt-scope: []                 # список МП для обработки
  plan-scanner-interval: 1     # интервал сканирования плана, минут
  dry-run-thinning: false      # режим тестирования прореживания
```

# Классы конфигурации (prop/)

| Класс | Поля | Назначение |
|---|---|---|
| MtProps | `scope` (список МП из application.yml), `dryRunThinning` | настройки МП; фильтр `BaseAlgorithm.getMtNames()` |
| PlanScannerProps | `planScannerInterval` (минуты) | планировщик PumpingPlanAlg |
| FormattingProps | `DECIMAL_FORMATTER` (3), `FLOAT_FORMATTER` (2), `DOUBLE_FORMATTER` (7) | формат вывода (KB-CALC-FORMULA-001) |
| PressureUnits | `pressureKgsToMpa`, `pressureMpaToKgs` | единицы давления (KB-CALC-FORMULA-001) |

- `Application.java` (`@SpringBootApplication`): конфигурация Spring Boot,
  регистрация `AlgoManager`, использование `application.yml` для внешних настроек.
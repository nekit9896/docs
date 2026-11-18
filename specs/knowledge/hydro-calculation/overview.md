---
id: KB-CALC-OVERVIEW-001
title: Микросервис hydro-calculation — назначение, слои, модель запуска
service: hydro-calculation
group: overview
source: confluence/repo_description_hydro-calculation#«Обзор архитектуры», #1, #4, #5
requires: []
related: [KB-CALC-ALGO-001, KB-CALC-API-001, KB-CALC-CONFIG-001]
status: verified
---

# hydro-calculation — обзор

Микросервис расчёта гидравлических параметров магистральных трубопроводов (МП)
и линейных участков (ЛУ) в режиме реального времени: обрабатывает данные
датчиков давления, расхода, высоты и др. Описание репозитория полное
(«Ожидается: нет» — все пути проанализированы).

## Слои (пакеты)

| Пакет | Назначение | Фрагмент |
|---|---|---|
| `Application.java` | Spring Boot, регистрация компонентов | KB-CALC-CONFIG-001 |
| `prop/` | Конфигурация (FormattingProps, MtProps, PlanScannerProps, PressureUnits) | KB-CALC-CONFIG-001, KB-CALC-FORMULA-001 |
| `AlgoManager.java` | Запуск и координация всех алгоритмов | KB-CALC-ALGO-001 |
| `AlgoStatus.java` | Состояние выполнения алгоритма (algoName, startTime, success, errorMsg) | KB-CALC-ALGO-001 |
| `dto/` | MappingToTags, SessionToServiceDTO | KB-CALC-MODELLING-001 |
| `errors/` | CalculationException, CalculationNotReadyException | KB-CALC-SIDEFX-001 |
| `filter/` | MultiReadHttpServletRequest, RequestInfoFilter (HTTP) | KB-CALC-API-001 |
| `modelling/` | Режим моделирования (EvoCoreDelegated, ModelAlarmService, ModelEvoApiManager, ModellingKafkaTnMsgSender) | KB-CALC-MODELLING-001 |
| `alg/` | 40 алгоритмов расчёта + BaseAlgorithm | KB-CALC-ALGO-001 и след. |
| `structure/` | Константы тегов (LuParameters, KipParameters, ...) | KB-CALC-TAGS-* |
| `utils/` | UnitConversion, CommaFormatter, PressureFormatter | KB-CALC-FORMULA-001 |
| `resources/application.yml` | Конфигурация приложения | KB-CALC-CONFIG-001 |

## Модель запуска

- `AlgoManager` (`@Component`, `@PostConstruct initAlgorithms()`) регистрирует
  все алгоритмы через `AlgoFactory`.
- `@Scheduled(fixedRate = 60000)` — **все алгоритмы запускаются каждые 60 секунд**
  (`runAllAlgorithms()` → `algo.run()`), ошибки логируются, падение одного
  алгоритма не роняет остальные.
- `@PreDestroy` — очистка списка алгоритмов.
- Каждый `BaseAlgorithm.run()` измеряет время выполнения, обрабатывает
  исключения; `destroy()` освобождает подписки и исполнители.
- Часть алгоритмов дополнительно держит собственные планировщики/подписки
  (см. фрагменты по алгоритмам: тики 2 с, 1000 мс, 60 мин и т.д.).

## Доступ к данным

Все чтения/записи — через Evo API (`KB-CALC-API-001`); кэши в `BaseAlgorithm`
(`data`, `dataInvalid`, `luName2MtReadable`, `knownSubscriptions`).
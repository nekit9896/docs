---
id: KB-HM-OVERVIEW-001
title: Микросервис hydro-history-and-model — назначение, типы сессий, структура
service: hydro-history-and-model
group: overview
source: confluence/repo_description_hydro-history-and-model#1, #2, шапка
requires: []
related: [KB-HM-SESSIONS-001, KB-HM-PLAYER-001, KB-HM-SAVE-001, KB-HM-STORAGE-001]
status: verified
---

# hydro-history-and-model — обзор

Сервис Воспроизведения истории и Моделирования: управляет сессиями и пошаговым
воспроизведением данных из ClickHouse в Kafka, имитируя реальный поток данных.
Поддерживаются значения сигналов (`tagValue`) и сообщения (`alarmValue`).

Источник описания: `readme.md` + `docs/spring-configuration-metadata.md`
(«Ожидается: нет» — описание репозитория полное).

## Виды сессий

| Тип | Описание |
|---|---|
| `historical + history` | Плеер истории |
| `historical + saved` | Воспроизведение сохранённых сессий |
| `historical + imported` | Импортированный поток данных |
| `modelling` | Моделирование |

Сохранение модельной сессии: по окончании работы поток данных из Kafka
сохраняется обратно в ClickHouse, сессия `modelling` превращается в
`historical + saved` (подробно — KB-HM-SAVE-001).

## Прикладные сессии

Реализованы в приложениях `hmi-backend`, `hydro-calculation`, `alarm-service`,
`alarm-view-service` (у каждого — endpoint `/v1/sessions`, KB-HM-STORAGE-001).
Обеспечивают изоляцию окружения в UI Гидроуклон: расчёты ведутся изолированно
от оперативных данных (детали — KB-HM-SESSIONS-001, KB-HM-FAULT-001).

## Прочие процессы

- **Сервис отчётов Гидроуклон** — выгрузка журнала событий за интервал времени
  в формате .xlsx (KB-HM-REPORT-001).
- **Импорт исторических данных** — `HistoryImportController` / `service/historyimport/`:
  импорт потока данных порождает новую сессию, в которую и импортирует
  (ZIP-механика — KB-HM-ZIP-001).

## Логическая структура (пакеты)

```
/controller/                       # REST-контроллеры
|- ModHistController.java          # Работа с сессиями Плеера и Моделирования
|- HistoryImportController.java    # Импорт потока данных, породит новую сессию, в которую и импортирует
|- ReportController.java           # Сервис отчетов Гидроуклон
|- AlarmSaverController.java       # Ручное-отладочное управление сохранением Сообщений (Модельная сессия)
|- ValueSaverController.java       # Ручное-отладочное управление сохранением Значений (Модельная сессия)
|- DataExchangeController.java     # Ручно-отладочный экспорт-импорт данных сессий
/modelling/                        # Подменные классы для управляемого окружения на уровне Evo-Api
/persistence/                      # JPA-классы для работы с СУБД
/saver/                            # Классы сохранения модельной сессии (поглощённый проект, обособлено)
/service/
|- ModHistService.java             # Согласующий Фасад над SessionManagerServiceImpl + ModellingService
|- ModellingService.java           # Плеер истории, потоки данных, порождение прикладных сессий, слежка
|- SessionManagerServiceImpl.java  # Управление сущностями Сессия (CRUD)
|- historyimport/                  # Классы для импорта исторических данных
|- player/                         # Плеер Истории и Моделирования (выгрузка из Clickhouse, timeline)
|- report/                         # Классы для построения Отчётов Гидроуклон
|- components/
   |- KafkaTopicRecreator.class    # Создание-удаление топиков в Kafka для Сессий
   |- RemotesWalker.class          # Создание-удаление Прикладных сессий
/watermark/                        # Watermark-сервис: владение асинхронным процессом
                                   # в конкурентной среде резервных сущностей приложения
```
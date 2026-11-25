---
id: KB-HMI-STREAM-001
title: Data Stream — стримовая обработка (значения, алармы, история)
service: hmi-backend
group: data
source: real_repo_dump/hmi-backend:L3855-L5291 (datastream/*)
requires: []
related: [KB-HMI-WS-001, KB-HMI-MODEL-001, KB-HMI-TAG-001]
status: verified
---

# Data Stream

Стримовый слой обработки данных в реальном времени.

## Компоненты

| Класс | Роль |
|---|---|
| `DataStreamManager` | Оркестратор: жизненный цикл провайдеров и хендлеров |
| `DataStreamProvider` (интерфейс) | Источник стримов (Kafka, mock, model) |
| `LiveDataStreamProvider` | Провайдер live-потока (текущие значения подписок) |
| `HistoryDataStreamProvider` | Провайдер стримов истории (плеер) |
| `TagValueStreamHandler` | Входящие значения тегов: буферизация, валидация, доставка подписчикам |
| `TagAlarmStreamHandler` | Алармы: ретрансляция подписчикам |
| `HistoryStreamHandler` | Стримы истории для плеера |
| `TimelineBucket` | Временное окно агрегации: собирает значения за период, отправляет пакетом |

## Поток данных (V2 подписка)

```
Kafka topic → DataStreamManager → TagValueStreamHandler
                                         │
                                         ├── ProtoValidator (валидация типа)
                                         ├── TimelineBucket (буфер 50 мс)
                                         └── HotlinkSession → WebSocket V2 (SUB_ANSWER)
```

## Поток данных (плеер истории)

```
ClickHouse → HistoryDataStreamProvider → HistoryStreamHandler
                                                  │
                                                  └── HotlinkSession → WebSocket V2 (SUB_ANSWER)
```
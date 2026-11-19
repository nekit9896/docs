---
id: KB-HMI-OVERVIEW-001
title: hmi-backend — назначение, модули, смежные компоненты, API V1/V2
service: hmi-backend
group: overview
source: confluence/hmi-backend-descr.md#«Общее описание», «Тег → Версии API»
requires: []
related: [KB-HMI-TAG-001, KB-HMI-WS-001, KB-HMI-STREAM-001, KB-HMI-MODEL-001, KB-HM-OVERVIEW-001]
status: verified
---

# hmi-backend — обзор

**hmi-backend** — сервис HMI в составе EVOSCADA на базе evo-manager. Обеспечивает
данные для расчёта отображения элементов экранных форм (ЭФ), получение/отправку
команд телерегулирования и телеуправления. Связующий интерфейс между клиентскими
приложениями (ЭФ, тренды) и внутренними сервисами SCADA.

## Модули функционала

| Модуль | Описание |
|---|---|
| WebSocket V1 | Текстовые подписки на сигналы, обмен в реальном времени (окно агрегации **1000 мс**) |
| WebSocket V2 | JSON-фреймы: подписки, вызовы (TAG_GET/SET/FIND/NAMES/OBJECT_TYPES), плеер истории, PING/PONG (окно агрегации **50 мс**) |
| REST | Получение/запись значений тегов, поиск, метаданные, история |
| Метаданные | Чтение из кеша (**TTL 5 с**), создание/удаление объектов с маршрутизацией |
| Аудит/алармы | Запись действий → Grant-Access-Audit, Alarm-Service |
| История | Вычитывание из ClickHouse (REST, батчи по **10 000** ключей), плеер истории (WebSocket) |
| Data Stream | Стримовая обработка: значения тегов, алармы, история (TimelineBucket) |
| Modelling | Моделирование сессий, маршрутизация сообщений, mock-провайдеры |
| Прогревание | Warm-up Kafka producer, WebSocket, tag-set, tag-info store при старте |

## Смежные компоненты

| Компонент | Роль |
|---|---|
| Kafka | Текущие данные/команды через топики; источник метаданных (взаимозаменяемо с Redis) |
| Redis | Кеш информационной модели, метаданные (взаимозаменяемо с Kafka) |
| ClickHouse | Исторические данные (JDBC) |
| Data-Manager | Интерфейс ИМ и сигналов (REST) |
| Alarm-Service | События и алармы (REST) |
| Grant-Access-Audit | Аудит действий оператора (REST) |
| Schema Registry | Confluent Schema Registry для Protobuf-сериализации |

## Инструменты

- **Swagger UI:** `http(s)://<host>:<port>/swagger-ui/index.html`
- **Tag Monitor:** `http(s)://<host>:<port>/tag-monitor.html` — поиск/подписка на
  теги, ручная запись значений, плеер истории, выборка архивов из ClickHouse

## Версии API

| Версия | Префикс | Формат значения | Статус |
|---|---|---|---|
| V1 | `/` | Вложенная типизация: `"value": {"stringVar": "..."}` | Устаревшая (активна для legacy-эндпоинтов) |
| V2 | `/v2/` | Плоские JSON-примитивы: `"value": "..."` | Актуальная |
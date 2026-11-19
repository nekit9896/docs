---
id: KB-HM-STORAGE-001
title: Хранилища, Kafka-топики, endpoints прикладных сессий, тег-время
service: hydro-history-and-model
group: storage
source: confluence/repo_description_hydro-history-and-model#3, «Таблицы Clickhouse», «Топики Kafka», «Endpoints», «Теги», «Параметры»
requires: [KB-HM-OVERVIEW-001]
related: [KB-HM-SESSIONS-001, KB-HM-WATERMARK-001, KB-HM-SAVE-001, KB-HM-ZIP-001, KB-HM-CONFIG-002]
status: verified
---

# Хранилища, топики, endpoints

## Требования к окружению

- Настроенная Информационная Модель (вычитывается из **Redis**).
- Возможность работы с брокером (**Kafka**).
- Доступ в **ClickHouse**.
- Для инициации Прикладных сессий — доступ к 4 приложениям (см. Endpoints);
  в конфигурации вписываются **прямые адреса** каждой сущности, без
  балансировщика (haProxy, nginx).

## Реляционная БД (PostgreSQL)

Таблицы (сущностные; в источнике перечислены под заголовком «Таблицы Clickhouse»
— расхождение G7, см. `meta/discrepancies-2026-11-17.md`; SQL ватермарка —
диалект PostgreSQL: `nextval`, `ON CONFLICT`, `now()`; `spring.datasource.*` —
`${PG_DB_*}`):

| Таблица | Назначение |
|---|---|
| `session_manager_sessions` | Сущность Сессии, присваивается номер |
| `watermarks` | Владение процессом в Watermark-сервисе (+ `watermark_epoch_seq`) |
| `save_sessions` | Сохранятельные сессии (для Сообщений и Значений) |
| `save_session_progress` | Прогресс сохранения, детализация на каждую партицию топика Kafka |

## ClickHouse

Основной datasource: `tn-scada.datasource.*` (`${DB_TYPE:clickhouse}`,
`${DB_CONNECTION_STRING}`, `${DB_USERNAME:}`, `${DB_PASSWORD:}`).
Для сохранения модельных сессий — отдельный `tn-scada.datasource-saver.*`
(`${CH_DB_*}`): БД `db`, таблицы `valueRecords` (значения сигналов) и
`alarmRecords` (сообщения). Чтение истории плеером и запись импортированных
данных — в тот же ClickHouse (партиции по сессиям, `partitionService`).

## Kafka

| Топик | Назначение |
|---|---|
| `historySaver.commands` | Сервисный топик команд (default `tn-scada.history-model.kafka.service-topic`) |
| Модельные топики | Для значений и для сообщений, префикс `model-session-` (`tn-scada.history-model.model-topic-prefix`) |

Топики сессий создаёт/удаляет `KafkaTopicRecreator`. При сохранении
модельной сессии топики **не уничтожаются** (KB-HM-SAVE-001). Схема данных —
`TnMsg.Key`/`TnMsg.Msg` (KB-HM-WORKER-001).

## Endpoints прикладных сессий

| Endpoint | Назначение |
|---|---|
| `/v1/sessions` | Создание-удаление прикладных сессий (hmi-backend, hydro-calculation, alarm-service, alarm-view-service) |

## Теги (Информационная Модель)

| Тег | Описание |
|---|---|
| `<Project_Name>:_Player.Time` | Тег-время по умолчанию, тип данных `timeVar` (должен быть создан и маршрутизирован) |
| `_Player.Time` | Тег вещания времени для Прикладных сессий, без уточнения проекта (`tn-scada.history-model.time-tag`) |
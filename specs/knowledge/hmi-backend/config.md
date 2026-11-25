---
id: KB-HMI-CONFIG-001
title: hmi-backend — переменные конфигурации (env/yml)
service: hmi-backend
group: config
source: real_repo_dump/hmi-backend:L11896-L12013 (src/main/resources/application.yml); L437-L536 (README.md)
requires: []
related: [KB-HMI-WS-001, KB-HMI-STREAM-001, KB-HMI-SVC-001, KB-HM-CONFIG-002]
status: verified
---

# Конфигурация hmi-backend

## Приложение

| Переменная | Default | Описание |
|---|---|---|
| `WEB_SERVER_PORT` | `8080` | TCP порт |
| `SERVER_ALLOWED_ORIGINS` | `*` | CORS |
| `WEB_CLIENT_TIMEOUT` / `NETWORK_TIMEOUT_MS` | `5000` | Таймаут HTTP-запросов к внешним сервисам (мс) |
| `CSPA_TOPICS` | — | Топик на чтение из Kafka |

## evo-manager / Kafka

| Переменная | Default | Описание |
|---|---|---|
| `EVO_MANAGER_APP_ID` | — | ID сервиса (шаблон `{имя}_{номер}`) |
| `EVO_MANAGER_HOT_TOPICS` | — | Hot-топики |
| `KAFKA_APPLICATION_ID_CONFIG` | `cspa-hmi-backend-1` | Group ID потребителя |
| `BOOTSTRAP_SERVERS_CONFIG` | — | Адреса нод Kafka |
| `SCHEMA_REGISTRY_URL_CONFIG` | — | Confluent Schema Registry URL |
| `KAFKA_ENABLE_SSL` | `false` | SSL для Kafka |
| `KAFKA_KEYSTORE_LOCATION` / `KAFKA_KEYSTORE_PASSWORD` | — | KeyStore для Kafka SSL |
| `KAFKA_TRUSTSTORE_LOCATION` / `KAFKA_TRUSTSTORE_PASSWORD` | — | TrustStore для Kafka SSL |

## Смежные сервисы

| Переменная | Описание |
|---|---|
| `DATAMANAGER_ROOT_URL` / `TN_SCADA_DATA_MANAGER_URL_ROOT` | Data-Manager |
| `GAAUDIT_URL_ROOT` | Grant-Access-Audit |
| `ALARMSERVICE_URL_ROOT` | Alarm-Service |

## Redis

| Переменная | Default | Описание |
|---|---|---|
| `REDIS_ADDRESS` | — | Адреса (Sentinel/Redis), через запятую с портами |
| `REDIS_CONNECTION_TYPE` | `Standalone` | `Standalone` / `Sentinel` / `Cluster` |
| `REDIS_SENTINEL_MASTER` | — | Имя master-узла (для Sentinel) |
| `REDIS_USERNAME` / `REDIS_PASSWORD` | — | ACL логин/пароль |
| `REDIS_SENTINEL_USERNAME` / `REDIS_SENTINEL_PASSWORD` | — | ACL логин/пароль для Sentinel |
| `REDIS_ENABLE_SSL` | `false` | SSL для Redis |
| `REDIS_KEYSTORE_LOCATION` / `REDIS_KEYSTORE_PASSWORD` | — | KeyStore для Redis SSL |
| `REDIS_TRUSTSTORE_LOCATION` / `REDIS_TRUSTSTORE_PASSWORD` | — | TrustStore для Redis SSL |
| `TAG_METADATA_TOPIC` / `TN_SCADA_METADATA_TOPIC` | `dm-meta` | Топик метаданных |

## ClickHouse

| Переменная | Описание |
|---|---|
| `DB_CONNECTION_STRING` | JDBC URL |
| `DB_USERNAME` / `DB_PASSWORD` | Учётка |
| `DB_TYPE` | `clickhouse` |

## HMI / WebSocket

| Переменная | Default | Описание |
|---|---|---|
| `tn-scada.hmi.sample-time` | `50` | Окно агрегации WS V2 (мс) |
| `tn-scada.hmi.clock-message-interval-s` | `1` | Интервал серверного времени (с), 0 — отключить |
| `tn-scada.hmi.clientside-stale-time-s` | `600` | Тайм-аут неактивной сессии (с); в `application.yml` = 600, ранее заявлялось 3600 (G46) |
| `tn-scada.hmi.clientside-wake-time-s` | `30` | Тайм-аут пробуждения сессии (с) |
| `CSPA_HMI_CLIENTSIDE_STALE_TIME_S` / `CSPA_HMI_CLIENTSIDE_WAKE_TIME_S` / `CSPA_HMI_CLOCK_MESSAGE_INTERVAL_S` | — | Альтернативные имена (stale / wake / clock) |
| `USER_ACTION_TAGNAME` | — | Тег журнала действий в Alarm-Service |
| `USER_ACTION_ALERT_CLASS` | `AC1` | Класс алармов |
| `tn-scada.hmi-backend.use-sync-set` | `true` | Синхронное подтверждение записи |

## Логирование / OpenTelemetry

| Переменная | Default | Описание |
|---|---|---|
| `LOGGER_ROOT_LEVEL` | `INFO` | Корневой логер (библиотеки) |
| `LOGGER_LEVEL` | `INFO` | `tnt.tnscada.*` |
| `LOGGER_OUTPUT_PATTERN_CONFIG` | — | Формат логов |
| `OTEL_SDK_DISABLED` | `false` | Вкл/выкл OTel |
| `OTEL_JAVAAGENT_LOGGING` | — | Куда выводить логи OTel agent |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | URL сборщика |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | — | Протокол (gRPC / HTTP) |
| `OTEL_SERVICE_NAME` | — | Имя в трассировке |
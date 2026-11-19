---
id: KB-HM-CONFIG-002
title: application.yml hydro-history-and-model — полная таблица параметров
service: hydro-history-and-model
group: config
source: confluence/repo_description_hydro-history-and-model#5 («Все параметры из application.yml»)
requires: [KB-HM-CONFIG-001]
related: [KB-HM-STORAGE-001]
status: verified
---

# application.yml — все параметры

Фрагмент дублирует значения дефолтов из KB-HM-CONFIG-001 только в пределах
самой таблицы yml (источник приводит её как отдельный список).

| Параметр | Значение |
|---|---|
| alarm-service-api.type | `mock` |
| debug | `false` |
| evo-manager.alarm-subscription.topic | `${ALARM_TOPIC:history}` |
| evo-manager.app-id | `${EVO_MANAGER_APP_ID}` |
| evo-manager.diagnostic.redu.enabled | `false` |
| evo-manager.launcher.enable | `false` |
| evo-services.consensus-service.mock | `true` |
| evo-services.consensus-service.type | `MOCK` |
| logging.charset.console | `UTF-8` |
| logging.charset.file | `UTF-8` |
| logging.level.root | `${LOGGER_ROOT_LEVEL:WARN}` |
| logging.level.tnt | `${LOGGER_LEVEL:INFO}` |
| logging.pattern.console | `${LOGGER_OUTPUT_PATTERN_CONFIG:%d{ISO8601} [%X{requestId}] [%-22.22t] %highlight(%-5level) %yellow(%30.30C{1}) %msg%n%throwable}` |
| management.endpoint.health.show-details | `always` |
| management.endpoints.web.exposure.include | `health,info,heapdump,prometheus` |
| server.allowed_origins | `${SERVER_ALLOWED_ORIGINS:*}` |
| server.max-http-request-header-size | `10MB` |
| server.port | `${WEB_SERVER_PORT}` |
| server.shutdown | `graceful` |
| spring.datasource.hikari.connection-timeout | `30000` |
| spring.datasource.hikari.idle-timeout | `300000` |
| spring.datasource.hikari.max-lifetime | `600000` |
| spring.datasource.hikari.validation-timeout | `150000` |
| spring.datasource.password | `${PG_DB_PASSWORD}` |
| spring.datasource.remove-abandoned | `true` |
| spring.datasource.remove-abandoned-timeout | `60` |
| spring.datasource.test-while-idle | `true` |
| spring.datasource.time-between-eviction-runs-millis | `30000` |
| spring.datasource.url | `${PG_DB_CONNECTION_STRING}` |
| spring.datasource.username | `${PG_DB_USERNAME}` |
| spring.datasource.validation-query | `SELECT 1;` |
| spring.flyway.enabled | `true` |
| spring.jpa.hibernate.ddl-auto | `validate` |
| spring.jpa.open-in-view | `false` |
| spring.kafka.application-id | `${KAFKA_APPLICATION_ID_CONFIG:}` |
| spring.kafka.bootstrap-servers | `${BOOTSTRAP_SERVERS_CONFIG:}` |
| spring.kafka.listener.group-id | `${KAFKA_APPLICATION_ID_CONFIG:}` |
| spring.kafka.schema-registry-url | `${SCHEMA_REGISTRY_URL_CONFIG:}` |
| spring.kafka.ssl.enable-ssl | `${KAFKA_ENABLE_SSL:false}` |
| spring.kafka.ssl.key-store-location | `${KAFKA_KEYSTORE_LOCATION:}` |
| spring.kafka.ssl.key-store-password | `${KAFKA_KEYSTORE_PASSWORD:}` |
| spring.kafka.ssl.trust-store-location | `${KAFKA_TRUSTSTORE_LOCATION:}` |
| spring.kafka.ssl.trust-store-password | `${KAFKA_TRUSTSTORE_PASSWORD:}` |
| spring.servlet.multipart.max-file-size | `50MB` |
| spring.servlet.multipart.max-request-size | `50MB` |
| springdoc.cache.disabled | `true` |
| springdoc.swagger-ui.disable-swagger-default-url | `true` |
| tn-scada.datasource-saver.alarm-table | `alarmRecords` |
| tn-scada.datasource-saver.db | `db` |
| tn-scada.datasource-saver.password | `${CH_DB_PASSWORD}` |
| tn-scada.datasource-saver.url | `${CH_DB_CONNECTION_STRING}` |
| tn-scada.datasource-saver.username | `${CH_DB_USERNAME}` |
| tn-scada.datasource-saver.value-table | `valueRecords` |
| tn-scada.datasource.database | `${DB_TYPE:clickhouse}` |
| tn-scada.datasource.password | `${DB_PASSWORD:}` |
| tn-scada.datasource.url | `${DB_CONNECTION_STRING}` |
| tn-scada.datasource.username | `${DB_USERNAME:}` |
| tn-scada.history-model.alarm-service-list | `${ALARM_SERVICE_LIST:}` |
| tn-scada.history-model.alarm-view-service-list | `${ALARM_VIEW_SERVICE_LIST:}` |
| tn-scada.history-model.cleanup.imported-sessions.cron | `0 0 0 * * *` |
| tn-scada.history-model.cleanup.imported-sessions.enabled | `true` |
| tn-scada.history-model.cleanup.imported-sessions.lock-at-least-for | `PT30S` |
| tn-scada.history-model.cleanup.imported-sessions.lock-at-most-for | `PT50S` |
| tn-scada.history-model.cleanup.imported-sessions.soft | `true` |
| tn-scada.history-model.cleanup.imported-sessions.ttl | `P7D` |
| tn-scada.history-model.fetch-optimized-enabled | `true` |
| tn-scada.history-model.hmi-backend-list | `${HMI_BACKEND_LIST:}` |
| tn-scada.history-model.hydro-calculation-list | `${HYDRO_CALCULATION_LIST:}` |
| tn-scada.history-model.kafka.service-topic | `historySaver.commands` |
| tn-scada.history-model.model-topic-prefix | `model-session-` |
| tn-scada.history-model.player-batch-limit | `100000` |
| tn-scada.history-model.player-preload-ticks | `300` |
| tn-scada.history-model.remote-session-check-interval | `PT10S` |
| tn-scada.history-model.report.alarm-history-max-page-size | `${ALARM_HISTORY_MAX_PAGE_SIZE:10000}` |
| tn-scada.history-model.report.alarm-view-service-haproxy-url | `${ALARM_VIEW_SERVICE_HAPROXY_URL:}` |
| tn-scada.history-model.report.messages-template-path | `${REPORT_MESSAGES_TEMPLATE_PATH:templates/reportMessagesTemplate.xlsx}` |
| tn-scada.history-model.report.template-path | `${REPORT_TEMPLATE_PATH:templates/reportTemplate.xlsx}` |
| tn-scada.history-model.report.time-zone | `${REPORT_TIME_ZONE:Europe/Moscow}` |
| tn-scada.history-model.time-tag | `_Player.Time` |
| tn-scada.history-model.watermark.lease-duration | `${WATERMARK_LEASE_DURATION:PT10S}` |
| tn-scada.history-model.watermark.node-id | `${WATERMARK_NODE_ID:${HOSTNAME:}}` |
| tn-scada.history-model.watermark.recovery-scan-interval | `${WATERMARK_RECOVERY_SCAN_INTERVAL:PT4S}` |
| tn-scada.history-model.worker.batch-size | `20000` |
| tn-scada.history-model.worker.max-runtime | `PT15M` |
| tn-scada.history-model.worker.max-workers | `4` |
| tn-scada.history-model.worker.poll-timeout | `PT1S` |
| tn-scada.history-model.worker.status-check-every | `PT1S` |
| tn-scada.kafka.bootstrap-servers | `${KAFKA_BOOTSTRAP_SERVERS}` |
| tn-scada.kafka.listener.group-id | `historySaver-group` |
| tn-scada.kafka.schema-registry-url | `${SCHEMA_REGISTRY_URL_CONFIG}` |
| tn-scada.metadata.dont-show-target-project-in-names | `true` |
| tn-scada.metadata.topic | `${TAG_METADATA_TOPIC:dm-meta}` |
| tn-scada.redis.acl.password | `${REDIS_PASSWORD:}` |
| tn-scada.redis.acl.sentinel-password | `${REDIS_SENTINEL_PASSWORD:}` |
| tn-scada.redis.acl.sentinel-username | `${REDIS_SENTINEL_USERNAME:}` |
| tn-scada.redis.acl.username | `${REDIS_USERNAME:}` |
| tn-scada.redis.address | `${REDIS_ADDRESS}` |
| tn-scada.redis.connection-type | `${REDIS_CONNECTION_TYPE:Cluster}` |
| tn-scada.redis.sentinel-master | `${REDIS_SENTINEL_MASTER:}` |
| tn-scada.redis.ssl-properties.key-store-location | `${REDIS_KEYSTORE_LOCATION:}` |
| tn-scada.redis.ssl-properties.key-store-password | `${REDIS_KEYSTORE_PASSWORD:}` |
| tn-scada.redis.ssl-properties.ssl | `${REDIS_ENABLE_SSL:false}` |
| tn-scada.redis.ssl-properties.trust-store-location | `${REDIS_TRUSTSTORE_LOCATION:}` |
| tn-scada.redis.ssl-properties.trust-store-password | `${REDIS_TRUSTSTORE_PASSWORD:}` |
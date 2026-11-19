---
id: KB-HM-CONFIG-001
title: Конфигурация: tn-scada.datasource-saver.* и tn-scada.history-model.*
service: hydro-history-and-model
group: config
source: confluence/repo_description_hydro-history-and-model#5 («Конфигурация», metadata)
requires: []
related: [KB-HM-CONFIG-002, KB-HM-WORKER-001, KB-HM-WATERMARK-001, KB-HM-CLEANUP-001, KB-HM-PLAYER-001, KB-HM-REPORT-001]
status: verified
---

# Конфигурация (spring-configuration-metadata)

Префикс параметров: **tn-scada.history-model** и **tn-scada.datasource-saver**.
Участвуют настройки Spring-Boot и Evo-Manager. Полный application.yml —
KB-HM-CONFIG-002.

## tn-scada.datasource-saver.* (ClickHouse сохранения)

| Параметр | Тип | Default | yml-переопределение | Описание |
|---|---|---|---|---|
| `alarm-table` | String | `alarmRecords` | — | Имя таблицы ClickHouse для сообщений модельных сессий |
| `db` | String | `db` | — | Database-пространство ClickHouse |
| `hikari.maximum-pool-size` | Integer | — | — | Ограничение множества соединений при сохранении |
| `password` | String | — | `${CH_DB_PASSWORD}` | Пароль ClickHouse |
| `url` | String | — | `${CH_DB_CONNECTION_STRING}` | URL ClickHouse |
| `username` | String | — | `${CH_DB_USERNAME}` | Учётная запись ClickHouse |
| `value-table` | String | `valueRecords` | — | Имя таблицы для значений сигналов |

## tn-scada.history-model.*

| Параметр | Тип | Default | yml-переопределение | Описание |
|---|---|---|---|---|
| `alarm-service-list` | String | — | `${ALARM_SERVICE_LIST:}` | Прямые URL Alarm-Service, через запятую |
| `alarm-view-service-list` | String | — | `${ALARM_VIEW_SERVICE_LIST:}` | Прямые URL Alarm-View-Service, через запятую |
| `cleanup.imported-sessions.cron` | String | `0 0 3 * * *` | `0 0 0 * * *` | Расписание планировщика очистки |
| `cleanup.imported-sessions.enabled` | Boolean | `true` | — | Включить очистку |
| `cleanup.imported-sessions.lock-at-least-for` | Duration | `PT1M` | `PT30S` | Минимальное время удержания лока |
| `cleanup.imported-sessions.lock-at-most-for` | Duration | `PT5M` | `PT50S` | Максимальное время удержания лока |
| `cleanup.imported-sessions.soft` | Boolean | `true` | — | Мягкое удаление (записи остаются со статусом DELETED) |
| `cleanup.imported-sessions.ttl` | Duration | `PT72H` | `P7D` | Время жизни импортированной сессии |
| `fetch-optimized-enabled` | Boolean | `true` | — | Оптимизированные выборки ClickHouse (нужны snapshot-запросы) |
| `hmi-backend-list` | String | — | `${HMI_BACKEND_LIST:}` | Прямые URL Hmi-Backend, через запятую |
| `hydro-calculation-list` | String | — | `${HYDRO_CALCULATION_LIST:}` | Прямые URL Hydro-Calculation, через запятую |
| `kafka.service-topic` | String | `historySaver.commands` | — | Сервисный топик команд Kafka |
| `model-topic-prefix` | String | `model-session-` | — | Префикс сессионных топиков Kafka |
| `player-batch-limit` | Integer | `100000` | — | Записей за одну вычитку из ClickHouse |
| `player-preload-ticks` | Integer | `300` | — | Секунд воспроизведения для предвыгрузки |
| `remote-session-check-interval` | Duration | `PT10S` | — | Интервал сверки наличия Прикладных сессий |
| `report.alarm-history-max-page-size` | Integer | `10000` | `${ALARM_HISTORY_MAX_PAGE_SIZE:10000}` | Размер порции выгрузки Сообщений |
| `report.alarm-view-service-haproxy-url` | String | — | `${ALARM_VIEW_SERVICE_HAPROXY_URL:}` | URL Alarm-View-Service (балансируемый допустим) |
| `report.messages-template-path` | String | `templates/reportMessagesTemplate.xlsx` | `${REPORT_MESSAGES_TEMPLATE_PATH:...}` | Шаблон Сообщений в отчёте |
| `report.template-path` | String | `templates/reportTemplate.xlsx` | `${REPORT_TEMPLATE_PATH:...}` | Шаблон документа отчёта |
| `report.time-zone` | String | `Europe/Moscow` | `${REPORT_TIME_ZONE:Europe/Moscow}` | Часовой пояс отчёта |
| `time-tag` | String | `_Player.Time` | — | Тег вещания времени для Прикладных сессий (без проекта) |
| `watermark.lease-duration` | Duration | `PT10S` | `${WATERMARK_LEASE_DURATION:PT10S}` | Длительность итерации владения |
| `watermark.node-id` | String | — | `${WATERMARK_NODE_ID:${HOSTNAME:}}` | ID сущности приложения (default в metadata: `${HOSTNAME}`) |
| `watermark.recovery-scan-interval` | Duration | `PT4S` | `${WATERMARK_RECOVERY_SCAN_INTERVAL:PT4S}` | Интервал поиска просроченных Владений |
| `worker.batch-size` | Integer | `20000` | — | Сообщений из Kafka перед записью в ClickHouse |
| `worker.max-runtime` | Duration | `PT15M` | — | Ограничение времени выполнения задания |
| `worker.max-workers` | Integer | `4` | — | Число обработчиков заданий |
| `worker.poll-timeout` | Duration | `PT1S` | — | Частота опроса Kafka при сохранении |
| `worker.status-check-every` | Duration | `PT1S` | — | Интервал сверки статуса задания (не отменён ли) |

Назначения отдельных групп: watermark — KB-HM-WATERMARK-001; worker —
KB-HM-WORKER-001; cleanup — KB-HM-CLEANUP-001; player — KB-HM-PLAYER-001;
report — KB-HM-REPORT-001.
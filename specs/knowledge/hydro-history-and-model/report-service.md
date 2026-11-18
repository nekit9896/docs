---
id: KB-HM-REPORT-001
title: Сервис отчётов Гидроуклон (xlsx-выгрузка журнала событий)
service: hydro-history-and-model
group: report
source: confluence/repo_description_hydro-history-and-model#1 («Сервис отчетов»), «Параметры» (report.*)
requires: []
related: [KB-HM-OVERVIEW-001, KB-HM-CONFIG-001, KB-HM-CONFIG-002]
status: verified
---

# Сервис отчётов Гидроуклон

Выгрузка журнала событий за интервал времени в формате **.xlsx**.
Реализация: `ReportController` + `service/report/` (классы построения отчётов).

## Параметры (KB-HM-CONFIG-001)

| Параметр | Default | Переопределение в yml | Назначение |
|---|---|---|---|
| `report.template-path` | `templates/reportTemplate.xlsx` | `${REPORT_TEMPLATE_PATH:...}` | Шаблон документа отчёта |
| `report.messages-template-path` | `templates/reportMessagesTemplate.xlsx` | `${REPORT_MESSAGES_TEMPLATE_PATH:...}` | Шаблон Сообщений в отчёте |
| `report.alarm-history-max-page-size` | `10000` | `${ALARM_HISTORY_MAX_PAGE_SIZE:10000}` | Размер порции выгрузки Сообщений |
| `report.alarm-view-service-haproxy-url` | — (пусто) | `${ALARM_VIEW_SERVICE_HAPROXY_URL:}` | URL Alarm-View-Service; **допустимо указывать балансируемый адрес** (Протокол://сервер) |
| `report.time-zone` | `Europe/Moscow` | `${REPORT_TIME_ZONE:Europe/Moscow}` | Часовой пояс Даты и Времени внутри отчёта |

Префикс: `tn-scada.history-model.report.*`. Данные сообщений — от
Alarm-View-Service (для отчётов допустим балансировщик, в отличие от
прямых адресов прикладных сессий — KB-HM-STORAGE-001).
---
id: KB-HMI-MODEL-001
title: Modelling (маршрутизация сессий) и Topic-Route (переопределение маршрутов)
service: hmi-backend
group: data
source: real_repo_dump/hmi-backend:L8911-L10222 (modelling/*); L11468-L11584 (service/TopicRouteConfig.java)
requires: [KB-HMI-REST-META-001]
related: [KB-HMI-STREAM-001, KB-HMI-WS-001, KB-HM-SESSIONS-001]
status: verified
---

# Modelling и Topic-Route

## Modelling

Модуль для моделирования/маршрутизации сообщений между сервисами.
Разделяет нагрузку между инстансами: каждый инстанс обслуживает свою порцию
сессий. Маршрутизация по `SessionToServiceDTO`.

| Класс | Роль |
|---|---|
| `EvoCoreDelegated` | Делегирование вызовов в Evo (ядро) |
| `ModelEvoApiManager` | Менеджер API для моделирования |
| `SessionManager` | Управление сессиями моделирования |
| `ModellingKafkaTnMsgSender` | Отправка TnMsg в Kafka (маршрутизация) |
| `ModelDataStreamProvider` | Провайдер данных для моделирования |
| `MockDataStreamProvider` | Mock-провайдер (тестирование) |
| `HotlinkSessionV2Modelling` | Сессия V2 для моделирования |
| `HotlinkWebSocketHandlerV2Modelling` | WebSocket handler для моделирования |
| `HotlinkWebSocketHandlerV2Routed` | Маршрутизированный handler V2 |

Сессии регистрируются через `SessionsController` (см. KB-HMI-REST-META-001).

## Topic-Route (переопределение маршрутов)

Соответствие проектов/типов/параметров → топики Kafka + `descentRule`.
Используется при создании объектов (`TagInfoEditService`).

### YAML

```yaml
tn-scada:
  cspa:
    topic-route:
      root:
        descentRule: rcv
        topic: cspa-main-topic
      project:
        TU1:
          root:
            descentRule: rcv
            topic: tu1-root-topic
          type:
            NPS:
              "[.Alm.AlmAll.AlmAllStop.AlarmMinLevelRzv]":
                descentRule: rcv
                topic: topic1
              "[.]":
                descentRule: rcv
                topic: topic2
```

### Переменные окружения (эквивалент YAML)

```
tn-scada.cspa.topic-route.root.topic=cspa-main-topic
tn-scada.cspa.topic-route.root.descentRule=rcv
tn-scada.cspa.topic-route.project.TU1.root.topic=tu1-root-topic
tn-scada.cspa.topic-route.project.TU1.root.descentRule=rcv
tn-scada.cspa.topic-route.project.TU1.type.NPS."[.Alm.AlmAll.AlmAllStop.AlarmMinLevelRzv]".topic=topic1
tn-scada.cspa.topic-route.project.TU1.type.NPS."[.Alm.AlmAll.AlmAllStop.AlarmMinLevelRzv]".descentRule=rcv
tn-scada.cspa.topic-route.project.TU1.type.NPS."[.]".topic=topic2
tn-scada.cspa.topic-route.project.TU1.type.NPS."[.]".descentRule=rcv
```

### Алгоритм `TopicRouteConfig.getRoutes(objectName, objectTypeName)`

1. Разбивает на `ProjectQualifier`
2. Проект не определён или отсутствует в конфиге → **root route**
3. Проект есть, тип не определён → **project root route**
4. Проект и тип есть → **типовые маршруты** (все параметры типа + `[.]` как fallback)

> `ROOT_PARAMETER_NAME = "."` — fallback-маршрут для параметров без явного определения.
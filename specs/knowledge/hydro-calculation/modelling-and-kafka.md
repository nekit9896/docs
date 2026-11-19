---
id: KB-CALC-MODELLING-001
title: Режим моделирования и Kafka (modelling/)
service: hydro-calculation
group: integration
source: confluence/repo_description_hydro-calculation#9.Modelling Layer, #6.DTO Layer, «Точки интеграции (Kafka)»
requires: [KB-CALC-API-001]
related: [KB-CALC-SIDEFX-001]
status: verified
---

# Modelling Layer (modelling/)

| Класс | Назначение | Методы/поля |
|---|---|---|
| EvoCoreDelegated | Делегирование вызовов Evo для управления временем в сессиях моделирования | `getWallclock()` — время из сессии или системное |
| GenerateModelAlarmDto | DTO для генерации алармов в моделировании | `tag`, `text`, `value` |
| ModelAlarmService | Работа с алармами в моделировании | `createAlarm()`, `updateAlarm()` |
| ModelEvoApiManager | API к Evo в режиме моделирования | `tagGet()`, `tagSet()`, `tagGetHistory()` |
| ModellingKafkaTnMsgSender | Отправка сообщений через **Kafka** в режиме моделирования | `send()` |

# Kafka

Отправка сообщений через `ModellingKafkaTnMsgSender` — только в режиме
моделирования (точка интеграции «Kafka» из описания репозитория).

# DTO Layer (dto/)

- `MappingToTags` — `mapToTags()` / `mapFromTags()` — маппинг данных в теги и обратно.
- `SessionToServiceDTO` — `sessionData`, `serviceData` — данные сессии и сервиса.
---
id: KB-HMI-REST-META-001
title: REST — метаданные (чтение/изменение объектов) и сессии Modelling
service: hmi-backend
group: api
source: real_repo_dump/hmi-backend:L2229-L2508 (controller/MetadataController.java); L2840-L2877 (controller/TagInfoEditController.java); L9176-L9225 (modelling/controller/SessionsController.java)
requires: [KB-HMI-MODEL-001]
related: [KB-HMI-REST-QUERY-001, KB-HMI-TAG-001, KB-HMI-SVC-001]
status: verified
---

# REST: метаданные и сессии

## Чтение (кеш core-meta-data-store)

| # | Эндпоинт | Параметры |
|---|---|---|
| 1 | `GET /v1/configurator/project` | `page`, `size` |
| 2 | `GET /v1/configurator/object-type` | `projectId`, `page`, `size` |
| 3 | `GET /v1/configurator/object` | `objectTypeId`, `projectId`, `parentId`, `sort`, `page`, `size` |
| 4 | `GET /v1/configurator/object/{parentId}/children` | `projectId` |
| 5 | `GET /v1/area_attr` | `project` |
| 6 | `GET /v1/general_attr/{object}` | path `object` |
| 7 | `GET /v2/tag-names` | `objectPattern`, `parameterPattern`, `types[]`, `skipFolders`, `limit` |

## Изменение

| # | Эндпоинт | Описание |
|---|---|---|
| 8 | `POST /object` | Создание объекта + автопрописывание маршрутов (topic-route) |
| 9 | `DELETE /object/{object_name}` | Каскадное удаление |

### Алгоритм `TagInfoEditService.createObjectWithRouting`

1. Проверка конфигурации (Data-Manager URL задан)
2. Получение маршрутов из `TopicRouteConfig` по имени объекта и типу (KB-HMI-MODEL-001)
3. `POST /v1/object` в Data-Manager
4. Если объект уже существует (400):
   - Проверка равенства DTO; если равен — дописывание недостающих маршрутов;
     если не равен — `BadRequestException`
5. Для каждого маршрута: `POST /v1/route_attr`
6. Проверка конфликтов маршрутов

### Вариант с ожиданием (`createObjectWithRoutingAndWaitForApply`)

После создания ожидает появления объекта в локальном кэше (**до 5 сек, интервал
500 мс**).

## Сессии (Modelling) — `SessionsController` (`/v1/sessions`, L9195-L9217)

| Метод | Путь | Описание |
|---|---|---|
| GET | `/v1/sessions/list` | Список сессий |
| GET | `/v1/sessions/{id}` | Информация о сессии (`SessionToServiceDTO`) |
| POST | `/v1/sessions/start` | Регистрация сессии (`SessionToServiceDTO`) |
| POST | `/v1/sessions/close/{id}` | Удаление сессии |

> Сверено с кодом (2026-11-25): ранее заявлялось `POST /sessions` +
> `DELETE /sessions/{sessionId}` — фактические пути другие. Используется модулем
> Modelling для маршрутизации сообщений между сервисами.
---
id: KB-HMI-REST-META-001
title: REST — метаданные (чтение/изменение объектов) и сессии Modelling
service: hmi-backend
group: api
source: confluence/hmi-backend-descr.md#«REST: метаданные (кеш core-meta-data-store)», «REST: сессии (Modelling)»
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

## Сессии (Modelling) — `SessionsController`

| Метод | Путь | Описание |
|---|---|---|
| POST | `/sessions` | Регистрация сессии (`SessionToServiceDTO`) |
| DELETE | `/sessions/{sessionId}` | Удаление сессии |

> Используется модулем Modelling для маршрутизации сообщений между сервисами.
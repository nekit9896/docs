---
id: KB-CALC-API-001
title: Evo API — точки интеграции hydro-calculation
service: hydro-calculation
group: integration
source: confluence/repo_description_hydro-calculation#«Точки интеграции (API Layer)», #8.Filter Layer, #«Валидация», #«Авторизация»
requires: [KB-CALC-OVERVIEW-001]
related: [KB-CALC-MODELLING-001, KB-CALC-SIDEFX-001]
status: verified
---

# Evo API — основной интерфейс взаимодействия с базой данных

| Метод | Назначение |
|---|---|
| `tagGet(String tagName)` | получение значения тега |
| `tagSet(String tagName, Object value, boolean invalid, Date timestamp)` | установка значения |
| `tagGetHistory(...)` | получение истории |
| `tagSubscribe(...)` / `tagUnsubscribe(Subscription)` | подписка на изменения / отписка |
| `makeAlarm(AlarmDto)` | создание аларма |
| `objectExists(String objectName)` | проверка существования объекта |
| `objectNames(String pattern, String type)` | объекты по шаблону |
| `getObjectChildren(String parentName)` / `getObjectParent(String childName)` | дети / родитель |
| `findTag(String tagName)` | поиск тега |

# Валидация чтений (BaseAlgorithm)

| Метод | Проверяет |
|---|---|
| `getFiniteValueOrNull` | null, invalid-флаг, NaN, Infinite |
| `getIntegerValueOrNull` | null, invalid-флаг |
| `getBooleanValueOrNull` | null, invalid-флаг |
| `getListStringOrNull` | null, invalid-флаг |
| `getStringValueOrNull` | null, invalid-флаг (по аналогии с описанными) |

# Авторизация

В коде **не обнаружена реализация авторизации**. Доступ к API — через Evo API.

# HTTP-слой (filter/)

- `MultiReadHttpServletRequest` — обёртка HttpServletRequest для многократного
  чтения тела (`getInputStream()`, `getReader()`, `getBodyAsString()`).
- `RequestInfoFilter` — `doFilter()`, `extractRequestInfo()`.
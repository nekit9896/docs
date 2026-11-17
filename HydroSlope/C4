# C4 Container Level — ЭВОСКАДА (СДКУ)

## Акторы

| Актор | Описание |
|---|---|
| **Неуправляющий Диспетчер** | Анализирует работу трубопровода в ОСТ |
| **Управляющий диспетчер** | Контролирует работу трубопровода в своей зоне ответственности |
| **Администратор** | Конфигурирует информационную модель системы; контролирует работоспособность модуля |
| **Администратор ЗВО.СЗИ** | Конфигурирует средство защиты информации |

## Внешние системы

| Система | Описание |
|---|---|
| **ЗВО.СЗИ** | Средство защиты информации |
| **Источники сигналов** (PC/IoT/сервисы) | Генерация событий/сигналов |

## Платформа: ЭВОСКАДА (СДКУ)

| Контейнер | Технология | Ответственность |
|---|---|---|
| **hydro-calculation** | Java, SpringBoot | Исполнение алгоритмов гидроклона |
| **Статический контент** | Directory | HTML, CSS, JavaScript |
| **hmi-frontend-hydropslope** | JavaScript, React | Клиентское приложение сервиса Гидроклон (UI) |
| **hmi-frontend-para** | JavaScript, React | Клиентская часть сервиса конфигурирования ИМ (UI сигналов) |
| **hmi-backend** | Java, SpringBoot | Обработка результатов алгоритмов для отображения в интерфейсе |
| **alarm-view-service** | Java, SpringBoot | Отображение алармов (сигналов) технологических объектов |
| **alarm-service** | Java, SpringBoot | Обработка и отображение событий |
| **hydro-history-and-model** | Java, SpringBoot | Импорт/экспорт сигналов (impepex), переключение на поток исторических данных, перерасчёт «что было бы если» |
| **data-manager** | Java, SpringBoot | Конфигурирование сигналов; предоставляет карту тегов (конфигурацию трубы) |
| **Брокер сообщений** | Apache Kafka, etc. | Поставка данных для Гидроклона по подписке; топик взаимодействия alarm-service ↔ alarm-view-service |
| **Database (PostgreSQL)** | PostgreSQL | Хранение данных информационной модели |
| **Database (Clickhouse)** | Clickhouse | Хранение исторических данных |
| **Cache** | Redis | Кэширование данных (в т.ч. карта тегов/конфигурация трубы) |
| **HashiCorp Vault** | Vault | Хранение секретов |

## Связи

### Акторы → Платформа

| От | К | Протокол / примечание |
|---|---|---|
| Неуправляющий Диспетчер | hmi-frontend-hydropslope | Загружает UI [HTTPS] |
| Управляющий диспетчер | hmi-frontend-hydropslope | Загружает UI [HTTPS] |
| Администратор | hmi-frontend-para | Загружает UI [HTTPS] |
| Администратор ЗВО.СЗИ | ЗВО.СЗИ | Получение Access Token [HTTPS] |
| Неуправляющий Диспетчер / Управляющий диспетчер | hydro-history-and-model | Импорт/Экспорт данных [XLS/HTTPS] — загрузка фрагментов истории для перерасчёта |

### Внешние системы ↔ Платформа

| От | К | Протокол / примечание |
|---|---|---|
| Источники сигналов | Брокер сообщений | Публикация сигналов [TLS+SASL/ACL] |
| hmi-frontend-hydropslope | ЗВО.СЗИ | Получение Access Token [HTTPS] |
| hmi-frontend-para | ЗВО.СЗИ | Получение Access Token [HTTPS] |
| hmi-backend | ЗВО.СЗИ | Получение Access Token [HTTPS] |

### Фронтенд / Статика / BFF

| От | К | Протокол / примечание |
|---|---|---|
| Статический контент | hmi-frontend-hydropslope | Поставляет контент [HTTPS] |
| Статический контент | hmi-frontend-para | Поставляет контент [HTTPS] |
| hmi-backend | hmi-frontend-hydropslope | Поставляет данные [HTTPS/TLS] |
| hmi-backend | hmi-frontend-para | Поставляет данные [HTTPS/TLS] |
| hmi-frontend-hydropslope | hmi-backend | Получение данных от бекенда [WebSocket] |
| hmi-frontend-para | hmi-backend | Получение данных от бекенда [WebSocket] |

### Брокер сообщений (Kafka)

| От | К | Протокол / примечание |
|---|---|---|
| alarm-view-service | Брокер сообщений | TLS AUTH:ACL [TCP 8379]; Чтение топика с данными [TLS+SASL/ACL] |
| alarm-service | Брокер сообщений | Публикация в топик для взаимодействия с alarm-view-service |
| hmi-backend | Брокер сообщений | Чтение топика с данными [TLS+SASL/ACL] |
| hydro-history-and-model | Брокер сообщений | Чтение топика с данными [TLS+SASL/ACL] |
| hmi-backend | Брокер сообщений | Авторизация TUA SASL/OAUTHBEARER + Keycloak [TLS] |

### Базы данных

| От | К | Протокол / примечание |
|---|---|---|
| hmi-backend | Database (PostgreSQL) | Запись/чтение данных, JDBC TLS verify-full, роль app_rw [TCP 8432] |
| data-manager | Database (PostgreSQL) | Запись/чтение данных, JDBC TLS verify-full, роль app_rw [TCP 8432] |
| data-manager | Database (Clickhouse) | Запись/чтение данных, JDBC TLS verify-host, роль analytics_ro_TTL [TCP 8443] |
| hydro-history-and-model | Database (Clickhouse) | Запись/чтение данных, JDBC TLS verify-host, роль analytics_ro_TTL [TCP 8443] |

### Redis (Cache) — конфигурация / теги

| От | К | Протокол / примечание |
|---|---|---|
| data-manager | Cache | **Запись** карты тегов (конфигурации трубы) [TLS AUTH:ACL [TCP 8379]] |
| alarm-service | Cache | Чтение/запись данных [TLS AUTH:ACL [TCP 8379]] |
| hmi-backend | Cache | Чтение конфигурации/тегов [TLS AUTH:ACL [TCP 8379]] (fallback → data-manager) |
| hydro-history-and-model | Cache | Чтение конфигурации/тегов [TLS AUTH:ACL [TCP 8379]] (fallback → data-manager) |
| alarm-view-service | Cache | Чтение конфигурации/тегов [TLS AUTH:ACL [TCP 8379]] (fallback → data-manager) |

### API между сервисами

| От | К | Протокол / примечание |
|---|---|---|
| hmi-backend | hydro-history-and-model | Вызов API [HTTPS] |
| hydro-history-and-model | data-manager | Вызов API [HTTPS/TLS + OAuth] — получение конфигурации |
| hydro-calculation | hmi-backend | Поставка данных расчётом алгоритмов [HTTPS/TLS] |
| alarm-service | hmi-backend / alarm-view-service | Поставка данных сообщений [HTTPS/TLS] |

### HashiCorp Vault (Auto-Auth, запрос секретов TLS [HTTPS])

| От | К |
|---|---|
| hmi-backend | HashiCorp Vault |
| hmi-frontend-para | HashiCorp Vault |
| alarm-view-service | HashiCorp Vault |
| hydro-history-and-model | HashiCorp Vault |
| data-manager | HashiCorp Vault |
| alarm-service | HashiCorp Vault |

---


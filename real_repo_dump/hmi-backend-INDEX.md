# hmi-backend — карта дампа кода (`real_repo_dump/hmi-backend`)

Навигационный слой по дампу репозитория **hmi-backend** (151 файл, 16 665 строк:
Java/Spring-бэкенд, `API.md`, страницы клиента, тесты). Источник истины по
hmi-backend (решения D45/D46, `../decisions/2026-11-25-hmi-backend-source-of-truth.md`);
`confluence/hmi-backend-descr.md` удалён. Назначение карты — быстро найти «где что»
для задач автотестирования (контракты, поведение, конфигурация), а не задокументировать
каждый метод.

**Как читать.** Дамп — один файл: секции `ФАЙЛ N/151: <путь>`, разделённые строками
`####...`. «Строки дампа» в таблице — диапазон L####-L#### внутри `hmi-backend`.
Канон `source`-ссылок в KB-фрагментах: `real_repo_dump/hmi-backend:L####-L#### (путь/файла)`.

**Скелет таблицы** генерируется: `python gen_hmi_index.py > hmi-backend-INDEX.md`
(колонка «Описание» заполняется вручную и при регенерации переносится из текущей
версии карты).

## Контрактные зоны (что читать для автотестов)

### WS-протокол `/v2/hotlink` (канон — D48, весь `Command` enum)

- `Command` enum — 14 команд: `SUBSCRIBE`, `UNSUBSCRIBE`, `UNSUBSCRIBE_ALL`,
  `SWITCH`, `PLAY`, `STOP`, `SEEK`, `SET_MILLIS_PER_TICK`, `PING`, `TAG_GET`,
  `TAG_SET`, `TAG_FIND`, `TAG_NAMES`, `OBJECT_TYPES` — **L8630-L8655**.
  `CALL_ANSWER` в enum НЕТ (G44).
- Кадр команды `CommandDto` (id, cmd, args, headers) — **L8656-L8680**; аргументы:
  `SwitchArgs`/`SwitchTarget` (HISTORY|LIVE) L8716-L8751, `PingArgs` L8699-L8715,
  `TagQueryArgs` L8752-L8773, `TagSetRequest` L8774-L8793, `ObjectTypeQueryArgs`
  L8681-L8698. Ответы: `AnswerDto`/`AnswerItem` L8582-L8629, `TagValueDto` L8794-L8851,
  `AlarmDto` L8561-L8581.
- Handshake: `HeadersHandshakeInterceptor` — **L6364-L6418** (атрибуты сессии: `IP`,
  `x-user-fullname`, `queryParameterMap`; отказ 503, пока `!hmiEvoService.isReady()`).
- Обслуживание сессии: `HotlinkSessionV2` — **L7445-L8083** (разбор команд;
  `SWITCH` → `switchToLive()`/`switchToHistory(start, finish, millisPerTick)` —
  L7820-L7836); общая база `HotlinkSessionBase` L6967-L7444 (**мерж query-параметров
  URL с `headers` кадра** — L7120-L7125); handler-и `HotlinkWebSocketHandlerBase`
  L8179-L8532, `HotlinkWebSocketHandlerV2` L8533-L8560.
- Регистрация эндпоинтов: `HotlinkWebSocketConfig` — **L1427-L1476** (`/hotlink` — V1,
  `/v2/hotlink` — V2).
- V1 (legacy, ЦСПА): `HotlinkSession` L6681-L6966, `HotlinkWebSocketHandler` L8152-L8178.
- Modelling (вне объёма клиента, D48): маршрутизация по query `modelSessionId` —
  `HotlinkWebSocketHandlerV2Routed` **L9849-L9914**, сессия `HotlinkSessionV2Modelling`
  L9746-L9815.

### Авторизация `X-USER-*` (канон — D47)

- `RequestUtils.getAnyUserIdentity` — **L11652-L11693**: порядок заголовков
  `X-USER-LOGIN` → `X-USER-FULLNAME` → `x-user-fullname` → `X-USER-ID`, фолбэк —
  query-параметр `x-user-fullname`, затем `URLDecoder.decode(user)` (query-значение
  декодируется **дважды** — отсюда двойное кодирование `%2520` у страницы).
- `RequestInfoFilter` — L6282-L6363 (IP клиента, identity, логирование запросов).
- Образец кодирования — `tag-monitor.html`: сборка URL L15045-L15055
  (`/v2/hotlink?${params}`), `encodeURIComponent(userId)` L15478-L15490.

### REST (канон — D38, семейство `tag-*` V2)

- V2: `GetSetControllerV2` — **L2878-L3070** (`/v2/tag-set`, `/v2/tags-set`,
  `/v2/tag-get`, `/v2/tags-get`), `TagInfoControllerV2` L3071-L3180,
  `HistoryV2Controller` L2121-L2228 (`/v2/tags-get-history`).
- V1: `GetSetController` L1678-L2002, `HistoryV1Controller` L2003-L2120,
  `TagInfoController` L2528-L2839, `TagInfoEditController` L2840-L2877.
- Метаданные/сессии: `MetadataController` L2229-L2508, `SessionsController` L9176-L9225.
- Готовность сервера: `ServerReadyRestInterceptor` L10981-L11061 +
  аннотация `RequireServerReady` L11694-L11719 (503 до прогрева).
- Ошибки: `ControllerErrorsHandler` L5927-L6032 (маппинг исключений → HTTP-статусы).

### Страницы клиента и документация контракта

- `tag-monitor.html` (V2; **образец подключения**: query `X-USER-*`, `SWITCH LIVE`,
  плеер истории) — **L14341-L16396**.
- `tag-monitor-v1.html` (V1: `/hotlink`, `x-user-fullname`) — L12468-L14340.
- `client/index.html` (демо V1) — L948-L1193; `API.md` L208-L409 и `API.html`
  L12014-L12467 — текстовая/веб-документация WS+REST контракта.
- `RootController` — **L2509-L2527**: `GET /` → редирект `/tag-monitor.html`.
  Ловушка: `WS_URL` без пути `/v2/hotlink` приводит к ошибке
  `scheme isn't ws or wss` (сервер отвечает редиректом на HTML).

### Потоки данных и история

`DataStreamManager` L3855-L3891; `LiveDataStreamProvider` L4782-L5136;
`HistoryDataStreamProvider` L3958-L4246; `HistoryStreamHandler` L4247-L4781;
`TagValueStreamHandler` L5184-L5230; `TagAlarmStreamHandler` L5137-L5183;
`TimelineBucket` L5231-L5291.

### Инфраструктура и конфигурация

`application.yml` L11896-L12013 (порт, Kafka, ClickHouse, WS); `HmiEvoService`
(isReady) L10898-L10942; `Minuteman` (killStaleSessions, контроль живых сессий)
L10943-L10980; Kafka: `KafkaSender` L8882-L8910, `TopicRouteConfig` L11468-L11584;
`AppWarmUp` (прогрев) L10349-L10602.

Факты с полными описаниями — `../specs/knowledge/hmi-backend/` (KB-HMI-*,
`source`-ссылки на строки дампа); решения — `../decisions/2026-11-25-*.md`,
расхождения — `../meta/discrepancies-2026-11-25.md` (G44+).

## Все файлы (151)

| № | Файл репозитория | Строки дампа | Подсказка (авто) | Описание (вручную) |
|---|---|---|---|---|
| 1/151 | `API.md` | L208-L409 | ## Информация о тегах | Контракт WS+REST: типы тегов, кадры команд, заголовки X-USER; исторический текстовый источник контракта |
| 2/151 | `Dockerfile-redos` | L410-L436 | FROM OPENJDK_17_BASE_IMAGE | Сборка образа под ОС РЕД ОС (OpenJDK 17) |
| 3/151 | `README.md` | L437-L536 | # Переменные окружения | Переменные окружения и запуск сервиса |
| 4/151 | `pom.xml` | L537-L768 | <?xml version="1.0" encoding="UTF-8"?> | Maven-сборка (Spring Boot, protobuf, ClickHouse-драйвер) |
| 5/151 | `.idea/misc.xml` | L769-L790 | <?xml version="1.0" encoding="UTF-8"?> | Служебный файл IDE (в дампе для полноты) |
| 6/151 | `.idea/vcs.xml` | L791-L802 | <?xml version="1.0" encoding="UTF-8"?> | Служебный файл IDE (в дампе для полноты) |
| 7/151 | `.idea/workspace.xml` | L803-L909 | <?xml version="1.0" encoding="UTF-8"?> | Служебный файл IDE (в дампе для полноты) |
| 8/151 | `.idea/inspectionProfiles/Project_Default.xml` | L910-L947 | <component name="InspectionProjectProfileManager"> | Служебный файл IDE (в дампе для полноты) |
| 9/151 | `client/index.html` | L948-L1193 | <!DOCTYPE html> | Демо-страница WS-клиента V1: `ws://<host>/hotlink`, ручная отправка кадров |
| 10/151 | `src/main/java/tnt/tnscada/hmi/HmiApp.java` | L1194-L1238 | @Component | Точка входа Spring Boot приложения |
| 11/151 | `src/main/java/tnt/tnscada/hmi/SwaggerConfig.java` | L1239-L1269 | @Configuration | Конфигурация Swagger UI; ссылки на /tag-monitor.html и /API.html |
| 12/151 | `src/main/java/tnt/tnscada/hmi/configuration/AppConfig.java` | L1270-L1401 | @RequiredArgsConstructor | Общая конфигурация бинов (клиенты, ObjectMapper) |
| 13/151 | `src/main/java/tnt/tnscada/hmi/configuration/CacheConfiguration.java` | L1402-L1426 | @Configuration | Кеши (core-meta-data-store и др.) |
| 14/151 | `src/main/java/tnt/tnscada/hmi/configuration/HotlinkWebSocketConfig.java` | L1427-L1476 | @Configuration | Регистрация WS-эндпоинтов: /hotlink (V1) и /v2/hotlink (V2) + handshake-interceptor |
| 15/151 | `src/main/java/tnt/tnscada/hmi/configuration/WebConfig.java` | L1477-L1530 | @Configuration | Web-конфигурация: CORS, статические ресурсы |
| 16/151 | `src/main/java/tnt/tnscada/hmi/controller/AuditFacadeController.java` | L1531-L1572 | @Slf4j | REST: фасад аудита (Grant-Access-Audit) |
| 17/151 | `src/main/java/tnt/tnscada/hmi/controller/ControllerUtils.java` | L1573-L1628 | public class ControllerUtils { | Утилиты контроллеров: разбор параметров, имя пользователя |
| 18/151 | `src/main/java/tnt/tnscada/hmi/controller/DiagController.java` | L1629-L1677 | @Slf4j | REST: диагностика hotlink-сессий (HotlinkDiagDTO) |
| 19/151 | `src/main/java/tnt/tnscada/hmi/controller/GetSetController.java` | L1678-L2002 | @Slf4j | REST V1: чтение/запись тегов (tag-get/tag-set) |
| 20/151 | `src/main/java/tnt/tnscada/hmi/controller/HistoryV1Controller.java` | L2003-L2120 | @Slf4j | REST V1: история тегов |
| 21/151 | `src/main/java/tnt/tnscada/hmi/controller/HistoryV2Controller.java` | L2121-L2228 | @Slf4j | REST V2: история (/v2/tags-get-history, ClickHouse) |
| 22/151 | `src/main/java/tnt/tnscada/hmi/controller/MetadataController.java` | L2229-L2508 | @RestController | REST: метаданные (объекты, типы, проекты; кеш) |
| 23/151 | `src/main/java/tnt/tnscada/hmi/controller/RootController.java` | L2509-L2527 | @Controller | GET / → редирект /tag-monitor.html (ловушка для WS_URL без пути) |
| 24/151 | `src/main/java/tnt/tnscada/hmi/controller/TagInfoController.java` | L2528-L2839 | @RestController | REST V1: информация о тегах (поиск, свойства, тег-типы) |
| 25/151 | `src/main/java/tnt/tnscada/hmi/controller/TagInfoEditController.java` | L2840-L2877 | @RestController | REST: редактирование объектов/тегов (create/delete) |
| 26/151 | `src/main/java/tnt/tnscada/hmi/controller/v2/GetSetControllerV2.java` | L2878-L3070 | @Slf4j | REST V2 (канон D38): /v2/tag-set, /v2/tags-set, /v2/tag-get, /v2/tags-get |
| 27/151 | `src/main/java/tnt/tnscada/hmi/controller/v2/TagInfoControllerV2.java` | L3071-L3180 | @RestController | REST V2: информация о тегах (v2-представления) |
| 28/151 | `src/main/java/tnt/tnscada/hmi/data/DataService.java` | L3181-L3279 | @Service | Сервис данных V1 (фасад чтения/записи) |
| 29/151 | `src/main/java/tnt/tnscada/hmi/data/DataServiceBase.java` | L3280-L3606 | @Slf4j | Базовая реализация чтения/записи значений тегов |
| 30/151 | `src/main/java/tnt/tnscada/hmi/data/DataServiceV2.java` | L3607-L3788 | @Service | Сервис данных V2 (строковые представления значений API V2) |
| 31/151 | `src/main/java/tnt/tnscada/hmi/data/HistoryServiceHmi.java` | L3789-L3854 | @Service | Сервис истории для HMI (выборки ClickHouse) |
| 32/151 | `src/main/java/tnt/tnscada/hmi/datastream/DataStreamManager.java` | L3855-L3891 | @Slf4j | Менеджер стрим-провайдеров (live/history/model) |
| 33/151 | `src/main/java/tnt/tnscada/hmi/datastream/DataStreamProvider.java` | L3892-L3957 | public interface DataStreamProvider extends Closeable { | Интерфейс стрим-провайдера |
| 34/151 | `src/main/java/tnt/tnscada/hmi/datastream/HistoryDataStreamProvider.java` | L3958-L4246 | @Slf4j | Провайдер потока истории (плеер, перемотка) |
| 35/151 | `src/main/java/tnt/tnscada/hmi/datastream/HistoryStreamHandler.java` | L4247-L4781 | @Slf4j | Обработчик потока истории (таймлайн, watermark) |
| 36/151 | `src/main/java/tnt/tnscada/hmi/datastream/LiveDataStreamProvider.java` | L4782-L5136 | @Slf4j | Провайдер live-потока (текущие значения подписок) |
| 37/151 | `src/main/java/tnt/tnscada/hmi/datastream/TagAlarmStreamHandler.java` | L5137-L5183 | @Slf4j | Обработчик потока алармов |
| 38/151 | `src/main/java/tnt/tnscada/hmi/datastream/TagValueStreamHandler.java` | L5184-L5230 | @Slf4j | Обработчик потока значений тегов |
| 39/151 | `src/main/java/tnt/tnscada/hmi/datastream/TimelineBucket.java` | L5231-L5291 | public class TimelineBucket<TValue> { | Бакет таймлайна (агрегация значений по времени) |
| 40/151 | `src/main/java/tnt/tnscada/hmi/dto/HistoryISORequestDTO.java` | L5292-L5332 | @Data | DTO запроса истории (ISO-время) |
| 41/151 | `src/main/java/tnt/tnscada/hmi/dto/HistoryRecordShortNameDTO.java` | L5333-L5381 | @Data | DTO краткой записи истории |
| 42/151 | `src/main/java/tnt/tnscada/hmi/dto/HistoryRequestDTO.java` | L5382-L5417 | @Data | DTO запроса истории (timestamp) |
| 43/151 | `src/main/java/tnt/tnscada/hmi/dto/HotlinkDiagDTO.java` | L5418-L5464 | @Data | DTO диагностики hotlink-сессий |
| 44/151 | `src/main/java/tnt/tnscada/hmi/dto/RecordValueISO.java` | L5465-L5523 | @Data | DTO значения записи (ISO-время) |
| 45/151 | `src/main/java/tnt/tnscada/hmi/dto/SummaryIntervalsStatDTO.java` | L5524-L5549 | @Data | DTO статистики интервалов |
| 46/151 | `src/main/java/tnt/tnscada/hmi/dto/SummaryStatDTO.java` | L5550-L5573 | @Data | DTO сводной статистики |
| 47/151 | `src/main/java/tnt/tnscada/hmi/dto/TagInfoRichDTO.java` | L5574-L5602 | @Data | DTO расширенной информации о теге |
| 48/151 | `src/main/java/tnt/tnscada/hmi/dto/TagSetAndWaitDTO.java` | L5603-L5631 | @Data | DTO «записать и дождаться» (tag-set-and-wait) |
| 49/151 | `src/main/java/tnt/tnscada/hmi/dto/copypasted/AuditEventLogApi.java` | L5632-L5675 | @ToString | DTO события аудита (копия из внешнего API-контракта) |
| 50/151 | `src/main/java/tnt/tnscada/hmi/dto/copypasted/ErrorMessage.java` | L5676-L5703 | @Data | DTO сообщения об ошибке (копия контракта) |
| 51/151 | `src/main/java/tnt/tnscada/hmi/dto/copypasted/ErrorResponseApi.java` | L5704-L5723 | @Getter | DTO ответа с ошибкой (копия контракта) |
| 52/151 | `src/main/java/tnt/tnscada/hmi/dto/copypasted/GenerateAlarmDto.java` | L5724-L5772 | @Data | DTO генерации аларма (копия контракта) |
| 53/151 | `src/main/java/tnt/tnscada/hmi/dto/copypasted/TnMsgKeyDto.java` | L5773-L5803 | @Data | DTO ключа TnMsg (копия контракта) |
| 54/151 | `src/main/java/tnt/tnscada/hmi/dto/metadata/ObjectResponse.java` | L5804-L5825 | @Data | DTO объекта метаданных |
| 55/151 | `src/main/java/tnt/tnscada/hmi/dto/metadata/ObjectTypeResponse.java` | L5826-L5845 | @Data | DTO типа объекта |
| 56/151 | `src/main/java/tnt/tnscada/hmi/dto/metadata/ProjectResponse.java` | L5846-L5862 | @Data | DTO проекта |
| 57/151 | `src/main/java/tnt/tnscada/hmi/errors/ApplicationLogicException.java` | L5863-L5876 | public class ApplicationLogicException extends RuntimeException { | Ошибка бизнес-логики |
| 58/151 | `src/main/java/tnt/tnscada/hmi/errors/BadRequestException.java` | L5877-L5894 | public class BadRequestException extends RuntimeException { | Некорректный запрос (400) |
| 59/151 | `src/main/java/tnt/tnscada/hmi/errors/ControllerDefaultErrorsHandler.java` | L5895-L5926 | @Slf4j | Дефолтный @ControllerAdvice (необработанные ошибки) |
| 60/151 | `src/main/java/tnt/tnscada/hmi/errors/ControllerErrorsHandler.java` | L5927-L6032 | @Slf4j | Маппинг исключений → HTTP-статусы/ErrorMessage |
| 61/151 | `src/main/java/tnt/tnscada/hmi/errors/ErrorMessage.java` | L6033-L6055 | @Data | DTO сообщения об ошибке (внутренний формат) |
| 62/151 | `src/main/java/tnt/tnscada/hmi/errors/ForbiddenException.java` | L6056-L6073 | public class ForbiddenException extends RuntimeException { | Доступ запрещён (403; паттерны X-USER) |
| 63/151 | `src/main/java/tnt/tnscada/hmi/errors/NotFoundException.java` | L6074-L6091 | public class NotFoundException extends RuntimeException { | Не найдено (404) |
| 64/151 | `src/main/java/tnt/tnscada/hmi/errors/TagErrorMessage.java` | L6092-L6114 | public record TagErrorMessage( | record ошибки по конкретному тегу |
| 65/151 | `src/main/java/tnt/tnscada/hmi/errors/TagNotAvailable.java` | L6115-L6132 | public class TagNotAvailable extends RuntimeException { | Тег недоступен |
| 66/151 | `src/main/java/tnt/tnscada/hmi/errors/TagNotFoundException.java` | L6133-L6146 | public class TagNotFoundException extends RuntimeException { | Тег не найден |
| 67/151 | `src/main/java/tnt/tnscada/hmi/errors/TagSetException.java` | L6147-L6160 | public class TagSetException extends RuntimeException { | Ошибка записи тега |
| 68/151 | `src/main/java/tnt/tnscada/hmi/errors/ValueConversionException.java` | L6161-L6174 | public class ValueConversionException extends RuntimeException { | Ошибка конвертации значения |
| 69/151 | `src/main/java/tnt/tnscada/hmi/errors/WebClientErrorException.java` | L6175-L6205 | @Getter | Ошибка вызова внешнего сервиса (с кодом ответа) |
| 70/151 | `src/main/java/tnt/tnscada/hmi/filter/MultiReadHttpServletRequest.java` | L6206-L6281 | public class MultiReadHttpServletRequest extends HttpServletRequestWrapper { | Обёртка request для многократного чтения body |
| 71/151 | `src/main/java/tnt/tnscada/hmi/filter/RequestInfoFilter.java` | L6282-L6363 | @Component | Фильтр: IP + identity пользователя, логирование запросов |
| 72/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HeadersHandshakeInterceptor.java` | L6364-L6418 | @Component | WS-handshake: атрибуты IP/x-user-fullname/queryParameterMap; 503 если сервер не готов (контрактная зона, D47) |
| 73/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HotlinkMessageLogger.java` | L6419-L6624 | Логирование всех входящих и исходящих WebSocket сообщений v1 и v2. | Трейс-лог всех WS-кадров v1/v2 (DEBUG/TRACE) |
| 74/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HotlinkService.java` | L6625-L6680 | @Slf4j | Управление hotlink-сессиями (реестр, рассылка) |
| 75/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HotlinkSession.java` | L6681-L6966 | Первая версия вебсокета для ЦСПА only, legacy | WS-сессия V1 (legacy, ЦСПА; вне объёма клиента) |
| 76/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HotlinkSessionBase.java` | L6967-L7444 | @Slf4j | База сессий: мерж query-параметров URL с headers кадра (L7120-L7125), общий разбор команд |
| 77/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HotlinkSessionV2.java` | L7445-L8083 | Вторая версия вебсокета, Использовать ее | WS-сессия V2 (канон D48): все команды Command enum, SWITCH LIVE/HISTORY — L7820-L7836 |
| 78/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HotlinkWaitValueSession.java` | L8084-L8151 | @Slf4j | Служебная сессия «дождаться значение» (tag-set-and-wait) |
| 79/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HotlinkWebSocketHandler.java` | L8152-L8178 | @Slf4j | WS-handler V1 (/hotlink) |
| 80/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HotlinkWebSocketHandlerBase.java` | L8179-L8532 | @Slf4j | Базовый WS-handler (подключения, жизненный цикл сессий) |
| 81/151 | `src/main/java/tnt/tnscada/hmi/hotlink/HotlinkWebSocketHandlerV2.java` | L8533-L8560 | @Slf4j | WS-handler V2 (/v2/hotlink) |
| 82/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/AlarmDto.java` | L8561-L8581 | @Data | DTO аларма в потоке |
| 83/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/AnswerDto.java` | L8582-L8610 | @Data | DTO ответа на команду (SUB_ANSWER и др.) |
| 84/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/AnswerItem.java` | L8611-L8629 | @Data | Элемент ответа (тег + значение/статус) |
| 85/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/Command.java` | L8630-L8655 | public enum Command { | enum команд WS-протокола: 14 команд (D48, G44) |
| 86/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/CommandDto.java` | L8656-L8680 | @Data | Кадр команды: id, cmd, args, headers |
| 87/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/ObjectTypeQueryArgs.java` | L8681-L8698 | @Data | Аргументы OBJECT_TYPES (typePattern, sorted) |
| 88/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/PingArgs.java` | L8699-L8715 | @Data | Аргументы PING (id → pong с тем же id) |
| 89/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/SwitchArgs.java` | L8716-L8738 | @Data | Аргументы SWITCH (target, start, finish, millisPerTick) |
| 90/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/SwitchTarget.java` | L8739-L8751 | public enum SwitchTarget { | enum цели SWITCH: HISTORY \| LIVE |
| 91/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/TagQueryArgs.java` | L8752-L8773 | @Data | Аргументы TAG_GET/TAG_FIND (список тегов) |
| 92/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/TagSetRequest.java` | L8774-L8793 | @Data | Элемент TAG_SET (tag + data) |
| 93/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/TagValueDto.java` | L8794-L8851 | @Getter | DTO значения тега в потоке |
| 94/151 | `src/main/java/tnt/tnscada/hmi/hotlink/dto/TagValueRawDto.java` | L8852-L8881 | @Data | DTO «сырого» значения (protobuf-представление) |
| 95/151 | `src/main/java/tnt/tnscada/hmi/kafka/KafkaSender.java` | L8882-L8910 | @Slf4j | Отправка сообщений в Kafka |
| 96/151 | `src/main/java/tnt/tnscada/hmi/modelling/EvoCoreDelegated.java` | L8911-L9000 | @Slf4j | Делегирование в Evo-ядро (режим моделирования) |
| 97/151 | `src/main/java/tnt/tnscada/hmi/modelling/ModellingKafkaTnMsgSender.java` | L9001-L9175 | public class ModellingKafkaTnMsgSender extends KafkaTnMsgSender { | Kafka-отправитель TnMsg моделирования (переопределённые маршруты) |
| 98/151 | `src/main/java/tnt/tnscada/hmi/modelling/controller/SessionsController.java` | L9176-L9225 | @Slf4j | REST: сессии моделирования (создание/управление) |
| 99/151 | `src/main/java/tnt/tnscada/hmi/modelling/datastream/MockDataStreamProvider.java` | L9226-L9357 | @Slf4j | Мок-провайдер потока (тесты моделирования) |
| 100/151 | `src/main/java/tnt/tnscada/hmi/modelling/datastream/ModelDataStreamProvider.java` | L9358-L9722 | @Slf4j | Провайдер потока моделируемой сессии |
| 101/151 | `src/main/java/tnt/tnscada/hmi/modelling/dto/SessionToServiceDTO.java` | L9723-L9745 | @Data | DTO сессии моделирования для сервиса |
| 102/151 | `src/main/java/tnt/tnscada/hmi/modelling/hotlink/HotlinkSessionV2Modelling.java` | L9746-L9815 | @Slf4j | WS-сессия V2 режима моделирования (вне объёма клиента) |
| 103/151 | `src/main/java/tnt/tnscada/hmi/modelling/hotlink/HotlinkWebSocketHandlerV2Modelling.java` | L9816-L9848 | @Slf4j | WS-handler моделирования |
| 104/151 | `src/main/java/tnt/tnscada/hmi/modelling/hotlink/HotlinkWebSocketHandlerV2Routed.java` | L9849-L9914 | @Slf4j | Маршрутизатор: query modelSessionId → modelling-handler, иначе live |
| 105/151 | `src/main/java/tnt/tnscada/hmi/modelling/service/ModelEvoApiManager.java` | L9915-L10155 | @Service | Менеджер Evo API для моделирования |
| 106/151 | `src/main/java/tnt/tnscada/hmi/modelling/service/SessionManager.java` | L10156-L10222 | @Service | Реестр сессий моделирования |
| 107/151 | `src/main/java/tnt/tnscada/hmi/proto/ProtoConverter.java` | L10223-L10259 | public class ProtoConverter { | Конвертация protobuf ↔ DTO |
| 108/151 | `src/main/java/tnt/tnscada/hmi/proto/ProtoValidator.java` | L10260-L10348 | public class ProtoValidator { | Валидация protobuf-сообщений |
| 109/151 | `src/main/java/tnt/tnscada/hmi/service/AppWarmUp.java` | L10349-L10602 | @Slf4j | Прогрев приложения (кеши, подписки) |
| 110/151 | `src/main/java/tnt/tnscada/hmi/service/AuditFacadeService.java` | L10603-L10722 | @Service | Сервис аудита (Grant-Access-Audit) |
| 111/151 | `src/main/java/tnt/tnscada/hmi/service/DiagService.java` | L10723-L10764 | @Service | Сервис диагностики |
| 112/151 | `src/main/java/tnt/tnscada/hmi/service/HistoryServiceLegacy.java` | L10765-L10897 | @Service public class HistoryServiceLegacy { | Легаси-сервис истории (V1) |
| 113/151 | `src/main/java/tnt/tnscada/hmi/service/HmiEvoService.java` | L10898-L10942 | @Slf4j | Подключение к Evo-ядру, isReady() (гейт handshake и REST) |
| 114/151 | `src/main/java/tnt/tnscada/hmi/service/Minuteman.java` | L10943-L10980 | @Service | Сторож сессий: killStaleSessions, контроль пингов |
| 115/151 | `src/main/java/tnt/tnscada/hmi/service/ServerReadyRestInterceptor.java` | L10981-L11061 | @Component | REST-interceptor: 503 пока сервер не готов (@RequireServerReady) |
| 116/151 | `src/main/java/tnt/tnscada/hmi/service/TagInfoEditService.java` | L11062-L11282 | @Service | Сервис редактирования объектов/тегов |
| 117/151 | `src/main/java/tnt/tnscada/hmi/service/TagInfoService.java` | L11283-L11467 | @Service | Сервис информации о тегах |
| 118/151 | `src/main/java/tnt/tnscada/hmi/service/TopicRouteConfig.java` | L11468-L11584 | @Slf4j | Переопределение маршрутов Kafka-топиков (Topic-Route) |
| 119/151 | `src/main/java/tnt/tnscada/hmi/utils/JsonUtils.java` | L11585-L11621 | public class JsonUtils { | Утилиты JSON |
| 120/151 | `src/main/java/tnt/tnscada/hmi/utils/LimitedMap.java` | L11622-L11651 | public class LimitedMap<K, V> extends LinkedHashMap<K, V> { | LRU-карта с ограничением размера |
| 121/151 | `src/main/java/tnt/tnscada/hmi/utils/RequestUtils.java` | L11652-L11693 | public class RequestUtils { | Извлечение IP и identity: X-USER-заголовки → query x-user-fullname → URLDecoder.decode (двойная декодировка, D47) |
| 122/151 | `src/main/java/tnt/tnscada/hmi/utils/RequireServerReady.java` | L11694-L11719 | @Target({ElementType.METHOD, ElementType.TYPE}) | Аннотация «только для готового сервера» |
| 123/151 | `src/main/java/tnt/tnscada/hmi/utils/TagValueUtils.java` | L11720-L11827 | @Slf4j | Утилиты значений тегов (нормализация, конвертация) |
| 124/151 | `src/main/java/tnt/tnscada/hmi/utils/TickCollector.java` | L11828-L11874 | public class TickCollector { | Сборщик тиков (интервалы значений) |
| 125/151 | `src/main/java/tnt/tnscada/hmi/utils/logging/PingPongLogger.java` | L11875-L11895 | @Slf4j | Логирование PING/PONG |
| 126/151 | `src/main/resources/application.yml` | L11896-L12013 | server: | Конфигурация Spring: порт, Kafka, ClickHouse, WS |
| 127/151 | `src/main/resources/public/API.html` | L12014-L12467 | <!doctype html> | Веб-документация WS+REST контракта (вёрстка API.md) |
| 128/151 | `src/main/resources/public/tag-monitor-v1.html` | L12468-L14340 | <!DOCTYPE html> | Tag Monitor V1: WS /hotlink, x-user-fullname в query |
| 129/151 | `src/main/resources/public/tag-monitor.html` | L14341-L16396 | <!DOCTYPE html> | Tag Monitor V2 (образец подключения, D47/D48): /v2/hotlink?X-USER-*, SWITCH LIVE/HISTORY, плеер, sync-команды |
| 130/151 | `src/test/java/tnt/tnscada/hmi/LoadTest.java` | L16397-L16486 | Запускаем вручную | Ручной нагрузочный тест WS |
| 131/151 | `src/test/java/tnt/tnscada/hmi/TagSetWaitTest.java` | L16487-L16522 | public class TagSetWaitTest { | Тест tag-set-and-wait |
| 132/151 | `src/test/java/tnt/tnscada/hmi/configuration/AppTestConfig.java` | L16523-L16760 | @TestConfiguration | Тестовая конфигурация бинов |
| 133/151 | `src/test/java/tnt/tnscada/hmi/configuration/TopologyTestConfig.java` | L16761-L17032 | public class TopologyTestConfig { | Тестовая топология Kafka |
| 134/151 | `src/test/java/tnt/tnscada/hmi/configuration/WebSocketTestConfig.java` | L17033-L17079 | @TestConfiguration | Тестовая WS-конфигурация |
| 135/151 | `src/test/java/tnt/tnscada/hmi/controller/AuditFacadeTest.java` | L17080-L17149 | @SpringBootTest( | Тест AuditFacadeController |
| 136/151 | `src/test/java/tnt/tnscada/hmi/controller/GetSetV1Test.java` | L17150-L17458 | @SpringBootTest( | Тест GetSetController (V1) |
| 137/151 | `src/test/java/tnt/tnscada/hmi/controller/GetSetV2Test.java` | L17459-L17757 | @SpringBootTest( | Тест GetSetControllerV2 (V2) |
| 138/151 | `src/test/java/tnt/tnscada/hmi/controller/HistoryV1Test.java` | L17758-L17906 | @SpringBootTest( | Тест HistoryV1Controller |
| 139/151 | `src/test/java/tnt/tnscada/hmi/controller/HistoryV2Test.java` | L17907-L18057 | @SpringBootTest( | Тест HistoryV2Controller |
| 140/151 | `src/test/java/tnt/tnscada/hmi/controller/TagInfoEditTest.java` | L18058-L18140 | @SpringBootTest( | Тест TagInfoEditController |
| 141/151 | `src/test/java/tnt/tnscada/hmi/controller/TagInfoTest.java` | L18141-L18418 | @SpringBootTest( | Тест TagInfoController |
| 142/151 | `src/test/java/tnt/tnscada/hmi/controller/TagInfoV2Test.java` | L18419-L18491 | @SpringBootTest( | Тест TagInfoControllerV2 |
| 143/151 | `src/test/java/tnt/tnscada/hmi/service/DataServiceTest.java` | L18492-L18610 | public class DataServiceTest { | Юнит-тест DataService |
| 144/151 | `src/test/java/tnt/tnscada/hmi/service/TopicRouteConfigTest.java` | L18611-L18699 | Переменные окружения заданы вручную, чтобы проверить, как оно будет работать в реальном окружении Можно раском | Тест TopicRouteConfig |
| 145/151 | `src/test/java/tnt/tnscada/hmi/util/MsgHelper.java` | L18700-L18775 | public class MsgHelper { | Помощник сообщений для тестов |
| 146/151 | `src/test/java/tnt/tnscada/hmi/websocket/HotlinkHandlerTest.java` | L18776-L18994 | @SpringBootTest( | Тест WS-handler V1 |
| 147/151 | `src/test/java/tnt/tnscada/hmi/websocket/HotlinkV2HandlerTest.java` | L18995-L19221 | @SpringBootTest( | Тест WS-handler V2 (протокол команд) |
| 148/151 | `src/test/resources/application.yml` | L19222-L19341 | server: | Тестовая конфигурация Spring |
| 149/151 | `src/test/resources/requests/http-client.env.json` | L19342-L19358 | { | Переменные HTTP-клиента IDE (env) |
| 150/151 | `src/test/resources/requests/tag-getset.http` | L19359-L19419 | ### TAG GETS BY LIST | HTTP-запросы tag-get/set для IDE-клиента |
| 151/151 | `src/test/resources/requests/tag-info.http` | L19420-L19437 | ### TAG NAMES | HTTP-запросы tag-info/tag-names для IDE-клиента |

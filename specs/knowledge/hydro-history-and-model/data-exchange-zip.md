---
id: KB-HM-ZIP-001
title: Экспорт/импорт данных сессий в ZIP (DataExchangeService)
service: hydro-history-and-model
group: data-exchange
source: confluence/repo_description_hydro-history-and-model#3.6, #6.5, #8.1
requires: [KB-HM-STORAGE-001]
related: [KB-HM-CLEANUP-001, KB-HM-OVERVIEW-001]
status: verified
---

# Экспорт/импорт данных сессий в ZIP

Контроллер `DataExchangeController` — ручно-отладочный экспорт-импорт данных
сессий. Сущности: `ExportMetadata`, `ImportResult`, `SessionMetadataDto`,
`SessionRecord`, `AlarmRecord`.

## Экспорт: `DataExchangeService.exportToZip(sessionId, userInfo)`

1. Загружает сессию из БД через `SessionManagerRepository.findById()`.
2. Читает записи из ClickHouse: `recordReader.readSessionRecords(sessionId)` —
   значения, `recordReader.readAlarmRecords(sessionId)` — алармы.
3. Создаёт ZIP-архив:
   - `metadata.json` — `ExportMetadata(sessionId, sessionRecords.size(), alarmRecords.size())`;
   - `session_metadata.json` — `SessionMetadataDto` из `SessionManagerEntity`;
   - `session_records.json` — список `SessionRecord`;
   - `alarm_records.json` — список `AlarmRecord`.
4. Возвращает байтовый массив ZIP-архива.

## Импорт: `DataExchangeService.importFromZip(zipStream, userInfo, overwrite)`

1. `parseArchive(zipStream)`: читает все файлы ZIP; ожидает наличие
   `metadata.json`, `session_metadata.json`, `session_records.json`,
   `alarm_records.json`; отсутствие файла →
   `ApiException(HttpStatus.BAD_REQUEST, "INVALID_ARCHIVE", ...)`.
2. `ExportMetadata` — `sessionId`, `sessionRecordsCount`, `alarmRecordsCount`.
3. `SessionMetadataDto` — `name`, `mode`, `source`, `startTime`, `endTime`,
   `durationSeconds`, `status`, `errorMessage`, `topicValue`, `topicAlarm`,
   `createdAt`, `userId`, `userName`, `created_dto`, `meta`.
4. Обработка сессии:
   - `overwrite = true`: проверка существования в БД; если есть — удаление
     партиций в ClickHouse через `partitionService.dropPartitionIfExists()`,
     обновление существующей `SessionManagerEntity` или создание новой, сохранение;
   - `overwrite = false`: создание новой `SessionManagerEntity`.
5. Метаданные из архива: `setSource(SourceMode.imported)`,
   `setUserId(userInfo.getId())`, `setUserName(userInfo.getFullName())`,
   `setCreatedAt(Instant.now())`.
6. Если `targetSessionId != originalSessionId` — обновляет `sessionId` у всех записей.
7. Запись в ClickHouse: `writeInBatches(records, writer)` делит на батчи по
   **`WRITE_BATCH_SIZE = 10_000`**, для каждого — `writer.writeBatch(batch)`
   (`ClickHouseSessionRecordsWriter` / `ClickHouseAlarmRecordsWriter`).

## Служебные DTO

- `ExportMetadata`: `sessionId`, `sessionRecordsCount`, `alarmRecordsCount`.
- `ImportResult`: `sessionId` (после импорта), `sessionRecordsImported`,
  `alarmRecordsImported`, `overwritten` (флаг перезаписи существующей сессии).

Импортированные сессии (`source = imported`) подлежат TTL-очистке
(KB-HM-CLEANUP-001).
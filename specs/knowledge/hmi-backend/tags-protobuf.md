---
id: KB-HMI-TAG-001
title: Тег, типы значений, Protobuf-схемы, ProtoValidator/ProtoConverter
service: hmi-backend
group: data
source: confluence/hmi-backend-descr.md#«Тег», «Protobuf-схемы»
requires: [KB-HMI-OVERVIEW-001]
related: [KB-HMI-ERR-001, KB-HMI-REST-VAL-001]
status: verified
---

# Тег и форматы данных

**Тег** — уникальный адрес в адресном пространстве EVOSCADA. Сигналы, параметры,
команды, коэффициенты — всё это значения тегов. Каждый тег имеет `value` и
`attributes` (метаданные: алармы, шкалы, ЕИ, принадлежность к объекту).

## Типы значений

| Тип | Protobuf field | Plotable |
|---|---|---|
| BOOL | `boolVar` | ✅ |
| INT | `intVar` | ✅ |
| LONG | `longVar` | ✅ |
| FLOAT | `floatVar` | ✅ |
| DOUBLE | `doubleVar` | ✅ |
| STRING | `stringVar` | ❌ |
| BYTES | `bytesVar` | ❌ |
| TIME | `timeVar` | ❌ |
| DYN_BOOL | `dynBoolVar` | ❌ |
| DYN_INT | `dynIntVar` | ❌ |
| DYN_LONG | `dynLongVar` | ❌ |
| DYN_FLOAT | `dynFloatVar` | ❌ |
| DYN_DOUBLE | `dynDoubleVar` | ❌ |
| DYN_STRING | `dynStringVar` | ❌ |
| DYN_TIME | `dynTimeVar` | ❌ |
| DYN_BYTES | `dynBytesVar` | ❌ |

> При записи значения (`TAG_SET`) сервис валидирует соответствие типа тега и типа
> значения через `ProtoValidator.validate()`. Несоответствие →
> `ValueConversionException` (HTTP 400).

## Protobuf-схемы (сериализация в Kafka)

HmiMsg:

```protobuf
message TagValueMsg { string tag = 1; ValueMsg value = 2; uint64 ts = 3; }
message BatchedTagValueMsg { repeated TagValueMsg tagValueBatch = 1; }
```

TnMsg.ValueMsg — `key` (опц.), `invalid`, `quality` (опц.),
`repeated uint64 chainTimeStamp` (опц.), далее `oneof value`: `boolVar`(5),
`intVar`(6), `longVar`(7), `floatVar`(8), `doubleVar`(9), `stringVar`(10),
`bytesVar`(11), `dynBoolVar`(12)…`dynBytesVar`(18), `timeVar`(19), `dynTimeVar`(20).

Dynamic / Time типы: `Dyn*Var { repeated <T> values = 1; }`,
`TimeVar { int64 millis = 1; }`, `DynTimeVar { repeated TimeVar values = 1; }`.

## Конвертация (ProtoConverter)

| Метод | Направление | Примечание |
|---|---|---|
| `toJson(MessageOrBuilder)` | Protobuf → JSON | `JsonFormat.printer()`; ошибка → `ValueConversionException` |
| `toMsg(String, Message.Builder)` | JSON → Protobuf | `JsonFormat.parser().merge()`; ошибка → `ValueConversionException` |
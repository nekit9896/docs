---
id: KB-CALC-SIDEFX-001
title: Алармы, записи тегов, ошибки (side effects)
service: hydro-calculation
group: side-effects
source: confluence/repo_description_hydro-calculation#«Side Effects», #«Обработка ошибок», #7.Error Handling, #10.BaseAlgorithm
requires: [KB-CALC-ALGO-001, KB-CALC-API-001]
related: [KB-CALC-MODELLING-001]
status: verified
---

# Алармы (через `evo.makeAlarm()`)

Виды генерируемых алармов:

- алармы отклонения давления;
- алармы выхода за пределы диапазона;
- алармы потери связи;
- алармы изменения несущей пользователем;
- алармы самотёка.

Формирование сообщения (`getParseableAlarmMessageForLu`):

```
.МП.ТУ.ЛУ.ЛУ..Текст.n
```

`setAlarm(tagName, text, text0, value, alertClassName, sequencedId, occuredAt)`
— параметры аларма в BaseAlgorithm.

# Запись в теги (алгоритмы пишут)

- значения датчиков (давление, расход, напор);
- флаги состояния (стационарность, контроль, связь);
- алармы;
- распределение плотности;
- самотёчные участки.

Запись — через `setValueAndInvalid(tag, value, invalid)` (значение + флаг
невалидности + кэш) либо `tagSet` Evo API.

# Обработка ошибок

| Исключение | Назначение |
|---|---|
| `CalculationException` | базовое исключение ошибки расчёта (конструкторы: базовый, с сообщением, с причиной) |
| `CalculationNotReadyException` | состояние «не готов к расчёту» (те же конструкторы) |
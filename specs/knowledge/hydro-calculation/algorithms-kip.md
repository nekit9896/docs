---
id: KB-CALC-ALGO-KIP-001
title: Алгоритмы Kip* (датчики давления)
service: hydro-calculation
group: algorithms
source: confluence/repo_description_hydro-calculation#10.Algorithm Layer (Kip*)
requires: [KB-CALC-ALGO-001, KB-CALC-TAGS-KIP-001]
related: [KB-CALC-STATE-001, KB-CALC-SIDEFX-001]
status: verified
---

# Алгоритмы Kip*

Все перечисленные алгоритмы в источнике описаны как «назначение + метод `calc()`»
(детальная логика в описании репозитория отсутствует — это факт источника).

| Алгоритм | Назначение | Теги (см. KB-CALC-TAGS-KIP-001) |
|---|---|---|
| KipAlarmsAlg | Генерация алармов для датчиков давления | KIP_ALMDEV* |
| KipAlmDevRangeMaxMinAlg | Контроль выхода давления за пределы диапазона | KIP_ALMDEVMAXRANGE*, KIP_ALMDEVMINRANGE* |
| KipHeadAlg | Расчёт напора для датчиков давления | KIP_HEAD (формула — KB-CALC-FORMULA-001) |
| KipHeadDeltaPressAlg | Расчёт разницы напора | KIP_HEADDELTA*, KIP_PRESSDELTA* |
| KipHeightAlg | Расчёт высоты для датчиков давления | KIP_HEIGHT |
| KipPressRangeAlg | Контроль давления в диапазоне | KIP_PRESSRANGE* |
| KipPressRateAlg | Контроль скорости изменения давления | KIP_PRESSRATE* |
| KipStationAlg | Контроль стационарности датчиков давления | KIP_STATION (см. KB-CALC-STATE-001) |
| KipVisibleAlg | Контроль видимости датчиков давления | KIP_VISIBLE |
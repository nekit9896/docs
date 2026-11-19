---
id: KB-HM-PLAYER-001
title: Плеер истории и Моделирования: Timeline, tick, предподгрузка
service: hydro-history-and-model
group: player
source: confluence/repo_description_hydro-history-and-model#3.1 (ensureRunning), «Параметры» (player.*)
requires: [KB-HM-SESSIONS-001]
related: [KB-HM-STORAGE-001, KB-HM-CONFIG-001]
status: verified
---

# Плеер истории и Моделирования

Реализация — `service/player/` (выгрузка из ClickHouse, timeline). Плеер
обслуживает все типы воспроизведения: историю, сохранённые сессии,
импортированные потоки и моделирование (KB-HM-OVERVIEW-001).

## Механика

- **Timeline** — ячейки данных, которые пошагово перекладываются в Kafka
  с заданной скоростью «времени» (`tick()`).
- Данные выгружаются из ClickHouse лениво: если нужные ячейки не готовы —
  воспроизведение приостанавливается, данные выгружаются, затем продолжение.
- **Предподгрузка**: если скоро закончатся готовые ячейки — выгрузка данных
  на будущие ячейки.
- На каждой подгрузке производится очистка данных из ячеек, которые уже
  оказались в прошлом.
- Стартовый срез данных на начало времени сессии вычитывается один раз при
  старте и отправляется в сессионные топики Kafka (KB-HM-SESSIONS-001).

## Параметры (KB-HM-CONFIG-001)

| Параметр | Default | Назначение |
|---|---|---|
| `tn-scada.history-model.player-batch-limit` | `100000` | Число записей за одну вычитку из ClickHouse |
| `tn-scada.history-model.player-preload-ticks` | `300` | Число секунд воспроизведения для предвыгрузки из ClickHouse |
| `tn-scada.history-model.fetch-optimized-enabled` | `true` | Оптимизированные выборки из ClickHouse (нужна подготовка окружения для snapshot-запросов) |
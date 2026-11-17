# ИСХОДНИКИ CONFLUENCE

Эта папка содержит файлы-исходники, отражающие состояние документации в
корпоративном Confluence. Формат — `.md`, пригодный для перетаскивания
(вставки) обратно в Confluence.

## Правило синхронизации

1. **Источник истины — рабочие документы** в `../test-plans/`, `../services/`,
   `../architecture/`, `../roadmap/` (разложены для удобного использования).
2. При изменении рабочего документа **обязательно актуализировать** файл-исходник
   в этой папке (маппинг — в `../meta/docs-map.yaml`, поле `confluence_source`).
3. Содержимое файлов этой папки перетаскивается в Confluence для публикации.
4. При выгрузке новых версий из Confluence — заменять файлы здесь и повторять
   раскладку по рабочим документам.

## Маппинг

| Файл-исходник (здесь) | Страница Confluence | Рабочий документ |
|---|---|---|
| `C4.md` | C4 | `../architecture/c4-container-level.md` |
| `roadmap_coverage.md` | roadmap_coverage | `../roadmap/roadmap-coverage.md` |
| `test-plan-hydro-calculation.md` | test-plan hydro-calculation | `../test-plans/hydro-calculation.md` |
| `test-plan-hydro-history-and-model.md` | test-plan hydro-history-and-model | `../test-plans/hydro-history-and-model.md` |
| `test-plan-of-system-tests.md` | test-plan of system tests | `../test-plans/system-tests.md` |
| `hmi-backend-descr.md` | hmi-backend descr | `../services/hmi-backend.md` |

Актуальная таблица маппинга — всегда в `../meta/docs-map.yaml`.

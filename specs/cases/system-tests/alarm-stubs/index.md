# Группа alarm-stubs — Алармные системные сценарии из HY-CALC (§3.1)

Сервис: system-tests. Источник: `confluence/test-plan-of-system-tests.md` §3.1.
Стенд: KB-SYS-TESTSTAND-001; обозначения и правила: KB-SYS-TESTPLAN-001.

> **Все 26 кейсов — заглушки источника** (`status: placeholder`). Будут дополнены после
> получения документации alarm-service / alarm-view-service (допущения 1–4, G28).
> Генерация алармов описана в кейсах HY-CALC; здесь проверяется полный системный путь:
> hydro-calc → Kafka `model_alarm_{id}` → alarm-service (REST) → hmi-backend WS →
> `hmi.wait_alarm`. Пример структуры дополнения — в HY-SYS-001.

| Кейс | Название | Базовый кейс | SYS | Статус |
|---|---|---|---|---|
| [HY-SYS-001](HY-SYS-001.md) | Аларм давления: верхняя граница | HY-CALC-014 | SYS-2 | placeholder |
| [HY-SYS-002](HY-SYS-002.md) | Аларм давления: нижняя граница | HY-CALC-015 | SYS-2 | placeholder |
| [HY-SYS-003](HY-SYS-003.md) | Аларм давления: ровно на границе | HY-CALC-016 | SYS-2 | placeholder |
| [HY-SYS-004](HY-SYS-004.md) | Аларм давления: invalid=true | HY-CALC-017 | SYS-2 | placeholder |
| [HY-SYS-005](HY-SYS-005.md) | Аларм давления: CSPA | HY-CALC-018 | SYS-2 | placeholder |
| [HY-SYS-006](HY-SYS-006.md) | Аларм расхода: AlmPressDev | HY-CALC-032 | SYS-2 | placeholder |
| [HY-SYS-007](HY-SYS-007.md) | Аларм скорости | HY-CALC-033 | SYS-2 | placeholder |
| [HY-SYS-008](HY-SYS-008.md) | Аларм расхода | HY-CALC-034 | SYS-2 | placeholder |
| [HY-SYS-009](HY-SYS-009.md) | CounterKIP | HY-CALC-035 | SYS-2 | placeholder |
| [HY-SYS-010](HY-SYS-010.md) | Индикаторы | HY-CALC-036 | SYS-2 | placeholder |
| [HY-SYS-011](HY-SYS-011.md) | Индикаторы (продолжение) | HY-CALC-037 | SYS-2 | placeholder |
| [HY-SYS-012](HY-SYS-012.md) | Самотёк: Gravity | HY-CALC-038 | SYS-2 | placeholder |
| [HY-SYS-013](HY-SYS-013.md) | GravityPossible | HY-CALC-039 | SYS-2 | placeholder |
| [HY-SYS-014](HY-SYS-014.md) | AlmFailOn | HY-CALC-040 | SYS-2 | placeholder |
| [HY-SYS-015](HY-SYS-015.md) | Достоверность | HY-CALC-041 | SYS-2 | placeholder |
| [HY-SYS-016](HY-SYS-016.md) | Аларм: строгие неравенства (верх) | HY-CALC-073 | SYS-2 | placeholder |
| [HY-SYS-017](HY-SYS-017.md) | Аларм: строгие неравенства (низ) | HY-CALC-074 | SYS-2 | placeholder |
| [HY-SYS-018](HY-SYS-018.md) | Аларм: invalid + граница | HY-CALC-075 | SYS-2 | placeholder |
| [HY-SYS-019](HY-SYS-019.md) | Аларм: CSPA (продолжение) | HY-CALC-076 | SYS-2 | placeholder |
| [HY-SYS-020](HY-SYS-020.md) | Аларм: многократное срабатывание | HY-CALC-077 | SYS-2 | placeholder |
| [HY-SYS-021](HY-SYS-021.md) | Аларм: снятие и повтор | HY-CALC-078 | SYS-2 | placeholder |
| [HY-SYS-022](HY-SYS-022.md) | Аларм: переход через границу | HY-CALC-079 | SYS-2 | placeholder |
| [HY-SYS-023](HY-SYS-023.md) | Аларм: невалидные форматы | HY-CALC-080 | SYS-2 | placeholder |
| [HY-SYS-024](HY-SYS-024.md) | Каскад: Activity→Visible→KIP | HY-CALC-083 | SYS-2 | placeholder |
| [HY-SYS-025](HY-SYS-025.md) | Каскад: все KIP отключены | HY-CALC-084 | SYS-2 | placeholder |
| [HY-SYS-026](HY-SYS-026.md) | Каскад: SGLU_CONTROLON | HY-CALC-085 | SYS-2 | placeholder |

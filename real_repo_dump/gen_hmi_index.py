#!/usr/bin/env python3
"""Генератор скелета карты дампа hmi-backend (D45/D47, 2026-11-25).

Читает дамп `hmi-backend` (формат dump_repo.py: секции `ФАЙЛ N/151: <путь>`,
разделённые строками `####...`) и выдаёт markdown-скелет `hmi-backend-INDEX.md`:
таблицу «N/151 | путь | строки дампа | подсказка | описание».

Колонка «описание» заполняется ВРУЧНУЮ; «подсказка» — первая осмысленная строка
секции (javadoc/объявление класса) и пересоздаётся скриптом при регенерации.

Использование (из этой папки):
    python gen_hmi_index.py            # печатает скелет в stdout
    python gen_hmi_index.py > hmi-backend-INDEX.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DUMP = Path(__file__).with_name("hmi-backend")
HEADER_RE = re.compile(r"^ФАЙЛ (\d+)/(\d+): (.+)$")
SEP = "#" * 60


def parse_sections(lines: list[str]) -> list[tuple[int, int, int, str]]:
    """Секции дампа: (номер, всего, строка-заголовок, путь). Строки 1-based."""
    sections = []
    for idx, line in enumerate(lines, start=1):
        match = HEADER_RE.match(line.strip())
        if match:
            number, total, path = int(match.group(1)), int(match.group(2)), match.group(3)
            sections.append((number, total, idx, path.replace("\\", "/")))
    return sections


def hint_of(lines: list[str], start: int, end: int) -> str:
    """Первая осмысленная строка секции: javadoc или объявление типа."""
    body = lines[start:end]
    javadoc: list[str] = []
    for line in body:
        stripped = line.strip()
        if not stripped or stripped == SEP or stripped.startswith(("package ", "import ")):
            if javadoc:
                break
            continue
        if stripped.startswith(("*", "/**", "*/", "//")):
            javadoc.append(stripped.lstrip("/* ").rstrip("*/ ").strip())
            if len(javadoc) >= 2:
                break
            continue
        if javadoc:
            return " ".join(javadoc)[:110]
        return stripped[:110]
    return " ".join(javadoc)[:110]


def main() -> int:
    lines = DUMP.read_text(encoding="utf-8", errors="replace").splitlines()
    sections = parse_sections(lines)
    if not sections:
        print("Секции ФАЙЛ N/M не найдены — проверь формат дампа", file=sys.stderr)
        return 1

    bounds = []
    for pos, (number, total, head, path) in enumerate(sections):
        next_head = sections[pos + 1][2] - 1 if pos + 1 < len(sections) else len(lines)
        bounds.append((number, total, head, path, next_head))

    total_files = bounds[0][1]
    print(f"<!-- Скелет сгенерирован gen_hmi_index.py из {DUMP.name}; описания — вручную. -->")
    print(f"<!-- Файлов в дампе: {len(bounds)} из {total_files} -->")
    print()
    print("| № | Файл репозитория | Строки дампа | Подсказка (авто) | Описание (вручную) |")
    print("|---|---|---|---|---|")
    for number, _total, head, path, tail in bounds:
        hint = hint_of(lines, head + 1, tail).replace("|", "\\|")
        print(f"| {number}/{total_files} | `{path}` | L{head}-L{tail} | {hint} |  |")
    return 0


if __name__ == "__main__":
    sys.exit(main())

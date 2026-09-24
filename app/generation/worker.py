"""Generation worker helpers."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app.generation import GenerationError, Generator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AvtoDoc generation worker")
    parser.add_argument("registry", type=Path)
    parser.add_argument("group")
    parser.add_argument("app_root", type=Path)
    return parser


def run_generation(
    registry: Path,
    group: str,
    app_root: Path,
    progress,
):
    """Run one generation job and forward progress messages."""
    return Generator().generate(
        registry,
        group,
        app_root,
        progress=progress,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    def report(message: str) -> None:
        print(message, flush=True)

    try:
        stats = run_generation(
            args.registry,
            args.group,
            args.app_root,
            progress=report,
        )
    except GenerationError as exc:
        print(f"ОШИБКА: {exc}", flush=True)
        return 2
    except Exception as exc:
        print(f"Критическая ошибка: {exc}", flush=True)
        return 1

    print(
        f"Статистика: студентов={stats.students}; "
        f"шаблонов={stats.templates}; "
        f"создано={stats.generated}; ошибок={stats.errors}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

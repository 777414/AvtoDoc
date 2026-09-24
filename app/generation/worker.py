"""Console worker for running one AvtoDoc generation job."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.generation import GenerationError, Generator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AvtoDoc generation worker")
    parser.add_argument("registry", type=Path)
    parser.add_argument("group")
    parser.add_argument("app_root", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()

    def report(message: str) -> None:
        print(message, flush=True)

    try:
        stats = Generator().generate(
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
    input("Нажмите Enter для завершения...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

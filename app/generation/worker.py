"""Console worker for running one AvtoDoc generation job."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from app.generation import GenerationError, Generator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AvtoDoc generation worker")
    parser.add_argument("registry", type=Path)
    parser.add_argument("group")
    parser.add_argument("app_root", type=Path)
    return parser


def configure_windows_console_io() -> None:
    """Reconnect Python standard streams to the newly created Windows console."""
    if sys.platform != "win32":
        return

    if not getattr(sys, "frozen", False):
        return

    sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
    sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")


def wait_for_completion() -> None:
    """Keep the worker console open in both script and frozen EXE modes."""
    if sys.platform == "win32":
        os.system("pause")
        return

    input("Нажмите Enter для завершения...")


def main(argv: list[str] | None = None) -> int:
    configure_windows_console_io()
    args = build_parser().parse_args(argv)

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
    wait_for_completion()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

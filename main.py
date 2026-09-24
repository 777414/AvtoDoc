"""AvtoDoc application entry point."""

import sys

from app.generation.worker import main as worker_main
from app.gui import run


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        raise SystemExit(worker_main(sys.argv[2:]))

    run()


if __name__ == "__main__":
    main()

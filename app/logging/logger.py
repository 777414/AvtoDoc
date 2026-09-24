"""Generation run logging."""

from datetime import datetime
from pathlib import Path


class GenerationLogger:
    """Write a dedicated UTF-8 log for one generation run."""

    def __init__(self, logs_dir: Path) -> None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = logs_dir / f"Генерация_{stamp}.log"

        # Avoid replacing an existing log if two runs start in the same second.
        counter = 1
        while path.exists():
            path = logs_dir / f"Генерация_{stamp}_{counter}.log"
            counter += 1

        self.path = path
        self._handle = path.open("w", encoding="utf-8")

    def write(self, message: str) -> None:
        self._handle.write(message.rstrip() + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> "GenerationLogger":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

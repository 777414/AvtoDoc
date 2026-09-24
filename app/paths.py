"""Application path handling."""

from pathlib import Path
import sys


TEMPLATES_DIRNAME = "Шаблоны"
LOGS_DIRNAME = "Логи"
RESULTS_DIRNAME = "Результат"


def get_app_root() -> Path:
    """Return the directory where the application is physically located.

    For a packaged executable this is the directory containing the executable.
    When running from source, it is the project root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_templates_dir(app_root: Path | None = None) -> Path:
    return (app_root or get_app_root()) / TEMPLATES_DIRNAME


def get_logs_dir(app_root: Path | None = None) -> Path:
    return (app_root or get_app_root()) / LOGS_DIRNAME


def get_results_dir(app_root: Path | None = None) -> Path:
    return (app_root or get_app_root()) / RESULTS_DIRNAME


def ensure_runtime_directories(app_root: Path | None = None) -> tuple[Path, Path, Path]:
    """Create the runtime directories required by AvtoDoc."""
    templates = get_templates_dir(app_root)
    logs = get_logs_dir(app_root)
    results = get_results_dir(app_root)

    templates.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    return templates, logs, results

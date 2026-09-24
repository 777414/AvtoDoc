"""Core document generation workflow."""

from dataclasses import dataclass, field
from pathlib import Path
import shutil

from app.documents import DocumentHandler, DocxHandler, DocumentProcessingError
from app.excel import read_registry
from app.paths import ensure_runtime_directories


@dataclass
class GenerationStats:
    """Statistics collected during one generation run."""

    students: int = 0
    templates: int = 0
    generated: int = 0
    errors: int = 0
    skipped_templates: list[str] = field(default_factory=list)


class GenerationError(Exception):
    """Raised when the generation run cannot be started."""


class Generator:
    """Generate documents for every student and supported template."""

    def __init__(self, handlers: list[DocumentHandler] | None = None) -> None:
        self._handlers = handlers or [DocxHandler()]

    def generate(
        self,
        registry_path: str | Path,
        group: str,
        app_root: Path | None = None,
    ) -> GenerationStats:
        """Generate all supported template documents for the registry."""
        if not group:
            raise GenerationError("Группа не указана.")

        _headers, students = read_registry(registry_path)
        stats = GenerationStats(students=len(students))
        if not students:
            return stats

        templates_dir, _logs_dir, results_dir = ensure_runtime_directories(app_root)
        supported_templates: list[tuple[Path, DocumentHandler]] = []

        for template_path in sorted(templates_dir.iterdir()):
            if not template_path.is_file():
                continue

            handler = self._handler_for(template_path)
            if handler is None:
                stats.skipped_templates.append(template_path.name)
                continue

            supported_templates.append((template_path, handler))

        stats.templates = len(supported_templates)

        group_dir = results_dir / group
        for student in students:
            student_dir = group_dir / student.get("{{ФИО}}")
            student_dir.mkdir(parents=True, exist_ok=True)

        if not supported_templates:
            return stats

        for student in students:
            fio = student.get("{{ФИО}}")
            surname = _surname(fio)

            for template_path, handler in supported_templates:
                output_name = f"{surname}_{template_path.stem}{template_path.suffix}"
                output_path = group_dir / fio / output_name

                try:
                    handler.render(template_path, output_path, student.values)
                except (DocumentProcessingError, OSError, ValueError):
                    stats.errors += 1
                    self._create_error_copy(template_path, output_path)
                else:
                    stats.generated += 1

        return stats

    def _handler_for(self, template_path: Path) -> DocumentHandler | None:
        suffix = template_path.suffix.lower()
        for handler in self._handlers:
            if suffix in handler.supported_suffixes:
                return handler
        return None

    @staticmethod
    def _create_error_copy(template_path: Path, output_path: Path) -> None:
        error_path = output_path.with_name(
            f"{output_path.stem}_ОШИБКА{output_path.suffix}"
        )
        try:
            shutil.copy2(template_path, error_path)
        except OSError:
            pass


def _surname(fio: str) -> str:
    """Return the first whitespace-separated part of the full name."""
    return fio.strip().split()[0] if fio.strip() else "БезФИО"

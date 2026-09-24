"""Core document generation workflow."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
import shutil

from app.documents import DocumentHandler, DocxHandler, DocumentProcessingError
from app.excel import ExcelReadError, read_registry
from app.logging import GenerationLogger
from app.paths import get_logs_dir, ensure_runtime_directories


ProgressCallback = Callable[[str], None]


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
    """Generate all supported template documents."""

    def __init__(self, handlers: list[DocumentHandler] | None = None) -> None:
        self._handlers = handlers or [DocxHandler()]

    def generate(
        self,
        registry_path: str | Path,
        group: str,
        app_root: Path | None = None,
        progress: ProgressCallback | None = None,
    ) -> GenerationStats:
        """Generate all supported template documents and write a run log."""
        if not group:
            raise GenerationError("Группа не указана.")

        def report(message: str) -> None:
            if progress is not None:
                progress(message)

        logs_dir = get_logs_dir(app_root)
        logs_dir.mkdir(parents=True, exist_ok=True)

        with GenerationLogger(logs_dir) as logger:
            report("=== AvtoDoc: начало генерации ===")
            logger.write("=== AvtoDoc: начало генерации ===")
            logger.write(f"Excel: {Path(registry_path)}")
            logger.write(f"Группа: {group}")

            try:
                _headers, students = read_registry(registry_path)
            except ExcelReadError as exc:
                report(f"ОШИБКА Excel: {exc}")
                logger.write(f"ОШИБКА Excel: {exc}")
                logger.write("=== Генерация завершена с ошибкой ===")
                raise

            stats = GenerationStats(students=len(students))
            report(f"Студентов: {stats.students}")
            logger.write(f"Студентов: {stats.students}")

            if not students:
                report("Студенты отсутствуют. Результаты не создаются.")
                logger.write("Студенты отсутствуют. Результаты не создаются.")
                logger.write("Итоги: создано документов: 0; ошибок: 0.")
                logger.write("=== Генерация завершена ===")
                report("=== Генерация завершена ===")
                return stats

            templates_dir, _logs_dir, results_dir = ensure_runtime_directories(app_root)
            supported_templates: list[tuple[Path, DocumentHandler]] = []
            for template_path in sorted(templates_dir.iterdir()):
                if not template_path.is_file():
                    continue

                handler = self._handler_for(template_path)
                if handler is None:
                    stats.skipped_templates.append(template_path.name)
                    message = (
                        f"Пропуск шаблона: {template_path.name} "
                        "(формат не поддерживается)."
                    )
                    report(message)
                    logger.write(message)
                    continue

                supported_templates.append((template_path, handler))

            stats.templates = len(supported_templates)
            report(f"Поддерживаемых шаблонов: {stats.templates}")
            logger.write(f"Поддерживаемых шаблонов: {stats.templates}")

            group_dir = results_dir / group
            for student in students:
                fio = student.get("{{ФИО}}")
                student_dir = group_dir / fio
                student_dir.mkdir(parents=True, exist_ok=True)

            if not supported_templates:
                report("Поддерживаемых шаблонов нет. Документы не создаются.")
                logger.write("Поддерживаемых шаблонов нет. Документы не создаются.")
                logger.write("Итоги: создано документов: 0; ошибок: 0.")
                logger.write("=== Генерация завершена ===")
                report("=== Генерация завершена ===")
                return stats

            for student in students:
                fio = student.get("{{ФИО}}")
                surname = _surname(fio)

                for template_path, handler in supported_templates:
                    output_name = f"{surname}_{template_path.stem}{template_path.suffix}"
                    output_path = group_dir / fio / output_name

                    try:
                        handler.render(template_path, output_path, student.values)
                    except (DocumentProcessingError, OSError, ValueError) as exc:
                        stats.errors += 1
                        error_path = self._create_error_copy(template_path, output_path)
                        message = f"ОШИБКА: {fio} / {template_path.name}: {exc}"
                        report(message)
                        logger.write(message)
                        if error_path is not None:
                            logger.write(f"  Копия шаблона: {error_path.name}")
                    else:
                        stats.generated += 1
                        message = f"Создано: {fio} / {output_path.name}"
                        report(message)
                        logger.write(message)

            summary = (
                f"Итоги: студентов: {stats.students}; "
                f"шаблонов: {stats.templates}; "
                f"создано документов: {stats.generated}; "
                f"ошибок: {stats.errors}."
            )
            report(summary)
            logger.write(summary)
            logger.write("=== Генерация завершена ===")
            report("=== Генерация завершена ===")
            return stats

    def _handler_for(self, template_path: Path) -> DocumentHandler | None:
        suffix = template_path.suffix.lower()
        for handler in self._handlers:
            if suffix in handler.supported_suffixes:
                return handler
        return None

    @staticmethod
    def _create_error_copy(template_path: Path, output_path: Path) -> Path | None:
        error_path = output_path.with_name(
            f"{output_path.stem}_ОШИБКА{output_path.suffix}"
        )
        if error_path.exists():
            return error_path

        try:
            shutil.copy2(template_path, error_path)
        except OSError:
            return None

        return error_path


def _surname(fio: str) -> str:
    """Return the first whitespace-separated part of the full name."""
    return fio.strip().split()[0] if fio.strip() else "БезФИО"

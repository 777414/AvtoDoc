"""Excel registry support."""

from .models import StudentRecord
from .reader import ExcelReadError, read_registry

__all__ = ["ExcelReadError", "StudentRecord", "read_registry"]

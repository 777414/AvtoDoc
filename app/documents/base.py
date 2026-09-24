"""Interfaces for document template handlers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Mapping


class DocumentProcessingError(Exception):
    """Raised when a template cannot be processed."""


class DocumentHandler(ABC):
    """Base interface for format-specific document handlers."""

    supported_suffixes: frozenset[str] = frozenset()

    @abstractmethod
    def render(
        self,
        template_path: Path,
        output_path: Path,
        values: Mapping[str, str],
    ) -> None:
        """Render a template into an output document."""
        raise NotImplementedError

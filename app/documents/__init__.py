"""Document template handlers."""

from .base import DocumentHandler, DocumentProcessingError
from .docx import DocxHandler

__all__ = ["DocumentHandler", "DocumentProcessingError", "DocxHandler"]

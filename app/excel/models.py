"""Data models used by the Excel reader."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StudentRecord:
    """One non-empty Excel row represented as text values keyed by headers."""

    values: dict[str, str]

    def get(self, marker: str, default: str = "") -> str:
        return self.values.get(marker, default)

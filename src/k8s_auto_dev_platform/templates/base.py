"""Base classes for project templates."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping


class BaseTemplate(ABC):
    """Abstract base class for code generation templates."""

    name: str = "base-template"
    description: str = "Abstract base template"
    version: str = "0.0.0"

    def validate_requirements(self, requirements: Mapping[str, Any]) -> Mapping[str, Any]:
        """Validate and normalize the provided requirements mapping."""
        return requirements

    @abstractmethod
    def generate_project(self, requirements: Mapping[str, Any], destination: Path) -> Path:
        """Generate a project at *destination* from *requirements*."""

    def _ensure_fields(self, requirements: Mapping[str, Any], fields: list[str]) -> None:
        missing = [field for field in fields if field not in requirements]
        if missing:
            readable = ", ".join(missing)
            raise ValueError(f"Missing required fields for template '{self.name}': {readable}")

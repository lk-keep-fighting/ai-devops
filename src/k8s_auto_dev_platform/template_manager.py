"""Template discovery and retrieval utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Type

from .templates import BaseTemplate, TEMPLATE_REGISTRY


@dataclass(frozen=True)
class TemplateInfo:
    """Data class describing an available template."""

    name: str
    description: str
    version: str | None = None


class TemplateManager:
    """Manage registration and instantiation of project templates."""

    def __init__(self, registry: Dict[str, Type[BaseTemplate]] | None = None) -> None:
        self._registry: Dict[str, Type[BaseTemplate]] = registry or dict(TEMPLATE_REGISTRY)

    def list_templates(self) -> Iterable[TemplateInfo]:
        for name, template_cls in self._registry.items():
            template = template_cls()
            yield TemplateInfo(
                name=template.name,
                description=template.description,
                version=getattr(template, "version", None),
            )

    def get_template(self, name: str) -> BaseTemplate:
        try:
            template_cls = self._registry[name]
        except KeyError as exc:  # pragma: no cover - defensive, covered via tests
            raise KeyError(f"Unknown template '{name}'. Available: {sorted(self._registry)}") from exc
        return template_cls()

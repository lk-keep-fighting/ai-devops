"""Available templates for the auto dev platform."""
from __future__ import annotations

from typing import Dict, Type

from .base import BaseTemplate
from .simple_service import SimplePythonServiceTemplate

TEMPLATE_REGISTRY: Dict[str, Type[BaseTemplate]] = {
    SimplePythonServiceTemplate.name: SimplePythonServiceTemplate,
}

__all__ = ["BaseTemplate", "TEMPLATE_REGISTRY", "SimplePythonServiceTemplate"]

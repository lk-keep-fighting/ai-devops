"""Utility helpers for the auto development platform."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_SLUGIFY_PATTERN = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Create a filesystem-friendly slug from the provided value."""
    normalized = value.strip().lower()
    normalized = _SLUGIFY_PATTERN.sub("-", normalized)
    normalized = normalized.strip("-")
    return normalized or "project"


def write_text(path: Path, content: str) -> None:
    """Write *content* to *path*, creating parent directories when needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    """Write *payload* as formatted JSON to *path*."""
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

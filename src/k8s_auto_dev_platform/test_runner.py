"""Test execution helpers for generated projects."""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class TestResult:
    """Result of executing a project's automated tests."""

    passed: bool
    command: Sequence[str]
    output: str
    return_code: int


class TestRunner:
    """Run the default unit test command for generated projects."""

    def __init__(self, python_executable: str | None = None) -> None:
        self._python = python_executable or sys.executable

    def run(self, project_path: Path) -> TestResult:
        command = [self._python, "-m", "unittest", "discover"]
        completed = subprocess.run(
            command,
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        return TestResult(
            passed=completed.returncode == 0,
            command=command,
            output=output,
            return_code=completed.returncode,
        )

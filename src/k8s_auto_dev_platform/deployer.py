"""Kubernetes deployment helpers."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DeploymentResult:
    """Outcome of applying Kubernetes manifests for a project."""

    applied: bool
    manifest_files: list[str]
    message: str
    command_sequence: list[Sequence[str]]


class KubernetesDeployer:
    """Apply Kubernetes manifests using the local kubectl binary when available."""

    def __init__(self, kubectl_path: str | None = None) -> None:
        self._kubectl = kubectl_path or shutil.which("kubectl")

    def deploy(self, project_path: Path, namespace: str | None = None) -> DeploymentResult:
        manifest_dir = project_path / "k8s"
        manifest_files = sorted(manifest_dir.glob("*.yaml"))
        manifest_paths = [str(path) for path in manifest_files]

        if not manifest_files:
            return DeploymentResult(
                applied=False,
                manifest_files=manifest_paths,
                message="No Kubernetes manifests found.",
                command_sequence=[],
            )

        if not self._kubectl:
            plan_path = manifest_dir / "deployment-plan.txt"
            summary_lines = [
                "kubectl command not found; generated dry-run deployment plan.",
                "Apply the following manifests manually:",
            ] + manifest_paths
            plan_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
            return DeploymentResult(
                applied=False,
                manifest_files=manifest_paths,
                message=f"kubectl not available. Plan written to {plan_path}.",
                command_sequence=[],
            )

        executed_commands: list[Sequence[str]] = []
        for manifest in manifest_files:
            command: list[str] = [self._kubectl, "apply", "-f", str(manifest)]
            if namespace:
                command.extend(["-n", namespace])
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            executed_commands.append(command)
            if completed.returncode != 0:
                message = (completed.stderr or completed.stdout or "Unknown kubectl error").strip()
                return DeploymentResult(
                    applied=False,
                    manifest_files=manifest_paths,
                    message=f"kubectl failed for {manifest}: {message}",
                    command_sequence=executed_commands,
                )

        return DeploymentResult(
            applied=True,
            manifest_files=manifest_paths,
            message="Applied Kubernetes manifests successfully.",
            command_sequence=executed_commands,
        )

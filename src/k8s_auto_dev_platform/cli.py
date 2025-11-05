"""Command line interface for the Kubernetes auto dev platform."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .orchestrator import K8sAutoDevPlatform
from .template_manager import TemplateManager


def _load_requirements(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Requirements file not found: {path}")

    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("PyYAML is required to read YAML requirement files.") from exc
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    else:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

    if not isinstance(data, Mapping):
        raise ValueError("Requirement specification must be a mapping/dictionary.")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate, test, and deploy projects from structured requirements.",
    )
    parser.add_argument(
        "--requirements",
        type=Path,
        help="Path to a JSON or YAML file describing the project requirements.",
    )
    parser.add_argument(
        "--template",
        help="Template identifier to use (see --list-templates).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./generated-projects"),
        help="Directory where generated projects will be placed (default: ./generated-projects).",
    )
    parser.add_argument(
        "--namespace",
        help="Optional Kubernetes namespace to deploy into.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running the generated project's tests.",
    )
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Skip the deployment step even if tests pass.",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates and exit.",
    )
    return parser


def _print_template_list(manager: TemplateManager) -> None:
    print("Available templates:")
    for info in manager.list_templates():
        version = f" (v{info.version})" if info.version else ""
        print(f"- {info.name}{version}: {info.description}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    manager = TemplateManager()

    if args.list_templates:
        _print_template_list(manager)
        return 0

    if not args.requirements or not args.template:
        parser.error("--requirements and --template are required unless --list-templates is used")

    requirements = _load_requirements(args.requirements)

    platform = K8sAutoDevPlatform(template_manager=manager)

    try:
        result = platform.run_pipeline(
            requirements,
            template_name=args.template,
            output_dir=args.output,
            run_tests=not args.skip_tests,
            deploy=not args.skip_deploy,
            namespace=args.namespace,
        )
    except Exception as exc:  # pragma: no cover - defensive top-level error handling
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Project generated at: {result.project_path}")
    if result.test_result:
        status = "PASSED" if result.test_result.passed else "FAILED"
        print(f"Tests: {status} (command: {' '.join(result.test_result.command)})")
        if not result.test_result.passed:
            print(result.test_result.output)
    else:
        print("Tests: skipped")

    if result.deployment_result:
        deployment_status = "applied" if result.deployment_result.applied else "not applied"
        print(
            f"Deployment: {deployment_status}. {result.deployment_result.message}"
        )
    else:
        print("Deployment: skipped")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

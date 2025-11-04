"""Pipeline orchestration for the Kubernetes auto dev platform."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from .deployer import DeploymentResult, KubernetesDeployer
from .template_manager import TemplateManager
from .test_runner import TestResult, TestRunner


@dataclass(frozen=True)
class PipelineResult:
    """Combined outcome of generating, testing, and deploying a project."""

    project_path: Path
    template_name: str
    requirements: Mapping[str, Any]
    test_result: Optional[TestResult]
    deployment_result: Optional[DeploymentResult]


class K8sAutoDevPlatform:
    """Coordinate code generation, automated testing, and deployment."""

    def __init__(
        self,
        template_manager: TemplateManager | None = None,
        tester: TestRunner | None = None,
        deployer: KubernetesDeployer | None = None,
    ) -> None:
        self.template_manager = template_manager or TemplateManager()
        self.test_runner = tester or TestRunner()
        self.deployer = deployer or KubernetesDeployer()

    def run_pipeline(
        self,
        requirements: Mapping[str, Any],
        template_name: str,
        output_dir: Path | str,
        *,
        run_tests: bool = True,
        deploy: bool = True,
        namespace: str | None = None,
    ) -> PipelineResult:
        """Execute the end-to-end pipeline for the provided specification."""

        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        template = self.template_manager.get_template(template_name)
        validated_requirements = template.validate_requirements(requirements)
        project_path = template.generate_project(validated_requirements, output_path)

        test_result: TestResult | None = None
        if run_tests:
            test_result = self.test_runner.run(project_path)

        should_deploy = deploy and (test_result is None or test_result.passed)
        deployment_result: DeploymentResult | None = None
        if should_deploy:
            deployment_result = self.deployer.deploy(project_path, namespace=namespace)

        return PipelineResult(
            project_path=project_path,
            template_name=template.name,
            requirements=validated_requirements,
            test_result=test_result,
            deployment_result=deployment_result,
        )

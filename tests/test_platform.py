from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from k8s_auto_dev_platform.deployer import KubernetesDeployer
from k8s_auto_dev_platform.orchestrator import K8sAutoDevPlatform
from k8s_auto_dev_platform.template_manager import TemplateManager
from k8s_auto_dev_platform.test_runner import TestRunner


class TemplateManagerTestCase(unittest.TestCase):
    def test_simple_template_is_registered(self) -> None:
        manager = TemplateManager()
        template_names = [info.name for info in manager.list_templates()]
        self.assertIn("simple-python-service", template_names)


class PipelineTestCase(unittest.TestCase):
    def test_full_pipeline_generates_and_tests_project(self) -> None:
        requirements = {
            "service_name": "Inventory",
            "description": "Inventory management microservice.",
            "version": "0.2.0",
            "routes": [
                {
                    "name": "list_items",
                    "method": "GET",
                    "path": "/items",
                    "status": 200,
                    "response": {
                        "items": [
                            {"sku": "SKU-001", "quantity": 5},
                            {"sku": "SKU-002", "quantity": 7},
                        ]
                    },
                },
                {
                    "name": "health",
                    "method": "GET",
                    "path": "/healthz",
                    "status": 200,
                    "response": {"status": "ok"},
                },
            ],
        }

        manager = TemplateManager()
        tester = TestRunner(python_executable=sys.executable)
        deployer = KubernetesDeployer(kubectl_path=None)
        platform = K8sAutoDevPlatform(template_manager=manager, tester=tester, deployer=deployer)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            result = platform.run_pipeline(
                requirements,
                template_name="simple-python-service",
                output_dir=output_dir,
                run_tests=True,
                deploy=True,
            )

            self.assertTrue(result.project_path.exists())
            self.assertTrue((result.project_path / "app" / "server.py").exists())

            self.assertIsNotNone(result.test_result)
            assert result.test_result is not None
            self.assertTrue(result.test_result.passed, msg=result.test_result.output)

            self.assertIsNotNone(result.deployment_result)
            assert result.deployment_result is not None
            self.assertFalse(result.deployment_result.applied)
            self.assertTrue(
                (result.project_path / "k8s" / "deployment-plan.txt").exists(),
                "Expected deployment plan when kubectl is unavailable",
            )

            metadata = result.requirements
            self.assertEqual(metadata["slug"], "inventory")
            self.assertEqual(len(metadata["routes"]), 2)


if __name__ == "__main__":
    unittest.main()

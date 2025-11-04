"""Simple Python HTTP service template."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any, Mapping

from .base import BaseTemplate
from ..utils import slugify, write_json, write_text

_ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE"}


class SimplePythonServiceTemplate(BaseTemplate):
    """Generate a lightweight HTTP JSON service powered by http.server."""

    name = "simple-python-service"
    description = "Lightweight Python service using the standard library HTTP server."
    version = "1.0.0"

    def validate_requirements(self, requirements: Mapping[str, Any]) -> Mapping[str, Any]:
        requirements = dict(requirements)
        self._ensure_fields(requirements, ["service_name", "description"])

        service_name = str(requirements["service_name"])
        slug = slugify(service_name)
        version = str(requirements.get("version", "0.1.0"))
        container_image = requirements.get("container_image") or f"registry.example.com/{slug}:{version}"

        routes = list(requirements.get("routes") or [])
        normalized_routes: list[dict[str, Any]] = []
        if not routes:
            normalized_routes.append(
                {
                    "name": "root",
                    "identifier": "root",
                    "method": "GET",
                    "path": "/",
                    "status": 200,
                    "response": {"message": f"Hello from {service_name}!"},
                }
            )
        else:
            for index, route in enumerate(routes):
                if not isinstance(route, Mapping):
                    raise ValueError("Each route must be described by a mapping/dictionary.")
                name = str(route.get("name") or f"route_{index + 1}")
                identifier = slugify(name).replace("-", "_") or f"route_{index + 1}"
                method = str(route.get("method", "GET")).upper()
                if method not in _ALLOWED_METHODS:
                    allowed = ", ".join(sorted(_ALLOWED_METHODS))
                    raise ValueError(f"Unsupported HTTP method '{method}'. Allowed: {allowed}")
                path = route.get("path")
                if not path or not str(path).startswith("/"):
                    raise ValueError("Each route must define a path starting with '/'.")
                status = int(route.get("status", 200))
                response = route.get("response") or {"message": f"Response from {name}"}
                normalized_routes.append(
                    {
                        "name": name,
                        "identifier": identifier,
                        "method": method,
                        "path": str(path),
                        "status": status,
                        "response": response,
                    }
                )

        normalized = requirements
        normalized.update(
            {
                "service_name": service_name,
                "description": str(requirements["description"]),
                "version": version,
                "container_image": str(container_image),
                "slug": slug,
                "routes": normalized_routes,
                "port": int(requirements.get("port", 8000)),
            }
        )
        return normalized

    def generate_project(self, requirements: Mapping[str, Any], destination: Path) -> Path:
        if "slug" not in requirements:
            requirements = self.validate_requirements(requirements)

        slug = requirements["slug"]
        project_dir = (destination / f"{slug}-service").resolve()
        if project_dir.exists():
            raise FileExistsError(f"Target project directory already exists: {project_dir}")

        app_dir = project_dir / "app"
        tests_dir = project_dir / "tests"
        k8s_dir = project_dir / "k8s"

        app_dir.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)
        k8s_dir.mkdir(parents=True, exist_ok=True)

        self._write_app_package(app_dir, requirements)
        self._write_tests(tests_dir, requirements)
        self._write_project_readme(project_dir, requirements)
        self._write_dockerfile(project_dir)
        self._write_k8s_manifests(k8s_dir, requirements)
        write_json(project_dir / "project-metadata.json", self._export_metadata(requirements))

        return project_dir

    def _write_app_package(self, app_dir: Path, spec: Mapping[str, Any]) -> None:
        write_text(
            app_dir / "__init__.py",
            textwrap.dedent(
                f'''"""{spec['description']}"""

SERVICE_NAME = "{spec['service_name']}"
VERSION = "{spec['version']}"
'''
            ),
        )

        write_text(app_dir / "routes.py", self._render_routes_module(spec))
        write_text(app_dir / "server.py", self._render_server_module(spec))

    def _write_tests(self, tests_dir: Path, spec: Mapping[str, Any]) -> None:
        write_text(tests_dir / "__init__.py", "")
        write_text(tests_dir / "test_routes.py", self._render_tests(spec))

    def _write_project_readme(self, project_dir: Path, spec: Mapping[str, Any]) -> None:
        routes_section = "\n".join(
            f"- **{route['method']} {route['path']}** → returns {json.dumps(route['response'], ensure_ascii=False)}"
            for route in spec["routes"]
        )
        write_text(
            project_dir / "README.md",
            textwrap.dedent(
                f'''# {spec['service_name']} Service

{spec['description']}

## Endpoints

{routes_section or 'No routes defined.'}

## Local Development

```bash
python -m app.server
```

## Testing

```bash
python -m unittest discover
```

## Deployment

Docker image: `{spec['container_image']}`

Apply the manifests in `k8s/` to deploy the service onto a Kubernetes cluster.
'''
            ),
        )

    def _write_dockerfile(self, project_dir: Path) -> None:
        write_text(
            project_dir / "Dockerfile",
            textwrap.dedent(
                """FROM python:3.11-slim
WORKDIR /app
COPY app ./app
CMD ["python", "-m", "app.server"]
"""
            ),
        )

    def _write_k8s_manifests(self, k8s_dir: Path, spec: Mapping[str, Any]) -> None:
        deployment = textwrap.dedent(
            f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {spec['slug']}
  labels:
    app: {spec['slug']}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {spec['slug']}
  template:
    metadata:
      labels:
        app: {spec['slug']}
    spec:
      containers:
        - name: {spec['slug']}
          image: {spec['container_image']}
          command: ["python", "-m", "app.server"]
          ports:
            - containerPort: {spec['port']}
'''
        )
        service = textwrap.dedent(
            f'''apiVersion: v1
kind: Service
metadata:
  name: {spec['slug']}
  labels:
    app: {spec['slug']}
spec:
  selector:
    app: {spec['slug']}
  ports:
    - protocol: TCP
      port: 80
      targetPort: {spec['port']}
  type: ClusterIP
'''
        )
        write_text(k8s_dir / "deployment.yaml", deployment)
        write_text(k8s_dir / "service.yaml", service)

    def _render_routes_module(self, spec: Mapping[str, Any]) -> str:
        route_blocks = []
        for route in spec["routes"]:
            payload = {
                "name": route["name"],
                "identifier": route["identifier"],
                "method": route["method"],
                "path": route["path"],
                "status": route["status"],
                "response": route["response"],
            }
            route_blocks.append(textwrap.indent(json.dumps(payload, indent=4, ensure_ascii=False), "    "))

        routes_literal = ",\n".join(route_blocks)
        if routes_literal:
            routes_literal = f"{routes_literal}\n"
        return textwrap.dedent(
            f'''"""Route definitions for {spec['service_name']}"""
from __future__ import annotations

from typing import Dict, Tuple

ROUTES = [
{routes_literal}]


def get_route_map() -> Dict[Tuple[str, str], dict]:
    return {{(route['method'], route['path']): route for route in ROUTES}}
'''
        )

    def _render_server_module(self, spec: Mapping[str, Any]) -> str:
        return textwrap.dedent(
            f'''"""HTTP server for {spec['service_name']}"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Tuple
from urllib.parse import urlparse

from .routes import get_route_map

ROUTE_MAP = get_route_map()


class DynamicRequestHandler(BaseHTTPRequestHandler):
    """Serve JSON responses for generated routes."""

    def _handle(self, method: str) -> None:
        parsed = urlparse(self.path)
        route = ROUTE_MAP.get((method, parsed.path))
        if not route:
            self.send_error(404, "Not Found")
            return

        body = json.dumps(route.get("response", {{}}), ensure_ascii=False).encode("utf-8")
        status = int(route.get("status", 200))
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")

    def do_PUT(self) -> None:  # noqa: N802
        self._handle("PUT")

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle("DELETE")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def create_server(host: str = "0.0.0.0", port: int = {spec['port']}) -> HTTPServer:
    return HTTPServer((host, port), DynamicRequestHandler)


def serve_forever(server: HTTPServer) -> None:
    try:
        server.serve_forever()
    finally:
        server.server_close()


def run(host: str = "0.0.0.0", port: int = {spec['port']}) -> None:
    server = create_server(host=host, port=port)
    try:
        serve_forever(server)
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    run()
'''
        )

    def _render_tests(self, spec: Mapping[str, Any]) -> str:
        return textwrap.dedent(
            '''"""Automated tests for generated routes."""
from __future__ import annotations

import http.client
import json
import threading
import time
import unittest
from typing import Any

from app.routes import ROUTES
from app.server import create_server, serve_forever


class RouteTestCase(unittest.TestCase):
    server_thread: threading.Thread | None = None
    server = None
    port: int = 0

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(host="127.0.0.1", port=0)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=serve_forever, args=(cls.server,), daemon=True)
        cls.server_thread.start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.server:
            cls.server.shutdown()
        if cls.server_thread:
            cls.server_thread.join(timeout=2)

    def _request(self, method: str, path: str) -> tuple[int, dict[str, Any]]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request(method, path)
        response = connection.getresponse()
        payload = response.read().decode("utf-8")
        connection.close()
        body = json.loads(payload) if payload else {}
        return response.status, body

    def test_routes(self) -> None:
        for route in ROUTES:
            status, body = self._request(route["method"], route["path"])
            self.assertEqual(status, route.get("status", 200))
            self.assertEqual(body, route.get("response", {}))

    def test_missing_route_returns_404(self) -> None:
        status, _ = self._request("GET", "/__unknown__")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
'''
        )

    def _export_metadata(self, spec: Mapping[str, Any]) -> Mapping[str, Any]:
        return {
            "template": self.name,
            "service_name": spec["service_name"],
            "description": spec["description"],
            "version": spec["version"],
            "container_image": spec["container_image"],
            "routes": [
                {
                    "name": route["name"],
                    "method": route["method"],
                    "path": route["path"],
                    "status": route["status"],
                }
                for route in spec["routes"]
            ],
        }

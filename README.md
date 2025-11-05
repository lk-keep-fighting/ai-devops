# Kubernetes Intelligent Auto Dev Platform

This repository contains a reference implementation of an "intelligent" development platform that automates project scaffolding, testing, and Kubernetes deployment from a high-level requirement specification and a pre-defined code framework template.

The goal of the platform is to demonstrate how a single command can:

1. **Generate** a new service based on a chosen template and structured requirements.
2. **Test** the generated service automatically using the template's recommended strategy.
3. **Deploy** (or produce a ready-to-apply deployment plan) to a Kubernetes cluster.

While this implementation focuses on a lightweight Python HTTP service template, the architecture is extensible and can accommodate additional frameworks and languages by adding new templates.

## Project Structure

```
.
├── pyproject.toml
├── README.md
├── src/
│   └── k8s_auto_dev_platform/
│       ├── cli.py
│       ├── deployer.py
│       ├── orchestrator.py
│       ├── template_manager.py
│       ├── templates/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── simple_service.py
│       ├── test_runner.py
│       └── utils.py
└── tests/
    └── test_platform.py
```

## Quickstart

### 1. Install the package locally (optional)

```bash
pip install -e .
```

### 2. Prepare a requirement specification

Create a JSON file describing the service you want to generate. For example, save the following as `requirements.json`:

```json
{
  "service_name": "inventory",
  "description": "Inventory management microservice",
  "version": "0.1.0",
  "container_image": "registry.example.com/inventory:0.1.0",
  "routes": [
    {
      "name": "list_items",
      "method": "GET",
      "path": "/items",
      "status": 200,
      "response": {
        "items": [
          {"sku": "A-123", "quantity": 10},
          {"sku": "B-987", "quantity": 4}
        ]
      }
    },
    {
      "name": "health",
      "method": "GET",
      "path": "/healthz",
      "status": 200,
      "response": {"status": "ok"}
    }
  ]
}
```

### 3. Run the platform

```bash
k8s-auto-dev \
  --requirements requirements.json \
  --template simple-python-service \
  --output ./generated-projects
```

This command will:

- Create a new project under `./generated-projects/inventory-service`.
- Populate it with code, tests, Dockerfile, and Kubernetes manifests according to the template.
- Execute the generated unit tests (`python -m unittest discover`).
- Produce a Kubernetes deployment plan. If `kubectl` is available, it will apply the manifests automatically; otherwise, it stores a deployment plan in `k8s/deployment-plan.txt` inside the generated project.

### 4. Inspect the Generated Project

```
inventory-service/
├── Dockerfile
├── README.md
├── app/
│   ├── __init__.py
│   ├── routes.py
│   └── server.py
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── deployment-plan.txt  # only when kubectl is unavailable
└── tests/
    └── test_routes.py
```

## Extending the Platform

Templates live in `k8s_auto_dev_platform/templates`. To add a new framework:

1. Subclass `BaseTemplate` and implement `generate_project`.
2. Register the template by exporting it from `templates/__init__.py`.
3. Provide any template-specific metadata or validation logic required.

The orchestrator, test runner, and deployer are intentionally modular to make it straightforward to swap implementations (for example, using a different test framework or integrating with a GitOps deployment approach).

## Running the Platform Tests

```bash
python -m unittest discover
```

The included tests execute the full pipeline end-to-end inside a temporary directory, ensuring that generation, testing, and deployment-plan creation succeed without external dependencies such as Docker or Kubernetes.

## License

This project is released under the MIT License.

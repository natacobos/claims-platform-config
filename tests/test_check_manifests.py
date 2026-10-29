import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
import check_manifests  # noqa: E402

ENVIRONMENTS = ["dev", "stg", "prd"]


def deployment(image="platformacr.azurecr.io/claims-api:2.14.0", probes=True, memory_limit="512Mi"):
    container = {"name": "api", "image": image, "resources": {"limits": {"memory": memory_limit}} if memory_limit else {}}
    if probes:
        container["readinessProbe"] = {"httpGet": {"path": "/health/ready", "port": "http"}}
        container["livenessProbe"] = {"httpGet": {"path": "/health/live", "port": "http"}}
    return {"kind": "Deployment", "metadata": {"name": "claims-api"},
            "spec": {"template": {"spec": {"containers": [container]}}}}


@pytest.mark.parametrize("environment", ENVIRONMENTS)
def test_every_environment_renders_and_passes(environment):
    resources = check_manifests.render(environment)
    assert {r["kind"] for r in resources} >= {"Deployment", "Service", "ExternalSecret"}
    assert check_manifests.check(environment, resources) == []


def test_latest_tag_is_rejected():
    problems = check_manifests.check("dev", [deployment(image="platformacr.azurecr.io/claims-api:latest")])
    assert any("no fixed version" in p for p in problems)


def test_missing_tag_is_rejected():
    problems = check_manifests.check("dev", [deployment(image="platformacr.azurecr.io/claims-api")])
    assert any("no fixed version" in p for p in problems)


def test_missing_probes_are_rejected():
    problems = check_manifests.check("dev", [deployment(probes=False)])
    assert len([p for p in problems if "Probe" in p]) == 2


def test_missing_memory_limit_is_rejected():
    problems = check_manifests.check("dev", [deployment(memory_limit=None)])
    assert any("no memory limit" in p for p in problems)

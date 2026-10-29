"""Checks the rendered configuration of every environment before Flux applies it.

Runs in CI on every pull request (see .github/workflows/validate.yml). For each overlay it runs
`kustomize build`, reads the resulting resources and applies the rules below. Any problem fails the check.

Usage:
    python tools/check_manifests.py              # check every environment
    python tools/check_manifests.py prd          # check one environment
"""

import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
OVERLAYS = ROOT / "apps" / "claims-api" / "overlays"


def render(environment):
    """Return the list of resources Kustomize produces for one environment."""
    output = subprocess.run(
        ["kustomize", "build", str(OVERLAYS / environment)],
        check=True, capture_output=True, text=True,
    ).stdout
    return [doc for doc in yaml.safe_load_all(output) if doc]


def containers(resources):
    """Yield (deployment name, container) for every container of every Deployment."""
    for res in resources:
        if res["kind"] == "Deployment":
            for container in res["spec"]["template"]["spec"]["containers"]:
                yield res["metadata"]["name"], container


def check_image_tags(environment, resources):
    """Images must use a fixed version, never 'latest' or no tag."""
    problems = []
    for deployment, container in containers(resources):
        image = container.get("image", "")
        tag = image.rsplit(":", 1)[1] if ":" in image.split("/")[-1] else ""
        if tag in ("", "latest"):
            problems.append(f"{environment}: {deployment}/{container['name']} image '{image}' has no fixed version")
    return problems


def check_probes(environment, resources):
    """Every container needs a readiness and a liveness check."""
    problems = []
    for deployment, container in containers(resources):
        for probe in ("readinessProbe", "livenessProbe"):
            if probe not in container:
                problems.append(f"{environment}: {deployment}/{container['name']} has no {probe}")
    return problems


def check_memory_limits(environment, resources):
    """Every container needs a memory limit."""
    problems = []
    for deployment, container in containers(resources):
        if not container.get("resources", {}).get("limits", {}).get("memory"):
            problems.append(f"{environment}: {deployment}/{container['name']} has no memory limit")
    return problems


RULES = [check_image_tags, check_probes, check_memory_limits]


def check(environment, resources):
    problems = []
    for rule in RULES:
        problems += rule(environment, resources)
    return problems


def main(argv):
    environments = argv[1:] or sorted(p.name for p in OVERLAYS.iterdir() if p.is_dir())
    problems = []
    for environment in environments:
        problems += check(environment, render(environment))
    for problem in problems:
        print(f"FAIL {problem}")
    print(f"{len(environments)} environment(s) checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

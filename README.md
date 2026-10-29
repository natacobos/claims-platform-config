# Code Challenge — claims-api platform configuration (30 minutes)

## The situation

This repository holds the Kubernetes configuration of **claims-api**, a .NET service that members use to submit insurance claims. It runs on AKS (Azure's Kubernetes service) in three environments: **dev**, **stg** (staging) and **prd** (production).

Nobody deploys by hand. Flux, a GitOps tool, watches this repository and applies what it contains to each cluster. Kustomize builds each environment's final configuration from two parts:

- `apps/claims-api/base/`: what every environment shares (the Deployment, the Service, the secret from Azure Key Vault, the autoscaler, the mesh permission and the Kong plugin).
- `apps/claims-api/overlays/<environment>/`: the changes for that environment only. Each overlay's `kustomization.yaml` lists the patch files it applies.

Production went live last week (ticket **PLAT-212** below). The `prd` overlay was created by copying `stg` and adjusting it. The CI check is green, but these reports have arrived since go-live:

- **Staging team:** "Since Monday we see real member claims in the staging app."
- **On-call engineer:** "claims-api pods in production restart several times a day at peak hours. Kubernetes shows the reason `OOMKilled`" (the pod was stopped because it used more memory than its limit).
- **Support:** "Every time we deploy a new version to production, members get errors for about a minute."
- **Finance:** "claims-api reserves far more CPU than it uses, and the cluster had to add machines. At peak hours, it still doesn't scale up."

Your job is to find the cause of each report in this configuration, fix it, and then extend the CI check.

You may use your usual tools, including an AI assistant. Please share your screen and explain what you ask it and how you check what it gives you.

## Ticket PLAT-212 — Run claims-api in production

**Facts measured in staging and production**

- Memory per pod: about 1.4 GiB at peak in production.
- CPU per pod: about 150m on average and 250m at peak (m = thousandths of a CPU; 1000m is one full CPU).
- Production must keep at least 6 copies (pods) running, and may grow to 12 at peak.

**Acceptance criteria**

1. Each environment uses only its own database. The connection string comes from the Key Vault secret for that environment: `claims-db-connection-dev`, `claims-db-connection-stg` or `claims-db-connection-prd`.
2. Production pods have enough memory for peak load, with room to spare, so they are never stopped for using too much memory.
3. Deploying a new version causes no errors for members: old pods keep serving until new ones are ready.
4. Production reserves CPU according to real use, so it doesn't pay for idle capacity and the autoscaler can add pods at peak. (The autoscaler adds pods when average CPU use goes over 70% of what each pod reserves.)
5. Every container has a fixed image version, a readiness and a liveness check, and a memory limit. The CI check (`tools/check_manifests.py`) enforces this.

## Steps

1. **Investigate (10 minutes).** For each report, find the cause in the configuration and the acceptance criterion it breaks. Tell us what you would fix first. Do not change files yet.
2. **Fix (12 minutes).** Fix the causes you found. Show the final production configuration that proves each fix.
3. **Extend (8 minutes).** A new acceptance criterion is added to the ticket:

   > 6. The CI check fails if any environment uses a Key Vault secret meant for a different environment.

   Add this rule to `tools/check_manifests.py`, with a test. If time is short, explain how you would finish it.

## Rules

- Keep the existing structure (base plus one overlay per environment); do not rewrite it from scratch.
- Check the configuration against the ticket; do not assume it is correct because the CI check is green.
- Changes for one environment must not change the others unless the ticket requires it.
- If you use an AI assistant, review every change it proposes before accepting it, and be ready to explain it.
- Do not add new libraries.

## Running the project

**With Docker (recommended).** You only need Docker Desktop. Clone the repository and run, from its folder:

```bash
docker compose run --rm tools render prd     # show production's final configuration (also: dev, stg)
docker compose run --rm tools check          # run the CI check on every environment
docker compose run --rm tools test           # run the CI check's tests
```

The first run builds a small image (about 1 minute). Edit the files in your usual editor; the commands always use your latest changes. There is no cluster: everything is checked by building the configuration.

**Without Docker.** Install Python 3.12 and kustomize v5.4.3, then run:

```bash
pip install -r requirements.txt
kustomize build apps/claims-api/overlays/prd
python tools/check_manifests.py
python -m pytest -q
```

The repository also works in a GitHub Codespace (Code → Codespaces); then use the Docker commands above.

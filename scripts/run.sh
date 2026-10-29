#!/bin/sh
# Entry point of the tools container. The repository is mounted at /repo, so your edits are used immediately.
set -e
case "$1" in
  render) kustomize build "apps/claims-api/overlays/${2:?usage: render dev|stg|prd}" ;;
  check)  shift; python tools/check_manifests.py "$@" ;;
  test)   shift; python -m pytest -q "$@" ;;
  *)      echo "usage: render <dev|stg|prd> | check [environment] | test"; exit 2 ;;
esac

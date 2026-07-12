# Umbrel Arr Store Guide

This repository is a generated Umbrel community app store.

## Rules

- Always sign commits.
- Use meaningful branches such as `feat/initial-media-stack` or
  `fix/setup-reconcile`.
- Never commit credentials, API keys, private hostnames, or machine paths.
- Pin every container image as `tag@sha256:digest`.
- Keep service packages minimal. Cross-service behavior belongs in the
  separate `umbrel-arr/umbrelarr` repository and published image.
- Edit `.tools/generate-packages.py`; do not hand-edit generated package files.
- Keep only Privado image source under `.src/`. Do not duplicate umbrelarr
  runtime source in this store.
- Run `.tools/generate-packages.py --check`, `.tools/validate-store.sh`, and the
  setup tests before publishing.
- Never run Docker-based package tests on macOS. Container integration belongs
  on the manually triggered Linux CI workflow, whose harness refuses to run on
  other hosts.
- Preserve user-owned service configuration. The reconciler may only update
  resources it owns by stable name or tag.

## Package Layout

Each non-hidden top-level directory is an Umbrel package. Its directory and
manifest id must match and start with `umbrel-arr-`.

Privado image source lives under `.src/privado-proxy`, shared assets under
`.assets/`, and generated packages are committed so umbrelOS can consume the
repository directly.

Community app icons must use an absolute HTTPS URL in `umbrel-app.yml`; Umbrel
does not resolve relative icon paths for custom stores. Keep the vendored
256x256 SVG in each package, use a fully opaque edge-to-edge canvas, and update
icons through `.assets/icon-sources/` plus `.tools/generate-icons.py`.

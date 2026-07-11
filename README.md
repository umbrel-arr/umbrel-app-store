# Umbrel Arr App Store

Umbrel Arr is a community app store for a complete, automatically configured
Arr media stack on umbrelOS.

Add this community store to Umbrel:

```text
https://github.com/umbrel-arr/umbrel-app-store
```

Install **umbrelarr**. Umbrel installs the service dependencies, then the
management dashboard configures VPN routing, download clients, media roots, Prowlarr,
Bazarr, Profilarr, and Overseerr.

## Development

App packages are generated from `.tools/generate-packages.py`:

```sh
.tools/generate-packages.py
.tools/validate-store.sh
python3 -m unittest discover -s .src/setup/tests -v
```

Do not edit generated package files directly. Change the catalog or templates,
regenerate, and commit the source and generated output together.

Container integration runs only on a remote Linux runner through the manually
triggered `Smoke stack on Linux` GitHub Actions workflow. Do not run the package
Compose files with Docker on macOS. The Linux-only harness exits before invoking
Docker anywhere outside that workflow.

## Storage

- Downloads: `${UMBREL_ROOT}/data/storage/downloads`, mounted as `/downloads`
- Media: `${UMBREL_ROOT}/data/storage/network`, mounted as `/media`

The setup app requires writable network storage before it creates media roots.

## Security

Service UIs are protected by Umbrel. Internal API credentials are random,
persisted in each owning app's data directory, and never committed. Privado
credentials are forwarded directly to the VPN app and are not stored by the
setup app.

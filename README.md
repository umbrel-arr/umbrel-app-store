# Umbrel Arr App Store

Umbrel Arr is a community app store for an explicitly connected and managed Arr
media stack on umbrelOS.

Add this community store to Umbrel:

```text
https://github.com/umbrel-arr/umbrel-app-store
```

Install the required service apps first, then install **umbrelarr**. Its setup
screen detects those user-installed apps and waits for explicit confirmation
before the management dashboard configures VPN routing, download clients, media
roots, Prowlarr, Bazarr, Profilarr, and Overseerr.

umbrelarr does not install, start, stop, or replace those apps. Umbrel records
all 13 as prerequisites so the management app can connect only to a complete,
user-installed stack.

### Required upgrade order for umbrelarr 1.1

Before installing or upgrading to umbrelarr 1.1, update all credential-handoff
packages below. Do not start the umbrelarr upgrade while an older revision is
installed because those packages used install-time exports that wrote API keys
and configuration files.

| Package | Required version |
| --- | --- |
| Prowlarr | `2.3.5.5327-umbrel.3` |
| qBittorrent | `5.2.4-umbrel.3` |
| SABnzbd | `5.0.4-umbrel.3` |
| Sonarr | `4.0.17.2952-umbrel.3` |
| Sonarr 4K | `4.0.17.2952-umbrel.3` |
| Radarr | `6.1.1.10360-umbrel.3` |
| Radarr 4K | `6.1.1.10360-umbrel.3` |
| Bazarr | `1.6.0-umbrel.3` |
| Overseerr | `1.35.0-umbrel.3` |
| Lidarr | `3.1.0.4875-umbrel.3` |

Only after all ten updates are installed should umbrelarr be updated to 1.1.
The 1.1 package deliberately requires their new `CONFIG_DIR` exports; it does
not guess sibling data paths, invoke an old export, or allow Docker to create a
missing source directory.

## Development

App packages are generated from `.tools/generate-packages.py`:

```sh
.tools/generate-packages.py
.tools/validate-store.sh
python3 -m unittest discover -s .tools/tests -v
```

Do not edit generated package files directly. Change the catalog or templates,
regenerate, and commit the source and generated output together.

Container integration runs only on a remote Linux runner through the manually
triggered `Smoke stack on Linux` GitHub Actions workflow. Do not run the package
Compose files with Docker on macOS. The Linux-only harness exits before invoking
Docker anywhere outside that workflow.

## Storage

- Downloads: `${UMBREL_ROOT}/data/storage/downloads`, mounted as `/downloads`
- Linked storage: `${UMBREL_ROOT}/data/storage/network`, mounted as `/network`

umbrelarr defaults to Umbrel's `/downloads/movies`, `/downloads/shows`, and
`/downloads/music` layout. Its dashboard can adopt existing Arr root-folder IDs
or switch its API-managed roots between the local and network presets. The
umbrelarr container does not mount either storage tree.

## Security

Service UIs are protected by Umbrel. Each service generates and owns its API
credentials. Dependency exports only expose service URLs, read-only config
directory paths, and Umbrel-provided environment values; they never create or
modify another app's files. umbrelarr reads credentials from those config
directories and performs managed changes through service APIs after setup is
confirmed.

The umbrelarr runtime is stateless, has a read-only root filesystem, and has no
persistent data or shared-storage mount. qBittorrent uses Umbrel's deterministic
app password, which umbrelarr applies through qBittorrent's API during explicit
setup. Privado credentials are forwarded directly to the VPN app and are not
stored by the management app. The umbrelarr source and image releases live in
the separate [`umbrel-arr/umbrelarr`](https://github.com/umbrel-arr/umbrelarr)
repository.

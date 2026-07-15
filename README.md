# Umbrel Arr App Store

Umbrel Arr is a community app store for an explicitly connected and managed Arr
media stack on umbrelOS.

Add this community store to Umbrel:

```text
https://github.com/umbrel-arr/umbrel-app-store
```

Install **umbrelarr** and only the service apps you want. Its setup screen offers
starting profiles and individual module switches, detects the selected
user-installed apps, and waits for explicit confirmation before the dashboard
configures the settings it owns.

umbrelarr does not install, start, stop, or replace service apps. Its manifest
requires only Prowlarr, the small control-plane anchor where setup consent and
modular choices are stored as API-owned tags. Download, media, subtitle,
request, profile, and VPN services are never forced as dependencies.

The umbrelarr lifecycle export checks the standard Umbrel app-data locations
for optional apps and publishes only config directories that already exist.
The package uses `/dev/null` for an absent path, so Docker cannot create a
phantom app directory and the dashboard can report that the selected app is
not installed. This keeps discovery read-only while every managed change still
goes through the owning service's API. Restart umbrelarr once after installing
a new optional module so Umbrel can refresh these read-only mounts.

### Starting profiles

- Core only: Prowlarr and umbrelarr.
- TV with torrents: Prowlarr, qBittorrent, and Sonarr.
- TV and movies with Usenet: Prowlarr, SABnzbd, Sonarr, and Radarr.
- Complete media stack: every supported service module.

Profiles are shortcuts, not separate packages. Any module can be adjusted
before detection, and VPN routing is selected independently as Privado,
compatible external SOCKS5, or direct routing.

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
credentials. The manager's lifecycle export exposes only existing read-only
config directory paths and Umbrel-derived qBittorrent credentials; it never
creates or modifies another app's files. umbrelarr reads credentials from those
config directories and performs managed changes through service APIs after
setup is confirmed.

The umbrelarr runtime is stateless, has a read-only root filesystem, and has no
persistent data or shared-storage mount. qBittorrent uses Umbrel's deterministic
app password, which umbrelarr applies through qBittorrent's API during explicit
setup. A 1.1 installation may have received umbrelarr's deterministic password;
1.2.3 accepts that value only as a migration fallback and immediately rotates
qBittorrent to its own app-derived password. Privado credentials are forwarded
directly to the VPN app and are not stored by the management app. The umbrelarr
source and image releases live in the separate
[`umbrel-arr/umbrelarr`](https://github.com/umbrel-arr/umbrelarr) repository.

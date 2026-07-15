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

umbrelarr does not install, start, stop, or replace service apps, and its
manifest does not force-install the complete catalog. Prowlarr remains the
small required control-plane anchor because setup consent and modular choices
are stored as API-owned tags; every download, media, subtitle, request, profile,
and VPN service is otherwise optional.

Installed apps publish their internal URL and, where necessary, their own
read-only config-directory path through Umbrel exports. The umbrelarr package
uses `/dev/null` for an export that is absent, so Docker cannot create a phantom
app directory and the dashboard can report that the selected app is not
installed. This keeps discovery read-only while every managed change still
goes through the owning service's API.

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
credentials. Installed-app exports only expose service URLs, read-only config
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

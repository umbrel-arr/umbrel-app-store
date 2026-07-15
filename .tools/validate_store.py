#!/usr/bin/env python3

import re
import sys
from pathlib import Path


IMAGE_RE = re.compile(r"^\s*image:\s*\S+@sha256:[0-9a-f]{64}\s*$", re.MULTILINE)
KEY_RE = re.compile(r"^(id|port|icon):\s*(.+?)\s*$", re.MULTILINE)
EXPORT_MUTATION_RE = re.compile(
    r"(?:^|\s)(?:mkdir|touch|chmod|chown|install|truncate|tee|openssl)\s|"
    r"sed\s+-i|(?:^|\s)printf\s|>\s*[\"']?\$",
    re.MULTILINE,
)
EXPORT_LINE_RE = re.compile(r'^export UMBREL_ARR_[A-Z0-9_]+="[^`]*"$')
MANAGER_CONFIG_SLUGS = (
    "prowlarr",
    "sabnzbd",
    "sonarr",
    "sonarr-4k",
    "radarr",
    "radarr-4k",
    "bazarr",
    "overseerr",
    "lidarr",
)


def manager_export_lines():
    lines = ['umbrel_arr_apps_root="${EXPORTS_APP_DIR%/*}"']
    for slug in MANAGER_CONFIG_SLUGS:
        variable = slug.upper().replace("-", "_")
        path = f"${{umbrel_arr_apps_root}}/umbrel-arr-{slug}/data/config"
        lines.extend(
            [
                f'if [ -d "{path}" ]; then',
                f'  export UMBREL_ARR_{variable}_CONFIG_DIR="{path}"',
                "fi",
            ]
        )
    lines.extend(
        [
            'if [ -d "${umbrel_arr_apps_root}/umbrel-arr-qbittorrent" ]; then',
            '  export UMBREL_ARR_QBITTORRENT_PASSWORD="$(derive_entropy "app-umbrel-arr-qbittorrent-seed-APP_PASSWORD")"',
            '  export UMBREL_ARR_QBITTORRENT_LEGACY_PASSWORD="$(derive_entropy "app-umbrel-arr-umbrelarr-seed-APP_PASSWORD")"',
            "fi",
            "unset umbrel_arr_apps_root",
        ]
    )
    return lines


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def main(root):
    store = root / "umbrel-app-store.yml"
    if not store.exists() or "id: umbrel-arr" not in store.read_text():
        fail("umbrel-app-store.yml must declare id umbrel-arr")

    ports = {}
    count = 0
    for directory in sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        manifest = directory / "umbrel-app.yml"
        compose = directory / "docker-compose.yml"
        if not manifest.exists() or not compose.exists():
            fail(f"{directory.name} is missing umbrel-app.yml or docker-compose.yml")

        manifest_text = manifest.read_text()
        metadata = dict(KEY_RE.findall(manifest_text))
        if metadata.get("id") != directory.name:
            fail(f"{directory.name} manifest id does not match its directory")
        if not directory.name.startswith("umbrel-arr-"):
            fail(f"{directory.name} does not start with the store id")
        icon = metadata.get("icon", "")
        expected_icon_suffix = f"/{directory.name}/icon.svg"
        if not icon.startswith("https://") or not icon.endswith(expected_icon_suffix):
            fail(f"{directory.name} must use an absolute HTTPS icon URL ending in {expected_icon_suffix}")
        if not (directory / "icon.svg").exists():
            fail(f"{directory.name} must include icon.svg")

        try:
            port = int(metadata["port"].strip('"'))
        except (KeyError, ValueError):
            fail(f"{directory.name} has an invalid port")
        if port in ports:
            fail(f"port {port} is shared by {ports[port]} and {directory.name}")
        ports[port] = directory.name

        compose_text = compose.read_text()
        if "app_proxy:" not in compose_text or "APP_HOST:" not in compose_text or "APP_PORT:" not in compose_text:
            fail(f"{directory.name} is missing app_proxy wiring")
        if re.search(r"^\s+ports:\s*$", compose_text, re.MULTILINE):
            fail(f"{directory.name} must not publish host port bindings")
        if "/media" in compose_text:
            fail(f"{directory.name} must use /downloads or /network instead of /media")
        for line in compose_text.splitlines():
            if ":/network" in line and not line.strip().endswith(":/network:rslave"):
                fail(f"{directory.name} must mount /network with rslave propagation")
        if "${UMBREL_ROOT}/data/storage" in compose_text and "STORAGE_DOWNLOADS" not in manifest_text:
            fail(f"{directory.name} must request STORAGE_DOWNLOADS permission")
        images = [line for line in compose_text.splitlines() if line.lstrip().startswith("image:")]
        if not images or len(IMAGE_RE.findall(compose_text)) != len(images):
            fail(f"{directory.name} contains an unpinned image")
        if directory.name == "umbrel-arr-umbrelarr":
            if (directory / "app").exists():
                fail("umbrel-arr-umbrelarr must use its published image instead of embedded source")
            if "read_only: true" not in compose_text:
                fail("umbrel-arr-umbrelarr must use a read-only root filesystem")
            for forbidden in ("${APP_DATA_DIR}", "STATE_DIR", "docker.sock", ":/data"):
                if forbidden in compose_text:
                    fail(f"umbrel-arr-umbrelarr stateless runtime contains {forbidden}")
            for line in compose_text.splitlines():
                if ":/managed-config/" in line and not line.strip().endswith(":ro"):
                    fail("umbrel-arr-umbrelarr config mounts must be read-only")
        elif "${APP_DATA_DIR}" not in compose_text and directory.name != "umbrel-arr-flaresolverr":
            fail(f"{directory.name} does not persist data under APP_DATA_DIR")

        exports = directory / "exports.sh"
        if exports.exists():
            exports_text = exports.read_text()
            if EXPORT_MUTATION_RE.search(exports_text):
                fail(f"{directory.name} exports.sh must not create or modify files")
            if directory.name == "umbrel-arr-umbrelarr":
                if exports_text.splitlines() != manager_export_lines():
                    fail("umbrel-arr-umbrelarr exports.sh contains unexpected discovery logic")
            else:
                for line in exports_text.splitlines():
                    if not EXPORT_LINE_RE.fullmatch(line) or "$(" in line:
                        fail(f"{directory.name} exports.sh may only export declarative handoff values")
        count += 1

    if count != 14:
        fail(f"expected 14 app packages, found {count}")
    print(f"Validated {count} app package(s).")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())

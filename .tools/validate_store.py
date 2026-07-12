#!/usr/bin/env python3

import re
import sys
from pathlib import Path


IMAGE_RE = re.compile(r"^\s*image:\s*\S+@sha256:[0-9a-f]{64}\s*$", re.MULTILINE)
KEY_RE = re.compile(r"^(id|port|icon):\s*(.+?)\s*$", re.MULTILINE)


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
        if "${APP_DATA_DIR}" not in compose_text and directory.name not in {
            "umbrel-arr-flaresolverr",
        }:
            fail(f"{directory.name} does not persist data under APP_DATA_DIR")
        if directory.name == "umbrel-arr-umbrelarr" and (directory / "app").exists():
            fail("umbrel-arr-umbrelarr must use its published image instead of embedded source")
        count += 1

    if count != 14:
        fail(f"expected 14 app packages, found {count}")
    print(f"Validated {count} app package(s).")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())

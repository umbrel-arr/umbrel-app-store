#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from textwrap import dedent, indent


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "umbrel-arr"

APPS = {
    "privado-vpn": {
        "name": "Privado VPN",
        "category": "Networking",
        "version": "1.2.2",
        "port": 30980,
        "internal_port": 8080,
        "image": "ghcr.io/umbrel-arr/privado-proxy:1.2.2@sha256:68dd6eb5d8355105dc913f59d02dd759ec4be4ae75a625032c9fc28264921eb2",
        "tagline": "Private SOCKS5 gateway for the media stack",
        "description": "Provides the WireGuard tunnel and SOCKS5 proxy used by Umbrel Arr. Enter your Privado login once in umbrelarr; a healthy server is selected automatically.",
        "developer": "Umbrel Arr",
        "website": "https://github.com/umbrel-arr/umbrel-app-store",
        "repo": "https://github.com/umbrel-arr/umbrel-app-store",
        "support": "https://github.com/umbrel-arr/umbrel-app-store/issues",
        "kind": "privado",
    },
    "flaresolverr": {
        "name": "FlareSolverr",
        "category": "Networking",
        "version": "3.5.0-umbrel.1",
        "port": 30981,
        "internal_port": 8191,
        "image": "ghcr.io/flaresolverr/flaresolverr:latest@sha256:139dfee1c6f89249c8d665d1333a42e8ec74ec0a86bc6bb1c8461e10d3a66a47",
        "tagline": "Browser challenge solver for Prowlarr",
        "description": "Solves supported browser challenges for tagged Prowlarr indexers. umbrelarr registers the proxy and routes browser traffic through Privado.",
        "developer": "FlareSolverr",
        "website": "https://github.com/FlareSolverr/FlareSolverr",
        "repo": "https://github.com/FlareSolverr/FlareSolverr",
        "support": "https://github.com/FlareSolverr/FlareSolverr/issues",
        "kind": "flaresolverr",
    },
    "prowlarr": {
        "name": "Prowlarr",
        "category": "Media",
        "version": "2.3.5.5327-umbrel.1",
        "port": 30982,
        "internal_port": 9696,
        "image": "lscr.io/linuxserver/prowlarr:latest@sha256:3e9bd62ca90c97c5df75b7012e10a29f6926e62807deeddc1dc89e6e2fd141e1",
        "tagline": "Indexer manager for the complete Arr stack",
        "description": "Manages indexers for Sonarr, Radarr, their 4K instances, and Lidarr. umbrelarr owns service registration, VPN proxy settings, and FlareSolverr integration.",
        "developer": "Prowlarr",
        "website": "https://prowlarr.com",
        "repo": "https://github.com/Prowlarr/Prowlarr",
        "support": "https://github.com/Prowlarr/Prowlarr/issues",
        "kind": "servarr",
        "api_version": "v1",
        "root": None,
    },
    "qbittorrent": {
        "name": "qBittorrent",
        "category": "Media",
        "version": "5.2.4-umbrel.1",
        "port": 30983,
        "internal_port": 8080,
        "image": "lscr.io/linuxserver/qbittorrent:latest@sha256:d8488fb24969bb0954cf64a1ca1cf7a763031641ba4246734964faea6f0b807a",
        "tagline": "Torrent client managed by umbrelarr",
        "description": "Downloads torrents to shared Umbrel storage. umbrelarr applies Privado SOCKS5 routing and creates the HD, 4K, TV, movie, and music categories.",
        "developer": "qBittorrent",
        "website": "https://www.qbittorrent.org",
        "repo": "https://github.com/qbittorrent/qBittorrent",
        "support": "https://github.com/qbittorrent/qBittorrent/issues",
        "kind": "qbittorrent",
    },
    "sabnzbd": {
        "name": "SABnzbd",
        "category": "Media",
        "version": "5.0.4-umbrel.1",
        "port": 30984,
        "internal_port": 8080,
        "image": "lscr.io/linuxserver/sabnzbd:latest@sha256:30cc2eb9e1c8b7c5bb90dbf3c7abb0e66643c21c3710e273a82d2f36239e176d",
        "tagline": "Usenet client managed by umbrelarr",
        "description": "Downloads from your Usenet providers to shared Umbrel storage. umbrelarr applies VPN routing, paths, and media categories; you only add provider credentials.",
        "developer": "SABnzbd",
        "website": "https://sabnzbd.org",
        "repo": "https://github.com/sabnzbd/sabnzbd",
        "support": "https://github.com/sabnzbd/sabnzbd/issues",
        "kind": "sabnzbd",
    },
    "sonarr": {
        "name": "Sonarr",
        "category": "Media",
        "version": "4.0.17.2952-umbrel.1",
        "port": 30985,
        "internal_port": 8989,
        "image": "lscr.io/linuxserver/sonarr:latest@sha256:633e0e66d85ce4e9172608a37d3d24e124b3e485fc0d946f533c3bb5875227e9",
        "tagline": "HD TV series manager",
        "description": "Manages the HD series library in Umbrel or linked network storage. umbrelarr configures roots, download clients, Prowlarr, and Profilarr.",
        "developer": "Sonarr",
        "website": "https://sonarr.tv",
        "repo": "https://github.com/Sonarr/Sonarr",
        "support": "https://github.com/Sonarr/Sonarr/issues",
        "kind": "servarr",
        "api_version": "v3",
        "root": "/downloads/shows",
    },
    "sonarr-4k": {
        "name": "Sonarr 4K",
        "category": "Media",
        "version": "4.0.17.2952-umbrel.1",
        "port": 30986,
        "internal_port": 8989,
        "image": "lscr.io/linuxserver/sonarr:latest@sha256:633e0e66d85ce4e9172608a37d3d24e124b3e485fc0d946f533c3bb5875227e9",
        "tagline": "Dedicated 4K TV series manager",
        "description": "Keeps a separate 2160p series library under network storage with its own category, root, quality profiles, and request-server registration.",
        "developer": "Sonarr",
        "website": "https://sonarr.tv",
        "repo": "https://github.com/Sonarr/Sonarr",
        "support": "https://github.com/Sonarr/Sonarr/issues",
        "kind": "servarr",
        "api_version": "v3",
        "root": "/downloads/shows-4k",
    },
    "radarr": {
        "name": "Radarr",
        "category": "Media",
        "version": "6.1.1.10360-umbrel.1",
        "port": 30987,
        "internal_port": 7878,
        "image": "lscr.io/linuxserver/radarr:latest@sha256:39da107b5a9371fdaa651bd188049b863716a815385eb3a30d41071b7e1aeb33",
        "tagline": "HD movie manager",
        "description": "Manages the HD movie library in Umbrel or linked network storage. umbrelarr configures roots, download clients, Prowlarr, and Profilarr.",
        "developer": "Radarr",
        "website": "https://radarr.video",
        "repo": "https://github.com/Radarr/Radarr",
        "support": "https://github.com/Radarr/Radarr/issues",
        "kind": "servarr",
        "api_version": "v3",
        "root": "/downloads/movies",
    },
    "radarr-4k": {
        "name": "Radarr 4K",
        "category": "Media",
        "version": "6.1.1.10360-umbrel.1",
        "port": 30988,
        "internal_port": 7878,
        "image": "lscr.io/linuxserver/radarr:latest@sha256:39da107b5a9371fdaa651bd188049b863716a815385eb3a30d41071b7e1aeb33",
        "tagline": "Dedicated 4K movie manager",
        "description": "Keeps a separate 2160p movie library under network storage with its own category, root, quality profiles, and request-server registration.",
        "developer": "Radarr",
        "website": "https://radarr.video",
        "repo": "https://github.com/Radarr/Radarr",
        "support": "https://github.com/Radarr/Radarr/issues",
        "kind": "servarr",
        "api_version": "v3",
        "root": "/downloads/movies-4k",
    },
    "bazarr": {
        "name": "Bazarr",
        "category": "Media",
        "version": "1.6.0-umbrel.1",
        "port": 30989,
        "internal_port": 6767,
        "image": "lscr.io/linuxserver/bazarr:latest@sha256:5d916d07404296ec35ee726e13e0e558f05952724cf494a7f009d913fb2b12f3",
        "tagline": "Subtitle manager for HD Sonarr and Radarr",
        "description": "Manages subtitles beside the HD series and movie libraries. umbrelarr connects Sonarr and Radarr and routes provider traffic through Privado.",
        "developer": "Bazarr",
        "website": "https://www.bazarr.media",
        "repo": "https://github.com/morpheus65535/bazarr",
        "support": "https://github.com/morpheus65535/bazarr/issues",
        "kind": "bazarr",
    },
    "overseerr": {
        "name": "Overseerr",
        "category": "Media",
        "version": "1.35.0-umbrel.1",
        "port": 30990,
        "internal_port": 5055,
        "image": "sctx/overseerr:latest@sha256:6197516c9d7b58ccf113455e32aafb94df5d91995fe50e8c2cae6ba6c7c7b7de",
        "tagline": "Media requests for HD and 4K libraries",
        "description": "Provides media discovery and requests. Complete Plex sign-in once; umbrelarr then registers the HD and 4K Sonarr and Radarr servers automatically.",
        "developer": "Overseerr",
        "website": "https://overseerr.dev",
        "repo": "https://github.com/sct/overseerr",
        "support": "https://github.com/sct/overseerr/issues",
        "kind": "overseerr",
    },
    "profilarr": {
        "name": "Profilarr",
        "category": "Media",
        "version": "2.0.9-umbrel.1",
        "port": 30991,
        "internal_port": 6868,
        "image": "ghcr.io/dictionarry-hub/profilarr:2.0.9@sha256:7a9b5112ff227320d17c65ab643a5d875713e6235991ef04a8e482ec51427902",
        "parser_image": "ghcr.io/dictionarry-hub/profilarr-parser:2.0.9@sha256:16b22ef6485e135cc660cd511697c637d44649753d02397c9374e1317cfaaf0e",
        "tagline": "Quality profiles and custom formats as code",
        "description": "Owns quality profiles and custom formats for the HD and 4K Sonarr and Radarr instances. umbrelarr links the public database and configures daily synchronization.",
        "developer": "Profilarr",
        "website": "https://github.com/Dictionarry-Hub/profilarr",
        "repo": "https://github.com/Dictionarry-Hub/profilarr",
        "support": "https://github.com/Dictionarry-Hub/profilarr/issues",
        "kind": "profilarr",
    },
    "umbrelarr": {
        "name": "umbrelarr",
        "category": "Media",
        "version": "1.0.0",
        "port": 30992,
        "internal_port": 8080,
        "image": "ghcr.io/umbrel-arr/umbrelarr:1.0.0@sha256:c1f012c615e1b65e6f264c27496134f8a5ca28d764a54d6b0dc12d9776321c68",
        "tagline": "Manage and automatically configure the complete stack",
        "description": "umbrelarr is the management surface for Umbrel Arr. It installs the service dependencies, accepts the one-time Privado login, configures all owned integrations, reports required actions, and repairs managed drift without touching user-owned settings.",
        "developer": "Umbrel Arr",
        "website": "https://github.com/umbrel-arr/umbrelarr",
        "repo": "https://github.com/umbrel-arr/umbrelarr",
        "support": "https://github.com/umbrel-arr/umbrelarr/issues",
        "kind": "setup",
    },
    "lidarr": {
        "name": "Lidarr",
        "category": "Media",
        "version": "3.1.0.4875-umbrel.1",
        "port": 30993,
        "internal_port": 8686,
        "image": "lscr.io/linuxserver/lidarr:latest@sha256:ba7d43fd5d7de790c38c2dc8f2b2b54c1ac00a452784891c37385a43a039907a",
        "tagline": "Music manager for the Arr stack",
        "description": "Manages music in Umbrel or linked network storage. umbrelarr configures the music root, both download clients, and Prowlarr synchronization.",
        "developer": "Lidarr",
        "website": "https://lidarr.audio",
        "repo": "https://github.com/Lidarr/Lidarr",
        "support": "https://github.com/Lidarr/Lidarr/issues",
        "kind": "servarr",
        "api_version": "v1",
        "root": "/downloads/music",
    },
}

SERVICE_SLUGS = [slug for slug in APPS if slug != "umbrelarr"]
STORAGE_SLUGS = {"qbittorrent", "sabnzbd", "sonarr", "sonarr-4k", "radarr", "radarr-4k", "bazarr", "umbrelarr", "lidarr"}


def app_id(slug):
    return f"{PREFIX}-{slug}"


def manifest(slug, app):
    dependencies = SERVICE_SLUGS if slug == "umbrelarr" else []
    lines = [
        "manifestVersion: 1",
        f"id: {app_id(slug)}",
        f"category: {app['category']}",
        f"name: {app['name']}",
        f'version: "{app["version"]}"',
        f"tagline: {app['tagline']}",
        "icon: icon.svg",
        "description: >-",
        f"  {app['description']}",
        "releaseNotes: >-",
        "  Initial Umbrel Arr package. Cross-service configuration is owned by",
        "  umbrelarr and internal credentials are generated at install time.",
        f"developer: {app['developer']}",
        f"website: {app['website']}",
    ]
    if dependencies:
        lines.append("dependencies:")
        lines.extend(f"  - {app_id(item)}" for item in dependencies)
    else:
        lines.append("dependencies: []")
    if slug in STORAGE_SLUGS:
        lines.extend(["permissions:", "  - STORAGE_DOWNLOADS"])
    lines.extend(
        [
            f"repo: {app['repo']}",
            f"support: {app['support']}",
            f"port: {app['port']}",
            "gallery: []",
            'path: ""',
            "deterministicPassword: false",
            "torOnly: false",
            "submitter: Umbrel Arr",
            'submission: ""',
        ]
    )
    return "\n".join(lines) + "\n"


def proxy(slug, internal_port):
    return dedent(
        f"""\
        version: "3.7"

        services:
          app_proxy:
            environment:
              APP_HOST: {app_id(slug)}_server_1
              APP_PORT: {internal_port}
        """
    )


def service_compose(slug, internal_port, block):
    rendered = dedent(block).strip() + "\n"
    return proxy(slug, internal_port) + indent(rendered, "  ")


def servarr_compose(slug, app):
    key_name = f"UMBREL_ARR_{slug.upper().replace('-', '_')}_API_KEY"
    storage = ""
    if app.get("root"):
        storage = "\n            - ${UMBREL_ROOT}/data/storage/downloads:/downloads\n            - ${UMBREL_ROOT}/data/storage/network:/network"
    return service_compose(slug, app["internal_port"],
        f"""\
        server:
          image: {app['image']}
          restart: on-failure
          entrypoint: [/bin/sh, -c]
          command:
            - |
              set -eu
              config=/config/config.xml
              mkdir -p /config
              [ -f "$$config" ] || printf '<Config>\\n</Config>\\n' > "$$config"

              set_xml_value() {{
                key=$$1
                value=$$2
                temporary=$$(mktemp /config/.umbrel-arr.XXXXXX)
                XML_KEY="$$key" XML_VALUE="$$value" awk '
                  BEGIN {{ key=ENVIRON["XML_KEY"]; value=ENVIRON["XML_VALUE"]; open="<" key ">"; close="</" key ">"; written=0 }}
                  index($$0, open) && index($$0, close) {{ print "  " open value close; written=1; next }}
                  index($$0, "</Config>") && !written {{ print "  " open value close; written=1 }}
                  {{ print }}
                ' "$$config" > "$$temporary"
                cat "$$temporary" > "$$config"
                rm -f "$$temporary"
              }}

              set_xml_value AuthenticationMethod External
              set_xml_value AuthenticationRequired DisabledForLocalAddresses
              set_xml_value ApiKey "$$SERVICE_API_KEY"
              exec /init
          environment:
            PUID: "1000"
            PGID: "1000"
            TZ: ${{TZ:-Etc/UTC}}
            SERVICE_API_KEY: ${{{key_name}:-}}
          volumes:
            - ${{APP_DATA_DIR}}/data/config:/config{storage}
        """
    )


def qbittorrent_compose(app):
    return service_compose("qbittorrent", 8080,
        f"""\
        server:
          image: {app['image']}
          restart: on-failure
          entrypoint: [/bin/sh, -c]
          command:
            - |
              set -eu
              config=/config/qBittorrent/qBittorrent.conf
              mkdir -p "$$(dirname "$$config")"
              [ -f "$$config" ] || printf '[Preferences]\\n' > "$$config"
              set_pref() {{
                key=$$1; value=$$2; tmp=$$(mktemp)
                QBIT_KEY="$$key" QBIT_VALUE="$$value" awk '
                  BEGIN {{ key=ENVIRON["QBIT_KEY"]; value=ENVIRON["QBIT_VALUE"]; written=0 }}
                  $$0 == "[Preferences]" {{ print; print key "=" value; written=1; next }}
                  index($$0, key "=") == 1 {{ next }}
                  {{ print }}
                ' "$$config" > "$$tmp"
                cat "$$tmp" > "$$config"; rm -f "$$tmp"
              }}
              set_pref 'WebUI\\HostHeaderValidation' 'false'
              set_pref 'WebUI\\ServerDomains' '*'
              set_pref 'WebUI\\SecureCookie' 'false'
              set_pref 'WebUI\\AuthSubnetWhitelistEnabled' 'true'
              set_pref 'WebUI\\AuthSubnetWhitelist' '0.0.0.0/0'
              set_pref 'Downloads\\SavePath' '/downloads/complete'
              set_pref 'Downloads\\TempPath' '/downloads/incomplete'
              set_pref 'Downloads\\TempPathEnabled' 'true'
              exec /init
          environment:
            PUID: "1000"
            PGID: "1000"
            TZ: ${{TZ:-Etc/UTC}}
            WEBUI_PORT: "8080"
            TORRENTING_PORT: "6881"
          volumes:
            - ${{APP_DATA_DIR}}/data/config:/config
            - ${{UMBREL_ROOT}}/data/storage/downloads:/downloads
        """
    )


def sabnzbd_compose(app):
    return service_compose("sabnzbd", 8080,
        f"""\
        server:
          image: {app['image']}
          restart: on-failure
          entrypoint: [/bin/sh, -c]
          command:
            - |
              set -eu
              bootstrap_key() {{
                config=/config/sabnzbd.ini
                api=http://127.0.0.1:8080/api
                attempts=0
                current_key=
                while [ "$$attempts" -lt 120 ]; do
                  if [ -f "$$config" ]; then
                    current_key=$$(awk -F= '/^[[:space:]]*api_key[[:space:]]*=/ {{ value=$$0; sub(/^[^=]*=[[:space:]]*/, "", value); sub(/[[:space:]]+$$/, "", value); print value; exit }}' "$$config")
                    [ -n "$$current_key" ] && break
                  fi
                  attempts=$$((attempts + 1)); sleep 2
                done
                [ -n "$$current_key" ] || return
                set_misc() {{
                  curl -fsS --get "$$api" --data-urlencode mode=set_config --data-urlencode section=misc --data-urlencode "keyword=$$1" --data-urlencode "value=$$2" --data-urlencode "apikey=$$current_key" --data-urlencode output=json >/dev/null
                }}
                set_misc host_whitelist "umbrel-arr-sabnzbd_server_1"
                set_misc complete_dir /downloads/complete
                set_misc download_dir /downloads/incomplete
                set_misc username ""
                set_misc password ""
                set_misc api_key "$$SABNZBD_API_KEY"
              }}
              bootstrap_key &
              exec /init
          environment:
            PUID: "1000"
            PGID: "1000"
            TZ: ${{TZ:-Etc/UTC}}
            SABNZBD_API_KEY: ${{UMBREL_ARR_SABNZBD_API_KEY:-}}
          volumes:
            - ${{APP_DATA_DIR}}/data/config:/config
            - ${{UMBREL_ROOT}}/data/storage/downloads:/downloads
        """
    )


def simple_compose(slug, app, environment="", volumes=""):
    lines = ["server:", f"  image: {app['image']}", "  restart: on-failure"]
    if environment:
        lines.append("  environment:")
        lines.extend(f"    {line.strip()}" for line in environment.splitlines() if line.strip())
    if volumes:
        lines.append("  volumes:")
        lines.extend(f"    {line.strip()}" for line in volumes.splitlines() if line.strip())
    return service_compose(slug, app["internal_port"], "\n".join(lines))


def setup_compose(app):
    env_lines = [
        "      TZ: ${TZ:-Etc/UTC}",
        "      DEVICE_DOMAIN_NAME: ${DEVICE_DOMAIN_NAME:-umbrel.local}",
        "      STATE_DIR: /data",
        "      RECONCILE_INTERVAL: \"300\"",
    ]
    for slug in SERVICE_SLUGS:
        var = slug.upper().replace("-", "_")
        internal = APPS[slug]["internal_port"]
        env_lines.append(f"      UMBREL_ARR_{var}_URL: ${{UMBREL_ARR_{var}_URL:-http://{app_id(slug)}_server_1:{internal}}}")
        if slug in {"prowlarr", "sabnzbd", "sonarr", "sonarr-4k", "radarr", "radarr-4k", "bazarr", "overseerr", "lidarr"}:
            env_lines.append(f"      UMBREL_ARR_{var}_API_KEY: ${{UMBREL_ARR_{var}_API_KEY:-}}")
    env_lines.extend(
        [
            "      UMBREL_ARR_PRIVADO_SOCKS_HOST: ${UMBREL_ARR_PRIVADO_SOCKS_HOST:-umbrel-arr-privado-vpn_server_1}",
            "      UMBREL_ARR_PRIVADO_SOCKS_PORT: ${UMBREL_ARR_PRIVADO_SOCKS_PORT:-1080}",
        ]
    )
    block = (
        f"server:\n"
        f"  image: {app['image']}\n"
        "  restart: on-failure\n"
        "  environment:\n"
        + "\n".join(f"    {line.strip()}" for line in env_lines)
        + "\n  volumes:\n"
        "    - ${APP_DATA_DIR}/data:/data\n"
        "    - ${UMBREL_ROOT}/data/storage/downloads:/downloads\n"
        "    - ${UMBREL_ROOT}/data/storage/network:/network\n"
    )
    return service_compose("umbrelarr", 8080, block)


def compose(slug, app):
    kind = app["kind"]
    if kind == "servarr":
        return servarr_compose(slug, app)
    if kind == "qbittorrent":
        return qbittorrent_compose(app)
    if kind == "sabnzbd":
        return sabnzbd_compose(app)
    if kind == "privado":
        return service_compose(
            slug,
            app["internal_port"],
            f"""\
            server:
              image: {app['image']}
              restart: on-failure
              cap_add: [NET_ADMIN]
              sysctls:
                net.ipv4.conf.all.src_valid_mark: "1"
              devices:
                - /dev/net/tun:/dev/net/tun
              environment:
                TZ: ${{TZ:-Etc/UTC}}
                SOCK_PORT: "1080"
                DASHBOARD_ENABLED: "true"
                DASHBOARD_PORT: "8080"
                PRIVADO_USERNAME: ""
                PRIVADO_PASSWORD: ""
                PRIVADO_SERVER: ""
              volumes:
                - ${{APP_DATA_DIR}}/data/config:/config
            """,
        )
    if kind == "flaresolverr":
        return simple_compose(
            slug,
            app,
            "    LOG_LEVEL: info\n    PROXY_URL: socks5://umbrel-arr-privado-vpn_server_1:1080",
        )
    if kind == "bazarr":
        return simple_compose(
            slug,
            app,
            "    PUID: \"1000\"\n    PGID: \"1000\"\n    TZ: ${TZ:-Etc/UTC}",
            "    - ${APP_DATA_DIR}/data/config:/config\n    - ${UMBREL_ROOT}/data/storage/downloads:/downloads\n    - ${UMBREL_ROOT}/data/storage/network:/network",
        )
    if kind == "overseerr":
        return simple_compose(
            slug,
            app,
            "    TZ: ${TZ:-Etc/UTC}\n    PORT: \"5055\"\n    CONFIG_DIRECTORY: /app/config",
            "    - ${APP_DATA_DIR}/data/config:/app/config",
        )
    if kind == "profilarr":
        return service_compose(slug, app["internal_port"],
            f"""\
            server:
              image: {app['image']}
              restart: on-failure
              environment:
                PUID: "1000"
                PGID: "1000"
                TZ: ${{TZ:-Etc/UTC}}
                AUTH: "off"
                PARSER_HOST: parser
                PARSER_PORT: "5000"
              volumes:
                - ${{APP_DATA_DIR}}/data/config:/config
              depends_on:
                parser:
                  condition: service_healthy

            parser:
              image: {app['parser_image']}
              restart: on-failure
            """
        )
    if kind == "setup":
        return setup_compose(app)
    raise ValueError(kind)


def random_key_exports(slug, extra=""):
    var = slug.upper().replace("-", "_")
    lines = [
        'key_file="${EXPORTS_APP_DATA_DIR}/.api-key"',
        'if [ ! -s "$key_file" ]; then',
        '  old_umask="$(umask)"',
        "  umask 077",
        '  mkdir -p "$EXPORTS_APP_DATA_DIR"',
        '  openssl rand -hex 16 > "$key_file"',
        '  umask "$old_umask"',
        "fi",
        f'export UMBREL_ARR_{var}_API_KEY="$(cat "$key_file")"',
        f'export UMBREL_ARR_{var}_URL="http://{app_id(slug)}_server_1:{APPS[slug]["internal_port"]}"',
    ]
    if extra:
        lines.extend(extra.splitlines())
    lines.append("unset key_file old_umask")
    return "\n".join(lines) + "\n"


def exports(slug, app):
    var = slug.upper().replace("-", "_")
    url = f"http://{app_id(slug)}_server_1:{app['internal_port']}"
    if app["kind"] == "servarr":
        return random_key_exports(slug)
    if slug == "sabnzbd":
        return random_key_exports(slug)
    if slug == "bazarr":
        extra = dedent(
            """\
            config_file="${EXPORTS_APP_DATA_DIR}/data/config/config.yaml"
            if [ ! -s "$config_file" ]; then
              mkdir -p "$(dirname "$config_file")"
              printf 'auth:\\n  apikey: %s\\n' "$UMBREL_ARR_BAZARR_API_KEY" > "$config_file"
            fi
            """
        ).strip()
        return random_key_exports(slug, extra)
    if slug == "overseerr":
        extra = dedent(
            """\
            settings_file="${EXPORTS_APP_DATA_DIR}/data/config/settings.json"
            if [ ! -s "$settings_file" ]; then
              mkdir -p "$(dirname "$settings_file")"
              printf '{"main":{"apiKey":"%s"}}\\n' "$UMBREL_ARR_OVERSEERR_API_KEY" > "$settings_file"
            fi
            """
        ).strip()
        return random_key_exports(slug, extra)
    if slug == "privado-vpn":
        return dedent(
            f"""\
            export UMBREL_ARR_PRIVADO_VPN_URL="{url}"
            export UMBREL_ARR_PRIVADO_SOCKS_HOST="{app_id(slug)}_server_1"
            export UMBREL_ARR_PRIVADO_SOCKS_PORT="1080"
            export UMBREL_ARR_PRIVADO_SOCKS_URL="socks5://{app_id(slug)}_server_1:1080"
            """
        )
    return f'export UMBREL_ARR_{var}_URL="{url}"\n'


def expected_files():
    result = {}
    for slug, app in APPS.items():
        directory = ROOT / app_id(slug)
        result[directory / "umbrel-app.yml"] = manifest(slug, app)
        result[directory / "docker-compose.yml"] = compose(slug, app)
        if slug != "umbrelarr":
            result[directory / "exports.sh"] = exports(slug, app)
        icon = ROOT / ".assets" / "icons" / f"{slug}.svg"
        result[directory / "icon.svg"] = icon.read_bytes()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    mismatches = []
    for path, content in expected_files().items():
        expected = content if isinstance(content, bytes) else content.encode()
        if args.check:
            if not path.exists() or path.read_bytes() != expected:
                mismatches.append(path.relative_to(ROOT))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(expected)
        if path.name == "exports.sh":
            path.chmod(0o755)
    if mismatches:
        print("Generated packages are stale:", file=sys.stderr)
        for path in mismatches:
            print(f"  {path}", file=sys.stderr)
        raise SystemExit(1)
    if not args.check:
        print(f"Generated {len(APPS)} app packages.")


if __name__ == "__main__":
    main()

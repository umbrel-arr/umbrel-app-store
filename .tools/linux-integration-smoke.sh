#!/usr/bin/env bash
set -euo pipefail

if [ "$(uname -s)" != "Linux" ] || [ "${UMBREL_ARR_LINUX_INTEGRATION:-}" != "1" ]; then
  printf '%s\n' "error: this container integration test is restricted to the Linux CI workflow" >&2
  exit 1
fi

command -v docker >/dev/null
docker compose version >/dev/null

readonly ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly RUN_TOKEN="${GITHUB_RUN_ID:-$$}-${GITHUB_RUN_ATTEMPT:-1}"
readonly STACK_NETWORK="umbrel-arr-integration-${RUN_TOKEN}"
readonly PROJECT_PREFIX="ua-ci-${RUN_TOKEN}"
readonly BASE="$(mktemp -d)"
readonly OVERRIDE="${BASE}/compose.override.yml"
readonly PARSER_OVERRIDE="${BASE}/compose.parser.yml"
readonly PYTHON_IMAGE="python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0"
readonly QBITTORRENT_PASSWORD="umbrel-arr-ci-${RUN_TOKEN}"
export RUN_TOKEN STACK_NETWORK

cleanup() {
  local exit_code="$?"
  local ids
  set +e
  ids="$(docker ps -aq --filter "label=umbrel-arr-smoke=${RUN_TOKEN}" 2>/dev/null || true)"
  if [ -n "$ids" ]; then
    docker rm -f $ids >/dev/null 2>&1
  fi
  docker network rm "$STACK_NETWORK" >/dev/null 2>&1
  sudo rm -rf "$BASE"
  return "$exit_code"
}
trap cleanup EXIT

cat > "$OVERRIDE" <<'YAML'
services:
  app_proxy:
    image: python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0
    command: [sleep, "3600"]
    labels:
      umbrel-arr-smoke: ${RUN_TOKEN}
    networks: [stack]
  server:
    labels:
      umbrel-arr-smoke: ${RUN_TOKEN}
    networks:
      stack:
        aliases:
          - ${INTEGRATION_SERVER_ALIAS}

networks:
  stack:
    external: true
    name: ${STACK_NETWORK}
YAML

cat > "$PARSER_OVERRIDE" <<'YAML'
services:
  parser:
    labels:
      umbrel-arr-smoke: ${RUN_TOKEN}
    networks: [stack]
YAML

mkdir -p \
  "${BASE}/umbrel/data/storage/downloads" \
  "${BASE}/umbrel/data/storage/network" \
  "${BASE}/apps"
sudo chown -R 1000:1000 "${BASE}/umbrel/data/storage"
docker network create "$STACK_NETWORK" >/dev/null

docker run -d \
  --name "${PROJECT_PREFIX}-privado-mock" \
  --label "umbrel-arr-smoke=${RUN_TOKEN}" \
  --network "$STACK_NETWORK" \
  --network-alias umbrel-arr-privado-vpn_server_1 \
  --volume "$ROOT/.tools/privado_ci_mock.py:/mock.py:ro" \
  "$PYTHON_IMAGE" \
  python3 -u /mock.py >/dev/null

cd "$ROOT"
. umbrel-arr-privado-vpn/exports.sh

compose_up() {
  local server_alias="$1"
  local app_data="$2"
  shift 2

  local attempt
  for attempt in $(seq 1 5); do
    if env \
      INTEGRATION_SERVER_ALIAS="$server_alias" \
      APP_DATA_DIR="$app_data" \
      UMBREL_ROOT="${BASE}/umbrel" \
        "$@" up -d --quiet-pull; then
      return 0
    fi
    printf 'Compose startup failed; retrying in %s seconds (attempt %s/5).\n' "$((attempt * 5))" "$attempt" >&2
    sleep "$((attempt * 5))"
  done
  return 1
}

start_app() {
  local slug="$1"
  local app_data="${BASE}/apps/${slug}"
  local before_export after_export
  mkdir -p "$app_data"
  if [ -f "umbrel-arr-${slug}/exports.sh" ]; then
    before_export="$(find "$app_data" -mindepth 1 -print | sort)"
    if [ "$slug" = "qbittorrent" ]; then
      APP_PASSWORD="$QBITTORRENT_PASSWORD" \
        EXPORTS_APP_DATA_DIR="${app_data}/data" \
        . "umbrel-arr-${slug}/exports.sh"
    else
      EXPORTS_APP_DATA_DIR="${app_data}/data" . "umbrel-arr-${slug}/exports.sh"
    fi
    after_export="$(find "$app_data" -mindepth 1 -print | sort)"
    if [ "$before_export" != "$after_export" ]; then
      printf 'Dependency export for %s modified app data.\n' "$slug" >&2
      return 1
    fi
  fi

  local compose=(
    docker compose
    -p "${PROJECT_PREFIX}-${slug}"
    -f "umbrel-arr-${slug}/docker-compose.yml"
    -f "$OVERRIDE"
  )
  if [ "$slug" = "profilarr" ]; then
    compose+=(-f "$PARSER_OVERRIDE")
  fi

  compose_up "umbrel-arr-${slug}_server_1" "$app_data" "${compose[@]}"
}

for slug in \
  flaresolverr prowlarr qbittorrent sabnzbd sonarr sonarr-4k radarr \
  radarr-4k bazarr overseerr profilarr lidarr; do
  start_app "$slug"
done

for slug in prowlarr sabnzbd sonarr sonarr-4k radarr radarr-4k bazarr overseerr lidarr; do
  var="UMBREL_ARR_${slug^^}_CONFIG_DIR"
  var="${var//-/_}"
  config_dir="${!var:-}"
  if [ -z "$config_dir" ] || [ ! -d "$config_dir" ]; then
    printf 'Missing generated config directory for %s: %s\n' "$slug" "${config_dir:-<unset>}" >&2
    exit 1
  fi
done

compose_up umbrel-arr-umbrelarr_server_1 "$BASE" \
  docker compose \
  -p "${PROJECT_PREFIX}-setup" \
  -f umbrel-arr-umbrelarr/docker-compose.yml \
  -f "$OVERRIDE"

setup_exec() {
  APP_DATA_DIR="$BASE" \
  UMBREL_ROOT="${BASE}/umbrel" \
    docker compose \
    -p "${PROJECT_PREFIX}-setup" \
    -f umbrel-arr-umbrelarr/docker-compose.yml \
    -f "$OVERRIDE" exec -T server "$@"
}

setup_request() {
  local method="$1"
  local path="$2"
  shift 2
  setup_exec python3 -c '
import sys
import urllib.error
import urllib.parse
import urllib.request

method, path, *pairs = sys.argv[1:]
values = dict(pair.split("=", 1) for pair in pairs)
body = urllib.parse.urlencode(values).encode() if pairs else None
request = urllib.request.Request(
    f"http://127.0.0.1:8080{path}",
    data=body,
    method=method,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
try:
    print(urllib.request.urlopen(request).read().decode())
except urllib.error.HTTPError as error:
    detail = error.read().decode("utf-8", "replace")
    print(detail or f"HTTP {error.code}", file=sys.stderr)
    raise SystemExit(1)
' "$method" "$path" "$@"
}

for _attempt in $(seq 1 90); do
  if setup_exec python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/healthz").read()' >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
setup_exec python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/healthz").read()'

setup_state=""
for _attempt in $(seq 1 90); do
  setup_state="$(setup_request POST /api/setup/detect 2>/dev/null || true)"
  if printf '%s' "$setup_state" | python3 -c '
import json, sys
data = json.load(sys.stdin)
raise SystemExit(not data.get("canConfirm"))
' 2>/dev/null; then
    break
  fi
  sleep 5
done

printf '%s' "$setup_state" | python3 -c '
import json, sys
data = json.load(sys.stdin)
assert data.get("phase") == "ready", data
assert data.get("confirmed") is False, data
assert data.get("canConfirm") is True, data
assert data.get("detectedCount") == data.get("requiredCount") == 13, data
assert all(app.get("reachable") for app in data.get("apps", [])), data
'

needs_qbittorrent_password="$(printf '%s' "$setup_state" | python3 -c '
import json, sys
apps = {app["id"]: app for app in json.load(sys.stdin).get("apps", [])}
print("1" if apps["qbittorrent"].get("action") == "temporary_password_required" else "0")
')"
qbittorrent_temporary_password=""
if [ "$needs_qbittorrent_password" = "1" ]; then
  qbittorrent_temporary_password="$(
    APP_DATA_DIR="${BASE}/apps/qbittorrent" \
    UMBREL_ROOT="${BASE}/umbrel" \
      docker compose \
      -p "${PROJECT_PREFIX}-qbittorrent" \
      -f umbrel-arr-qbittorrent/docker-compose.yml \
      -f "$OVERRIDE" logs --no-color server 2>&1 \
    | python3 -c '
import re, sys
matches = re.findall(
    r"temporary password is provided for this session:\s*([^\s\x1b]+)",
    sys.stdin.read(),
    re.IGNORECASE,
)
print(matches[-1] if matches else "")
'
  )"
  if [ -z "$qbittorrent_temporary_password" ]; then
    printf '%s\n' "qBittorrent requires its one-time password, but the smoke harness could not find it in the startup log." >&2
    exit 1
  fi

  # Prove that the redacted log handoff is a usable credential before asking
  # umbrelarr to consume it. The password remains in argv/memory only; output
  # contains status metadata and never echoes the secret.
  setup_exec python3 -c '
import sys
import urllib.error
import urllib.parse
import urllib.request

password = sys.argv[1]
origin = "http://umbrel-arr-qbittorrent_server_1:8080"
request = urllib.request.Request(
    f"{origin}/api/v2/auth/login",
    data=urllib.parse.urlencode({"username": "admin", "password": password}).encode(),
    method="POST",
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": origin,
        "Referer": f"{origin}/",
    },
)
try:
    response = urllib.request.urlopen(request)
    body = response.read().decode("utf-8", "replace").strip()
    cookie = response.headers.get("Set-Cookie", "")
except urllib.error.HTTPError as error:
    body = error.read().decode("utf-8", "replace").strip()
    print(
        f"qBittorrent rejected its startup credential: HTTP {error.code}; "
        f"password_length={len(password)}; response={body[:80]!r}",
        file=sys.stderr,
    )
    raise SystemExit(1)
if body.casefold().startswith("fails") or "SID=" not in cookie:
    print(
        f"qBittorrent returned an unusable login response; "
        f"password_length={len(password)}; response={body[:80]!r}",
        file=sys.stderr,
    )
    raise SystemExit(1)
' "$qbittorrent_temporary_password"
fi

setup_request POST /api/setup/confirm \
  "storageMode=local" \
  "rootIds={}" \
  "qbittorrentUsername=admin" \
  "qbittorrentTemporaryPassword=${qbittorrent_temporary_password}" >/dev/null
unset qbittorrent_temporary_password

wait_for_reconcile() {
  local previous_completed="${1:-}"
  local status=""
  local completed=""
  local last_failure_signature=""
  local failure_signature=""
  local stable_failures=0
  local _attempt
  for _attempt in $(seq 1 90); do
    status="$(setup_request GET /api/status 2>/dev/null || true)"
    completed="$(printf '%s' "$status" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("lastCompletedAt", ""))' 2>/dev/null || true)"
    if [ -n "$completed" ] && [ "$completed" != "$previous_completed" ] && printf '%s' "$status" | python3 -c '
import json, sys
data = json.load(sys.stdin)
counts = data.get("counts", {})
services = data.get("services", [])
pending = [
    service for service in services
    if service.get("status") in {"unknown", "waiting", "configuring"}
    and not (service.get("id") == "profilarr" and service.get("status") == "waiting")
]
raise SystemExit(bool(data.get("running") or counts.get("failed") or pending))
' 2>/dev/null; then
      printf '%s' "$status"
      return 0
    fi

    failure_signature="$(printf '%s' "$status" | python3 -c '
import json, sys
data = json.load(sys.stdin)
if data.get("running"):
    raise SystemExit
failed = sorted(
    (service.get("id"), service.get("detail"))
    for service in data.get("services", [])
    if service.get("status") == "failed"
)
if failed:
    print(json.dumps(failed, separators=(",", ":")))
' 2>/dev/null || true)"
    if [ -n "$failure_signature" ] && [ "$failure_signature" = "$last_failure_signature" ]; then
      stable_failures=$((stable_failures + 1))
    elif [ -n "$failure_signature" ]; then
      last_failure_signature="$failure_signature"
      stable_failures=1
    else
      last_failure_signature=""
      stable_failures=0
    fi
    if [ "$stable_failures" -ge 3 ]; then
      printf '%s\n' "Stopping after three identical deterministic failure reports." >&2
      break
    fi
    sleep 10
  done
  printf '%s' "$status" >&2
  return 1
}

first_status="$(wait_for_reconcile)"
first_completed="$(printf '%s' "$first_status" | python3 -c 'import json,sys; print(json.load(sys.stdin)["lastCompletedAt"])')"
sleep 1
setup_request POST /api/reconcile >/dev/null
second_status="$(wait_for_reconcile "$first_completed")"

printf '%s' "$second_status" | python3 -c '
import json, sys
data = json.load(sys.stdin)
counts = data.get("counts", {})
services = {service["id"]: service for service in data.get("services", [])}
assert data.get("lastCompletedAt"), "reconciliation never completed"
assert not counts.get("failed"), data
assert services["privado-vpn"]["status"] == "healthy", data
assert services["overseerr"]["status"] == "action_required", data
assert services["profilarr"]["status"] in {"healthy", "waiting"}, data
print(json.dumps(data, indent=2, sort_keys=True))
'
storage_before_restart="$(setup_request GET /api/storage)"

APP_DATA_DIR="$BASE" UMBREL_ROOT="${BASE}/umbrel" \
  docker compose \
  -p "${PROJECT_PREFIX}-setup" \
  -f umbrel-arr-umbrelarr/docker-compose.yml \
  -f "$OVERRIDE" restart server >/dev/null
for _attempt in $(seq 1 90); do
  if setup_request GET /healthz >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
restored_setup="$(setup_request GET /api/setup)"
printf '%s' "$restored_setup" | python3 -c '
import json, sys
data = json.load(sys.stdin)
assert data.get("phase") == "confirmed", data
assert data.get("confirmed") is True, data
'
storage_after_restart="$(setup_request GET /api/storage)"
python3 -c '
import json, sys
before, after = (json.loads(value) for value in sys.argv[1:])
for key in ("mode", "roots", "rootIds", "actionRequired"):
    assert after.get(key) == before.get(key), (key, before, after)
' "$storage_before_restart" "$storage_after_restart"

setup_id="$(
  APP_DATA_DIR="$BASE" UMBREL_ROOT="${BASE}/umbrel" \
    docker compose \
    -p "${PROJECT_PREFIX}-setup" \
    -f umbrel-arr-umbrelarr/docker-compose.yml \
    -f "$OVERRIDE" ps -q server
)"
docker inspect "$setup_id" | python3 -c '
import json, sys
container = json.load(sys.stdin)[0]
assert container["HostConfig"]["ReadonlyRootfs"], container["Name"]
mounts = container.get("Mounts", [])
assert not any(mount["Destination"] == "/data" for mount in mounts), mounts
configs = [mount for mount in mounts if mount["Destination"].startswith("/managed-config/")]
assert len(configs) == 9, configs
assert all(not mount["RW"] for mount in configs), configs
print("Verified stateless read-only umbrelarr runtime and nine read-only config mounts.")
'

ids="$(docker ps -q --filter "label=umbrel-arr-smoke=${RUN_TOKEN}")"
docker inspect $ids | python3 -c '
import json, sys
containers = json.load(sys.stdin)
bound = [container["Name"] for container in containers if container["HostConfig"].get("PortBindings")]
assert not bound, f"host port bindings detected: {bound}"
print(f"Verified {len(containers)} containers with no host port bindings.")
'

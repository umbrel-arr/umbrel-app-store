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
docker network create "$STACK_NETWORK" >/dev/null

docker run -d \
  --name "${PROJECT_PREFIX}-privado-mock" \
  --label "umbrel-arr-smoke=${RUN_TOKEN}" \
  --network "$STACK_NETWORK" \
  --network-alias umbrel-arr-privado-vpn_server_1 \
  "$PYTHON_IMAGE" \
  python3 -u -c 'import json; from http.server import BaseHTTPRequestHandler,HTTPServer
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  body=json.dumps({"state":"healthy","credentialsConfigured":True,"detail":"Connected"}).encode(); self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
 def log_message(self,*_args): pass
HTTPServer(("0.0.0.0",8080),Handler).serve_forever()' >/dev/null

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
  mkdir -p "$app_data"
  if [ -f "umbrel-arr-${slug}/exports.sh" ]; then
    EXPORTS_APP_DATA_DIR="$app_data" . "umbrel-arr-${slug}/exports.sh"
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

readonly SETUP_DATA="${BASE}/apps/setup"
mkdir -p "$SETUP_DATA"
compose_up umbrel-arr-setup_server_1 "$SETUP_DATA" \
  docker compose \
  -p "${PROJECT_PREFIX}-setup" \
  -f umbrel-arr-setup/docker-compose.yml \
  -f "$OVERRIDE"

setup_exec() {
  APP_DATA_DIR="$SETUP_DATA" \
  UMBREL_ROOT="${BASE}/umbrel" \
    docker compose \
    -p "${PROJECT_PREFIX}-setup" \
    -f umbrel-arr-setup/docker-compose.yml \
    -f "$OVERRIDE" exec -T server "$@"
}

for _attempt in $(seq 1 90); do
  if setup_exec python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/healthz").read()' >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
setup_exec python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/healthz").read()'

status=""
for _attempt in $(seq 1 90); do
  status="$(setup_exec python3 -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8080/api/status").read().decode())' 2>/dev/null || true)"
  if printf '%s' "$status" | python3 -c '
import json, sys
data = json.load(sys.stdin)
counts = data.get("counts", {})
pending = sum(counts.get(name, 0) for name in ("unknown", "waiting", "configuring"))
raise SystemExit(not (data.get("lastCompletedAt") and not data.get("running") and not counts.get("failed") and not pending))
' 2>/dev/null; then
    break
  fi

  if printf '%s' "$status" | python3 -c 'import json,sys; raise SystemExit(json.load(sys.stdin).get("running", True))' 2>/dev/null; then
    setup_exec python3 -c 'import urllib.request; request=urllib.request.Request("http://127.0.0.1:8080/api/reconcile",data=b"",method="POST"); urllib.request.urlopen(request).read()' >/dev/null
  fi
  sleep 10
done

printf '%s' "$status" | python3 -c '
import json, sys
data = json.load(sys.stdin)
counts = data.get("counts", {})
pending = sum(counts.get(name, 0) for name in ("unknown", "waiting", "configuring"))
services = {service["id"]: service for service in data.get("services", [])}
assert data.get("lastCompletedAt"), "reconciliation never completed"
assert not counts.get("failed"), data
assert not pending, data
assert services["privado-vpn"]["status"] == "healthy", data
assert services["overseerr"]["status"] == "action_required", data
print(json.dumps(data, indent=2, sort_keys=True))
'

ids="$(docker ps -q --filter "label=umbrel-arr-smoke=${RUN_TOKEN}")"
docker inspect $ids | python3 -c '
import json, sys
containers = json.load(sys.stdin)
bound = [container["Name"] for container in containers if container["HostConfig"].get("PortBindings")]
assert not bound, f"host port bindings detected: {bound}"
print(f"Verified {len(containers)} containers with no host port bindings.")
'

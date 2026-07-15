#!/usr/bin/env bash
set -euo pipefail

if [ "$(uname -s)" != "Linux" ] || [ "${UMBREL_ARR_LINUX_INTEGRATION:-}" != "1" ]; then
  printf '%s\n' "error: this container integration test is restricted to the Linux CI workflow" >&2
  exit 1
fi

command -v docker >/dev/null

readonly ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly RUN_TOKEN="${GITHUB_RUN_ID:-$$}-${GITHUB_RUN_ATTEMPT:-1}"
readonly CONTAINER="umbrel-arr-privado-process-${RUN_TOKEN}"
readonly CONFIG_DIR="$(mktemp -d)"
readonly IMAGE="$(
  sed -n 's/^    image: \([^ ]*\)$/\1/p' \
    "${ROOT}/umbrel-arr-privado-vpn/docker-compose.yml"
)"

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  rm -rf "$CONFIG_DIR"
}

diagnose() {
  local status="$?"
  if [ "$status" -ne 0 ]; then
    printf '%s\n' "Privado lifecycle test failed; collecting credential-free diagnostics." >&2
    docker inspect --format '{{json .State}}' "$CONTAINER" >&2 || true
    docker logs "$CONTAINER" >&2 || true
    docker exec "$CONTAINER" supervisorctl status >&2 || true
  fi
  cleanup
  exit "$status"
}
trap diagnose EXIT

docker run -d \
  --name "$CONTAINER" \
  --cap-add NET_ADMIN \
  --sysctl net.ipv4.conf.all.src_valid_mark=1 \
  --volume "${CONFIG_DIR}:/config" \
  --env DASHBOARD_ENABLED=true \
  --env DASHBOARD_PORT=8080 \
  --env SOCK_PORT=1080 \
  "$IMAGE" >/dev/null

dashboard_ready=false
for _attempt in $(seq 1 30); do
  if docker exec "$CONTAINER" curl -fsS http://127.0.0.1:8080/api/status >/dev/null; then
    dashboard_ready=true
    break
  fi
  sleep 1
done

if [ "$dashboard_ready" != "true" ]; then
  printf '%s\n' "Privado dashboard did not become ready." >&2
  exit 1
fi

dashboard_status=""
for _attempt in $(seq 1 10); do
  dashboard_status="$(timeout 10 docker exec "$CONTAINER" supervisorctl status dashboard || true)"
  if [[ "$dashboard_status" == *RUNNING* ]]; then
    break
  fi
  sleep 1
done
if [[ "$dashboard_status" != *RUNNING* ]]; then
  printf '%s\n' "Privado dashboard is not supervised as RUNNING: ${dashboard_status}" >&2
  exit 1
fi

main_status=""
for _attempt in $(seq 1 15); do
  main_status="$(timeout 10 docker exec "$CONTAINER" supervisorctl status main || true)"
  if [[ "$main_status" =~ (EXITED|STOPPED|FATAL) ]]; then
    break
  fi
  sleep 1
done
if [[ ! "$main_status" =~ (EXITED|STOPPED|FATAL) ]]; then
  printf '%s\n' "Privado main did not settle without credentials: ${main_status}" >&2
  exit 1
fi

set +e
timeout 10 docker exec "$CONTAINER" supervisorctl start main >/dev/null 2>&1
start_status="$?"
set -e
if [ "$start_status" -eq 124 ]; then
  printf '%s\n' "Privado main startup deadlocked supervisor RPC." >&2
  exit 1
fi

dashboard_status="$(timeout 10 docker exec "$CONTAINER" supervisorctl status dashboard || true)"
if [[ "$dashboard_status" != *RUNNING* ]]; then
  printf '%s\n' "Privado dashboard stopped responding after main startup: ${dashboard_status}" >&2
  exit 1
fi
if docker exec "$CONTAINER" pgrep -x microsocks >/dev/null; then
  printf '%s\n' "SOCKS5 started without a healthy WireGuard tunnel." >&2
  exit 1
fi

#!/bin/bash

set -u -o pipefail

source /scripts/vars.sh
source /scripts/utils.sh
source /scripts/iptables.sh
source /scripts/privado.sh
source /scripts/dante.sh

cleanup_after_failure() {
  local status=$?
  trap - EXIT

  if [[ ${status} -ne 0 ]]; then
    log "WARNING: PRIVADO: Startup failed; restoring the original network state"
    cleanup_wireguard_state
  fi

  exit "${status}"
}

trap cleanup_after_failure EXIT

# Supervisor restarts reuse the container network namespace. Remove stale
# tunnel state before any API or DNS request tries to use the old default route.
cleanup_wireguard_state

print_settings
set_timezone

log "INFO: Dashboard lifecycle is managed directly by supervisord"

# Set sysctl for WireGuard policy-based routing
# First check if it's already set correctly
if current_value=$(sysctl -n net.ipv4.conf.all.src_valid_mark 2>/dev/null); then
  if [[ "${current_value}" == "1" ]]; then
    log "INFO: net.ipv4.conf.all.src_valid_mark is already set to 1"
  else
    log "INFO: Setting net.ipv4.conf.all.src_valid_mark=1 for WireGuard (current value: ${current_value})"
    if ! error_msg=$(sysctl -w net.ipv4.conf.all.src_valid_mark=1 2>&1); then
      log "WARNING: Failed to set src_valid_mark sysctl: ${error_msg}"
      log "WARNING: This sysctl requires privileged mode or allowedUnsafeSysctls in Kubernetes"
      log "WARNING: WireGuard policy-based routing may not work correctly"
      log "WARNING: See README for Kubernetes deployment instructions"
    else
      log "INFO: Successfully set net.ipv4.conf.all.src_valid_mark=1"
    fi
  fi
else
  # sysctl read failed - try to set it anyway
  log "INFO: Setting net.ipv4.conf.all.src_valid_mark=1 for WireGuard"
  if ! error_msg=$(sysctl -w net.ipv4.conf.all.src_valid_mark=1 2>&1); then
    log "WARNING: Failed to set src_valid_mark sysctl: ${error_msg}"
    log "WARNING: This sysctl requires privileged mode or allowedUnsafeSysctls in Kubernetes"
    log "WARNING: WireGuard policy-based routing may not work correctly"
    log "WARNING: See README for Kubernetes deployment instructions"
  else
    log "INFO: Successfully set net.ipv4.conf.all.src_valid_mark=1"
  fi
fi

# Validate required parameters
if [[ -z ${PRIVADO_USERNAME} ]] || [[ -z ${PRIVADO_PASSWORD} ]]; then
  log "ERROR: PRIVADO_USERNAME and PRIVADO_PASSWORD are required"
  log "ERROR: Set these via environment variables, Docker secrets, or ${CONFIG_FILE}"
  if [[ "${DASHBOARD_ENABLED,,}" == "true" ]]; then
    log "INFO: Dashboard remains available for browser setup; VPN process is waiting to be started"
    exit 0
  fi
  exit 1
fi

# Setup Privado VPN via WireGuard
login_privado
get_servers
get_wireguard_config
setup_wireguard
connect_privado
check_connection

# Setup iptables and DNS
enforce_proxies_iptables
setup_dns

# Log public IP for verification
PUBLIC_IP=$(get_public_ip)
log "INFO: Public IP: ${PUBLIC_IP}"

# Hand the supervised main process over to the SOCKS5 proxy only after the
# tunnel is healthy. This keeps supervisor RPC available to the dashboard and
# prevents the proxy from ever relaying traffic before WireGuard is ready.
setup_dante
log "INFO: Privado VPN Proxy is ready"
log "INFO: SOCKS5 proxy available on port ${SOCK_PORT}"
if [[ "${DASHBOARD_ENABLED,,}" == "true" ]]; then
  log "INFO: Dashboard available on port ${DASHBOARD_PORT}"
fi
start_dante

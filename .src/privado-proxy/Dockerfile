FROM debian:bookworm-slim@sha256:60eac759739651111db372c07be67863818726f754804b8707c90979bda511df

LABEL org.opencontainers.image.source="https://github.com/umbrel-arr/umbrel-app-store" \
      org.opencontainers.image.title="Umbrel Arr Privado Proxy" \
      org.opencontainers.image.description="Privado WireGuard and SOCKS5 gateway with an Umbrel setup dashboard"

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install dependencies including WireGuard and microsocks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl jq microsocks supervisor iproute2 iptables python3 \
    net-tools gettext wireguard-tools procps \
    && apt-get clean all && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create user and group
RUN addgroup --system vpn && useradd -lNms /bin/bash -u "${NUID:-1000}" -G vpn privadoclient

# Install scripts and make them executable
COPY scripts/ /scripts/
RUN chmod +x /scripts/*.sh

COPY etc/ /etc/

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
HEALTHCHECK --interval=5m --timeout=1m --start-period=1m CMD /scripts/healthcheck.sh
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]

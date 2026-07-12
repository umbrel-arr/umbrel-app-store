# Icon Sources

The upstream app icons in this directory are the opaque 256x256 artwork
published by the [official Umbrel app gallery](https://getumbrel.github.io/umbrel-apps-gallery/):

- Bazarr
- FlareSolverr
- Lidarr
- Overseerr
- Prowlarr
- qBittorrent
- Radarr
- SABnzbd
- Sonarr

Profilarr uses the official `logo.svg` from
`Dictionarry-Hub/profilarr`. Privado VPN uses the upstream Privado mark that
shipped with `lucasilverentand/privado-proxy`.

Run `.tools/generate-icons.py` to produce the final app icons. The generator
adds full-canvas treatments for custom apps and clear badges for the 4K
instances. Do not hand-edit files under `.assets/icons/`.

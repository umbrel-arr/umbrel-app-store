umbrel_arr_apps_root="${EXPORTS_APP_DIR%/*}"
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-prowlarr/data/config" ]; then
  export UMBREL_ARR_PROWLARR_CONFIG_DIR="${umbrel_arr_apps_root}/umbrel-arr-prowlarr/data/config"
fi
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-sabnzbd/data/config" ]; then
  export UMBREL_ARR_SABNZBD_CONFIG_DIR="${umbrel_arr_apps_root}/umbrel-arr-sabnzbd/data/config"
fi
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-sonarr/data/config" ]; then
  export UMBREL_ARR_SONARR_CONFIG_DIR="${umbrel_arr_apps_root}/umbrel-arr-sonarr/data/config"
fi
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-sonarr-4k/data/config" ]; then
  export UMBREL_ARR_SONARR_4K_CONFIG_DIR="${umbrel_arr_apps_root}/umbrel-arr-sonarr-4k/data/config"
fi
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-radarr/data/config" ]; then
  export UMBREL_ARR_RADARR_CONFIG_DIR="${umbrel_arr_apps_root}/umbrel-arr-radarr/data/config"
fi
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-radarr-4k/data/config" ]; then
  export UMBREL_ARR_RADARR_4K_CONFIG_DIR="${umbrel_arr_apps_root}/umbrel-arr-radarr-4k/data/config"
fi
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-bazarr/data/config" ]; then
  export UMBREL_ARR_BAZARR_CONFIG_DIR="${umbrel_arr_apps_root}/umbrel-arr-bazarr/data/config"
fi
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-overseerr/data/config" ]; then
  export UMBREL_ARR_OVERSEERR_CONFIG_DIR="${umbrel_arr_apps_root}/umbrel-arr-overseerr/data/config"
fi
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-lidarr/data/config" ]; then
  export UMBREL_ARR_LIDARR_CONFIG_DIR="${umbrel_arr_apps_root}/umbrel-arr-lidarr/data/config"
fi
if [ -d "${umbrel_arr_apps_root}/umbrel-arr-qbittorrent" ]; then
  export UMBREL_ARR_QBITTORRENT_PASSWORD="$(derive_entropy "app-umbrel-arr-qbittorrent-seed-APP_PASSWORD")"
  export UMBREL_ARR_QBITTORRENT_LEGACY_PASSWORD="$(derive_entropy "app-umbrel-arr-umbrelarr-seed-APP_PASSWORD")"
fi
unset umbrel_arr_apps_root

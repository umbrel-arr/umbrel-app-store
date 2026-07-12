export UMBREL_ARR_QBITTORRENT_URL="http://umbrel-arr-qbittorrent_server_1:8080"
config_file="${EXPORTS_APP_DATA_DIR}/config/qBittorrent/qBittorrent.conf"
if [ ! -s "$config_file" ]; then
  mkdir -p "$(dirname "$config_file")"
  printf '%s\n' '[Preferences]' 'WebUI\HostHeaderValidation=false' 'WebUI\ServerDomains=*' 'WebUI\SecureCookie=false' 'WebUI\AuthSubnetWhitelistEnabled=true' 'WebUI\AuthSubnetWhitelist=0.0.0.0/0' 'Downloads\SavePath=/downloads/complete' 'Downloads\TempPath=/downloads/incomplete' 'Downloads\TempPathEnabled=true' > "$config_file"
fi
unset config_file

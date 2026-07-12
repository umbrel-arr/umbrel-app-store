key_file="${EXPORTS_APP_DATA_DIR}/.api-key"
if [ ! -s "$key_file" ]; then
  old_umask="$(umask)"
  umask 077
  mkdir -p "$EXPORTS_APP_DATA_DIR"
  openssl rand -hex 16 > "$key_file"
  umask "$old_umask"
fi
export UMBREL_ARR_SABNZBD_API_KEY="$(cat "$key_file")"
export UMBREL_ARR_SABNZBD_URL="http://umbrel-arr-sabnzbd_server_1:8080"
config_file="${EXPORTS_APP_DATA_DIR}/config/sabnzbd.ini"
if [ ! -s "$config_file" ]; then
  mkdir -p "$(dirname "$config_file")"
  printf '__version__ = 19\n__encoding__ = utf-8\n[misc]\napi_key = %s\nhost_whitelist = umbrel-arr-sabnzbd_server_1\ncomplete_dir = /downloads/complete\ndownload_dir = /downloads/incomplete\nusername =\npassword =\n' "$UMBREL_ARR_SABNZBD_API_KEY" > "$config_file"
fi
unset key_file old_umask

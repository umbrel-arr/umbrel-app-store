key_file="${EXPORTS_APP_DATA_DIR}/.api-key"
if [ ! -s "$key_file" ]; then
  old_umask="$(umask)"
  umask 077
  mkdir -p "$EXPORTS_APP_DATA_DIR"
  openssl rand -hex 16 > "$key_file"
  umask "$old_umask"
fi
export UMBREL_ARR_OVERSEERR_API_KEY="$(cat "$key_file")"
export UMBREL_ARR_OVERSEERR_URL="http://umbrel-arr-overseerr_server_1:5055"
settings_file="${EXPORTS_APP_DATA_DIR}/config/settings.json"
if [ ! -s "$settings_file" ]; then
  mkdir -p "$(dirname "$settings_file")"
  printf '{"main":{"apiKey":"%s"}}\n' "$UMBREL_ARR_OVERSEERR_API_KEY" > "$settings_file"
fi
unset key_file old_umask

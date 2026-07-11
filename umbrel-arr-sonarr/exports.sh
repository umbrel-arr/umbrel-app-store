key_file="${EXPORTS_APP_DATA_DIR}/.api-key"
if [ ! -s "$key_file" ]; then
  old_umask="$(umask)"
  umask 077
  mkdir -p "$EXPORTS_APP_DATA_DIR"
  openssl rand -hex 16 > "$key_file"
  umask "$old_umask"
fi
export UMBREL_ARR_SONARR_API_KEY="$(cat "$key_file")"
export UMBREL_ARR_SONARR_URL="http://umbrel-arr-sonarr_server_1:8989"
unset key_file old_umask

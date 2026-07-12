key_file="${EXPORTS_APP_DATA_DIR}/.api-key"
if [ ! -s "$key_file" ]; then
  old_umask="$(umask)"
  umask 077
  mkdir -p "$EXPORTS_APP_DATA_DIR"
  openssl rand -hex 16 > "$key_file"
  umask "$old_umask"
fi
export UMBREL_ARR_PROWLARR_API_KEY="$(cat "$key_file")"
export UMBREL_ARR_PROWLARR_URL="http://umbrel-arr-prowlarr_server_1:9696"
config_file="${EXPORTS_APP_DATA_DIR}/config/config.xml"
if [ ! -s "$config_file" ]; then
  mkdir -p "$(dirname "$config_file")"
  printf '<Config>\n  <AuthenticationMethod>External</AuthenticationMethod>\n  <AuthenticationRequired>DisabledForLocalAddresses</AuthenticationRequired>\n  <ApiKey>%s</ApiKey>\n</Config>\n' "$UMBREL_ARR_PROWLARR_API_KEY" > "$config_file"
fi
unset key_file old_umask

#!/usr/bin/env bash
set -euo pipefail

BUNDLE_DIR=${1:-.}
SERVICE_NAME=${SERVICE_NAME:-xray}
XRAY_BIN=${XRAY_BIN:-/usr/local/bin/xray}
CONFIG_TARGET=${CONFIG_TARGET:-/etc/xray/${SERVICE_NAME}.json}
SERVICE_TARGET=${SERVICE_TARGET:-/etc/systemd/system/${SERVICE_NAME}.service}
PROXIES_TXT=${PROXIES_TXT:-$BUNDLE_DIR/proxies.txt}
RENDER_SUMMARY=${RENDER_SUMMARY:-1}
SUMMARY_RENDERER=${SUMMARY_RENDERER:-$BUNDLE_DIR/render_preflight_summary.py}

json_escape() {
  python3 - <<'PY' "$1"
import json, sys
print(json.dumps(sys.argv[1]))
PY
}

append_json_array() {
  local -n arr_ref=$1
  local value=$2
  arr_ref+=("$(json_escape "$value")")
}

local_ipv4s() {
  ip -o -4 addr show 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | sort -u
}

service_active() {
  systemctl is-active "$1" >/dev/null 2>&1
}

list_xray_services() {
  systemctl list-unit-files --type=service --no-legend 2>/dev/null | awk '{print $1}' | grep '^xray' || true
}

port_in_use() {
  local ip=$1
  local port=$2
  ss -lnt 2>/dev/null | awk '{print $4}' | grep -Eq "(^|[\[\]:])${ip//./\\.}:${port}$|^${ip//./\\.}:${port}$"
}

emit_json() {
  local status=$1
  local -n issues_ref=$2
  local -n warnings_ref=$3
  local -n suggestions_ref=$4
  local -n bind_ref=$5

  printf '{\n'
  printf '  "bundle_dir": %s,\n' "$(json_escape "$BUNDLE_DIR")"
  printf '  "service_name": %s,\n' "$(json_escape "$SERVICE_NAME")"
  printf '  "xray_bin": %s,\n' "$(json_escape "$XRAY_BIN")"
  printf '  "config_target": %s,\n' "$(json_escape "$CONFIG_TARGET")"
  printf '  "service_target": %s,\n' "$(json_escape "$SERVICE_TARGET")"
  printf '  "issues": [%s],\n' "$(IFS=,; echo "${issues_ref[*]:-}")"
  printf '  "warnings": [%s],\n' "$(IFS=,; echo "${warnings_ref[*]:-}")"
  printf '  "suggestions": [%s],\n' "$(IFS=,; echo "${suggestions_ref[*]:-}")"
  printf '  "bind_checks": [%s],\n' "$(IFS=,; echo "${bind_ref[*]:-}")"
  printf '  "status": %s\n' "$(json_escape "$status")"
  printf '}\n'
}

main() {
  local issues=()
  local warnings=()
  local suggestions=()
  local bind_checks=()
  local all_local_ips
  local result_file
  result_file=$(mktemp)

  if [[ ! -f "$PROXIES_TXT" ]]; then
    append_json_array issues "Missing proxies.txt: $PROXIES_TXT"
  fi

  if [[ ! -x "$XRAY_BIN" ]]; then
    append_json_array issues "xray binary not found: $XRAY_BIN"
  fi

  if ! command -v systemctl >/dev/null 2>&1; then
    append_json_array issues "systemctl not found; this host may not be systemd-based"
  fi

  if [[ -f "$SERVICE_TARGET" ]]; then
    append_json_array warnings "Service file already exists: $SERVICE_TARGET"
    if [[ "$SERVICE_NAME" == "xray" ]]; then
      append_json_array suggestions "Current target is default xray service; consider SERVICE_NAME=xray-test for side-by-side testing"
    fi
  fi

  if [[ -f "$CONFIG_TARGET" ]]; then
    append_json_array warnings "Config file already exists: $CONFIG_TARGET"
  fi

  if command -v systemctl >/dev/null 2>&1; then
    if service_active "$SERVICE_NAME"; then
      append_json_array warnings "Service is already active: $SERVICE_NAME"
      append_json_array suggestions "Use AUTO_START=0 for file-only install, or switch to SERVICE_NAME=xray-test before touching a live service"
    fi

    mapfile -t other_xray < <(list_xray_services | grep -v "^${SERVICE_NAME}\.service$" || true)
    if (( ${#other_xray[@]} > 0 )); then
      append_json_array warnings "Other xray-like services found: ${other_xray[*]}"
      append_json_array suggestions "If these are production services, prefer sidecar testing with SERVICE_NAME=xray-test"
    fi
  fi

  mapfile -t all_local_ips < <(local_ipv4s)

  if [[ -f "$PROXIES_TXT" ]]; then
    while read -r name endpoint _; do
      [[ -z "${name:-}" ]] && continue
      local ip=${endpoint%:*}
      local port=${endpoint##*:}
      local found_local=0
      for lip in "${all_local_ips[@]:-}"; do
        if [[ "$lip" == "$ip" ]]; then
          found_local=1
          break
        fi
      done

      if (( found_local == 0 )); then
        bind_checks+=("{\"name\":$(json_escape "$name"),\"listen\":$(json_escape "$endpoint"),\"status\":\"ip_not_local\"}")
        append_json_array warnings "Target bind IP is not present on this machine: $name -> $endpoint"
        continue
      fi

      if port_in_use "$ip" "$port"; then
        bind_checks+=("{\"name\":$(json_escape "$name"),\"listen\":$(json_escape "$endpoint"),\"status\":\"port_in_use\"}")
        append_json_array warnings "Port conflict detected on this machine: $name -> $endpoint"
      else
        bind_checks+=("{\"name\":$(json_escape "$name"),\"listen\":$(json_escape "$endpoint"),\"status\":\"bind_ok\"}")
      fi
    done < "$PROXIES_TXT"
  fi

  if printf '%s\n' "${warnings[@]:-}" | grep -q 'Target bind IP is not present on this machine'; then
    append_json_array suggestions "Run this remote preflight on the actual target server that owns the bind IPs"
  fi

  local status="ok"
  if (( ${#issues[@]} > 0 )); then
    status="fail"
  fi

  emit_json "$status" issues warnings suggestions bind_checks | tee "$result_file"

  if [[ "$RENDER_SUMMARY" == "1" && -f "$SUMMARY_RENDERER" ]]; then
    python3 "$SUMMARY_RENDERER" "$result_file" || true
  fi

  rm -f "$result_file"
  [[ "$status" == "ok" ]]
}

main "$@"

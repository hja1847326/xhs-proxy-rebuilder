#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
OUTPUT_DIR=${1:-"$PROJECT_DIR/generated-build"}
XRAY_BIN=${XRAY_BIN:-/usr/local/bin/xray}
SERVICE_NAME=${SERVICE_NAME:-xray}
XRAY_CONFIG_TARGET=${XRAY_CONFIG_TARGET:-/etc/xray/${SERVICE_NAME}.json}
XRAY_SERVICE_TARGET=${XRAY_SERVICE_TARGET:-/etc/systemd/system/${SERVICE_NAME}.service}
BACKUP_DIR=${BACKUP_DIR:-/etc/xray/backups}
AUTO_ENABLE=${AUTO_ENABLE:-1}
AUTO_START=${AUTO_START:-1}
RUN_PREFLIGHT=${RUN_PREFLIGHT:-1}
PREFLIGHT_STATIC_ONLY=${PREFLIGHT_STATIC_ONLY:-0}
PREFLIGHT_PYTHON=${PREFLIGHT_PYTHON:-python3}
PREFLIGHT_SCRIPT=${PREFLIGHT_SCRIPT:-$PROJECT_DIR/scripts/preflight_check.py}
PREFLIGHT_RENDER=${PREFLIGHT_RENDER:-$PROJECT_DIR/scripts/render_preflight_summary.py}
APPLY_NETWORK_PLAN=${APPLY_NETWORK_PLAN:-1}
NETWORK_PLAN_SCRIPT=${NETWORK_PLAN_SCRIPT:-$PROJECT_DIR/scripts/apply_network_plan.py}
RESOURCE_PLAN_SOURCE=${RESOURCE_PLAN_SOURCE:-$OUTPUT_DIR/resource-plan.json}

require_root() {
  if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
    echo "Please run as root (or with sudo)." >&2
    exit 1
  fi
}

require_file() {
  local path=$1
  if [[ ! -f "$path" ]]; then
    echo "Required file not found: $path" >&2
    exit 1
  fi
}

backup_file_if_exists() {
  local src=$1
  if [[ -f "$src" ]]; then
    mkdir -p "$BACKUP_DIR"
    local ts
    ts=$(date +%Y%m%d-%H%M%S)
    cp "$src" "$BACKUP_DIR/$(basename "$src").$ts.bak"
    echo "Backed up $src -> $BACKUP_DIR/$(basename "$src").$ts.bak"
  fi
}

install_xray_if_missing() {
  if [[ -x "$XRAY_BIN" ]]; then
    echo "Found xray binary: $XRAY_BIN"
    return 0
  fi

  echo "xray not found at $XRAY_BIN"
  echo "Please install xray manually first, then rerun this installer."
  echo "Recommended target binary path: /usr/local/bin/xray"
  exit 2
}

rewrite_service_execstart() {
  local source_service=$1
  local temp_service=$2
  sed "s#ExecStart=/usr/local/bin/xray run -c /etc/xray/config.json#ExecStart=${XRAY_BIN} run -c ${XRAY_CONFIG_TARGET}#g" "$source_service" > "$temp_service"
}

run_preflight() {
  if [[ "$RUN_PREFLIGHT" != "1" ]]; then
    echo "RUN_PREFLIGHT=0 -> skip preflight"
    return 0
  fi

  if [[ ! -f "$PREFLIGHT_SCRIPT" ]]; then
    echo "Preflight script not found: $PREFLIGHT_SCRIPT" >&2
    echo "Set RUN_PREFLIGHT=0 to bypass, or fix PREFLIGHT_SCRIPT." >&2
    exit 3
  fi

  local cmd=(
    "$PREFLIGHT_PYTHON" "$PREFLIGHT_SCRIPT"
    --generated-dir "$OUTPUT_DIR"
    --service-name "$SERVICE_NAME"
    --xray-bin "$XRAY_BIN"
    --config-target "$XRAY_CONFIG_TARGET"
    --service-target "$XRAY_SERVICE_TARGET"
  )

  if [[ "$PREFLIGHT_STATIC_ONLY" == "1" ]]; then
    cmd+=(--static-only)
  fi

  local result_file
  result_file=$(mktemp)

  echo "Running preflight check..."
  if ! "${cmd[@]}" > "$result_file"; then
    cat "$result_file"
    if [[ -f "$PREFLIGHT_RENDER" ]]; then
      "$PREFLIGHT_PYTHON" "$PREFLIGHT_RENDER" "$result_file" || true
    fi
    rm -f "$result_file"
    echo "Preflight failed. Refusing to continue installation." >&2
    exit 4
  fi

  cat "$result_file"
  if [[ -f "$PREFLIGHT_RENDER" ]]; then
    "$PREFLIGHT_PYTHON" "$PREFLIGHT_RENDER" "$result_file" || true
  fi
  rm -f "$result_file"
}

apply_network_plan_if_enabled() {
  if [[ "$APPLY_NETWORK_PLAN" != "1" ]]; then
    echo "APPLY_NETWORK_PLAN=0 -> skip runtime network plan"
    return 0
  fi

  if [[ ! -f "$NETWORK_PLAN_SCRIPT" ]]; then
    echo "Network plan script not found: $NETWORK_PLAN_SCRIPT" >&2
    return 0
  fi

  if [[ ! -f "$RESOURCE_PLAN_SOURCE" ]]; then
    echo "resource-plan.json not found: $RESOURCE_PLAN_SOURCE"
    return 0
  fi

  echo "Applying runtime network plan..."
  "$PREFLIGHT_PYTHON" "$NETWORK_PLAN_SCRIPT" --resource-plan "$RESOURCE_PLAN_SOURCE" || true
}

main() {
  require_root

  local source_config="$OUTPUT_DIR/xray-config.json"
  local source_service="$OUTPUT_DIR/xray.service"
  local temp_service
  temp_service=$(mktemp)

  require_file "$source_config"
  require_file "$source_service"
  install_xray_if_missing
  run_preflight
  apply_network_plan_if_enabled

  mkdir -p /etc/xray

  backup_file_if_exists "$XRAY_CONFIG_TARGET"
  backup_file_if_exists "$XRAY_SERVICE_TARGET"

  cp "$source_config" "$XRAY_CONFIG_TARGET"
  rewrite_service_execstart "$source_service" "$temp_service"
  cp "$temp_service" "$XRAY_SERVICE_TARGET"
  rm -f "$temp_service"

  chmod 0644 "$XRAY_CONFIG_TARGET" "$XRAY_SERVICE_TARGET"

  systemctl daemon-reload

  if [[ "$AUTO_ENABLE" == "1" ]]; then
    systemctl enable "$SERVICE_NAME"
  else
    echo "AUTO_ENABLE=0 -> skip enable ${SERVICE_NAME}"
  fi

  if [[ "$AUTO_START" == "1" ]]; then
    systemctl restart "$SERVICE_NAME"
    systemctl --no-pager --full status "$SERVICE_NAME" || true
  else
    echo "AUTO_START=0 -> skip restart ${SERVICE_NAME}"
  fi

  echo
  echo "[INSTALL:OK]"
  echo "Service name: $SERVICE_NAME"
  echo "Config: $XRAY_CONFIG_TARGET"
  echo "Service: $XRAY_SERVICE_TARGET"
  echo "Proxy list: $OUTPUT_DIR/proxies.txt"
  echo "[OK] install_complete"
}

main "$@"

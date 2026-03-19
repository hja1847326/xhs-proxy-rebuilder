#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
PREFIX=${PREFIX:-/usr/local}
LIB_DIR=${LIB_DIR:-$PREFIX/lib/xhs-proxy}
BIN_DIR=${BIN_DIR:-$PREFIX/bin}
BIN_NAME=${BIN_NAME:-xhs-proxy}
TARGET_BIN="$BIN_DIR/$BIN_NAME"
TARGET_LIB="$LIB_DIR"

require_root_if_needed() {
  if [[ ! -w "$BIN_DIR" || ! -w "$(dirname "$TARGET_LIB")" ]]; then
    if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
      echo "Need root privileges to install into $PREFIX" >&2
      echo "Run with sudo, or override PREFIX to a writable location." >&2
      exit 1
    fi
  fi
}

main() {
  require_root_if_needed

  mkdir -p "$BIN_DIR"
  mkdir -p "$TARGET_LIB/scripts"
  mkdir -p "$TARGET_LIB/profiles"

  cp "$PROJECT_DIR/xhs-proxy" "$TARGET_LIB/xhs-proxy"
  cp "$PROJECT_DIR/scripts/xhs_proxy_cli.py" "$TARGET_LIB/scripts/xhs_proxy_cli.py"
  cp "$PROJECT_DIR/scripts/build.py" "$TARGET_LIB/scripts/build.py"
  cp "$PROJECT_DIR/scripts/release.py" "$TARGET_LIB/scripts/release.py"
  cp "$PROJECT_DIR/scripts/install.sh" "$TARGET_LIB/scripts/install.sh"
  cp "$PROJECT_DIR/scripts/preflight_check.py" "$TARGET_LIB/scripts/preflight_check.py"
  cp "$PROJECT_DIR/scripts/render_preflight_summary.py" "$TARGET_LIB/scripts/render_preflight_summary.py"
  cp "$PROJECT_DIR/scripts/smoke_tests.py" "$TARGET_LIB/scripts/smoke_tests.py"
  cp "$PROJECT_DIR/scripts/convert_ip_origin.py" "$TARGET_LIB/scripts/convert_ip_origin.py"
  cp "$PROJECT_DIR/scripts/lint_inventory.py" "$TARGET_LIB/scripts/lint_inventory.py"
  cp "$PROJECT_DIR/scripts/generate.py" "$TARGET_LIB/scripts/generate.py"
  cp "$PROJECT_DIR/scripts/package_release.py" "$TARGET_LIB/scripts/package_release.py"
  cp "$PROJECT_DIR/scripts/remote_preflight.sh" "$TARGET_LIB/scripts/remote_preflight.sh"
  cp "$PROJECT_DIR/scripts/test_proxies.py" "$TARGET_LIB/scripts/test_proxies.py"
  cp "$PROJECT_DIR/scripts/apply_network_plan.py" "$TARGET_LIB/scripts/apply_network_plan.py"
  cp "$PROJECT_DIR/scripts/apply_netns_expansion.py" "$TARGET_LIB/scripts/apply_netns_expansion.py"
  cp "$PROJECT_DIR/scripts/validate_netns_expansion.py" "$TARGET_LIB/scripts/validate_netns_expansion.py"

  cp "$PROJECT_DIR/profiles/"*.yaml "$TARGET_LIB/profiles/"

  chmod +x "$TARGET_LIB/xhs-proxy"
  chmod +x "$TARGET_LIB/scripts/xhs_proxy_cli.py"
  chmod +x "$TARGET_LIB/scripts/install.sh"
  chmod +x "$TARGET_LIB/scripts/remote_preflight.sh"

  cat > "$TARGET_BIN" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "$TARGET_LIB/xhs-proxy" "\$@"
EOF
  chmod +x "$TARGET_BIN"

  echo "[BOOTSTRAP:OK]"
  echo "installed_bin=$TARGET_BIN"
  echo "installed_lib=$TARGET_LIB"
  echo "test_cmd=$TARGET_BIN --help"
  echo "[OK] bootstrap_install_complete"
}

main "$@"

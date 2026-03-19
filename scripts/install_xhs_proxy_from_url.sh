#!/usr/bin/env bash
set -euo pipefail

CLI_URL=${1:-${XHS_PROXY_CLI_URL:-}}
PREFIX=${PREFIX:-/usr/local}
WORKDIR=${WORKDIR:-/tmp/xhs-proxy-curl-install}
ARCHIVE_NAME=${ARCHIVE_NAME:-xhs-proxy-cli.tar.gz}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

main() {
  need_cmd curl
  need_cmd tar
  need_cmd bash
  need_cmd python3

  if [[ -z "$CLI_URL" ]]; then
    echo "Usage: $0 <xhs-proxy-cli.tar.gz URL>" >&2
    echo "Or set XHS_PROXY_CLI_URL=https://.../xhs-proxy-cli.tar.gz" >&2
    exit 2
  fi

  rm -rf "$WORKDIR"
  mkdir -p "$WORKDIR"

  local archive="$WORKDIR/$ARCHIVE_NAME"
  echo "[INSTALL-URL:FETCH] $CLI_URL"
  curl -fsSL "$CLI_URL" -o "$archive"

  echo "[INSTALL-URL:EXTRACT] $archive"
  tar -xzf "$archive" -C "$WORKDIR"

  local root="$WORKDIR/xhs-proxy-cli"
  if [[ ! -d "$root" ]]; then
    echo "Invalid archive structure: missing xhs-proxy-cli/" >&2
    exit 3
  fi

  echo "[INSTALL-URL:BOOTSTRAP]"
  cd "$root"
  PREFIX="$PREFIX" bash scripts/bootstrap_install.sh

  echo "[OK] install_from_url_complete"
  echo "prefix=$PREFIX"
  echo "hint=xhs-proxy --help"
}

main "$@"

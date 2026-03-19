#!/usr/bin/env bash
set -euo pipefail

SRC=${1:-}
PREFIX=${PREFIX:-/usr/local}
WORKDIR=${WORKDIR:-/tmp/xhs-proxy-install}
ARCHIVE_NAME=${ARCHIVE_NAME:-xhs-proxy-cli.tar.gz}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

fetch_archive() {
  local src=$1
  local archive=$2

  if [[ -z "$src" ]]; then
    echo "Usage: $0 <tar.gz path or URL>" >&2
    exit 2
  fi

  if [[ "$src" =~ ^https?:// ]]; then
    need_cmd curl
    curl -fsSL "$src" -o "$archive"
  else
    cp "$src" "$archive"
  fi
}

main() {
  need_cmd tar
  need_cmd bash
  need_cmd python3

  rm -rf "$WORKDIR"
  mkdir -p "$WORKDIR"

  local archive="$WORKDIR/$ARCHIVE_NAME"
  fetch_archive "$SRC" "$archive"

  tar -xzf "$archive" -C "$WORKDIR"

  local root="$WORKDIR/xhs-proxy-cli"
  if [[ ! -d "$root" ]]; then
    echo "Invalid archive structure: missing xhs-proxy-cli/" >&2
    exit 3
  fi

  cd "$root"
  PREFIX="$PREFIX" bash scripts/bootstrap_install.sh

  echo "[OK] remote_install_complete"
  echo "prefix=$PREFIX"
  echo "hint=xhs-proxy --help"
}

main "$@"

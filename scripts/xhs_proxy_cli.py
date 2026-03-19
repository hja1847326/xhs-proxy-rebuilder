#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"

COMMAND_MAP = {
    "build": SCRIPTS_DIR / "build.py",
    "release": SCRIPTS_DIR / "release.py",
    "install": SCRIPTS_DIR / "install.sh",
    "preflight": SCRIPTS_DIR / "preflight_check.py",
    "smoke-test": SCRIPTS_DIR / "smoke_tests.py",
    "validate-netns": SCRIPTS_DIR / "validate_netns_expansion.py",
    "healthcheck-install": SCRIPTS_DIR / "healthcheck_install.py",
    "post-install-verify": SCRIPTS_DIR / "post_install_verify.py",
    "bootstrap-install": SCRIPTS_DIR / "bootstrap_install.sh",
    "package-cli": SCRIPTS_DIR / "package_cli_bundle.py",
    "remote-install": SCRIPTS_DIR / "install_xhs_proxy_remote.sh",
    "install-from-url": SCRIPTS_DIR / "install_xhs_proxy_from_url.sh",
}


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="xhs-proxy",
        description="xhs-proxy CLI V1 - unified entry for xhs-proxy-rebuilder",
    )
    parser.add_argument("command", nargs="?", choices=sorted(COMMAND_MAP.keys()), help="Subcommand to run")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed through to the subcommand")
    parsed = parser.parse_args()

    if not parsed.command:
        parser.print_help()
        print("\nAvailable subcommands:")
        for name in sorted(COMMAND_MAP):
            print(f"  - {name}")
        return 0

    target = COMMAND_MAP[parsed.command]
    passthrough = parsed.args
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    if target.suffix == ".sh":
        cmd = ["bash", str(target), *passthrough]
    else:
        cmd = [sys.executable, str(target), *passthrough]

    print(f"[CLI] command={parsed.command}")
    print(f"[CLI] target={target}")
    return run(cmd)


if __name__ == "__main__":
    raise SystemExit(main())

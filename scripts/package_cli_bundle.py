#!/usr/bin/env python3
import argparse
import shutil
import tarfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

FILES = [
    "xhs-proxy",
    "scripts/xhs_proxy_cli.py",
    "scripts/bootstrap_install.sh",
    "scripts/build.py",
    "scripts/release.py",
    "scripts/install.sh",
    "scripts/preflight_check.py",
    "scripts/render_preflight_summary.py",
    "scripts/smoke_tests.py",
    "scripts/convert_ip_origin.py",
    "scripts/lint_inventory.py",
    "scripts/generate.py",
    "scripts/package_release.py",
    "scripts/remote_preflight.sh",
    "scripts/test_proxies.py",
    "scripts/apply_network_plan.py",
    "scripts/apply_netns_expansion.py",
]


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Package xhs-proxy CLI into a distributable tar.gz")
    parser.add_argument("--output", default="dist/xhs-proxy-cli.tar.gz", help="Output tar.gz path")
    args = parser.parse_args()

    output = resolve(args.output)
    staging = output.parent / (output.stem.replace(".tar", "") + "-staging")
    root = staging / "xhs-proxy-cli"

    if staging.exists():
        shutil.rmtree(staging)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "profiles").mkdir(parents=True, exist_ok=True)

    for rel in FILES:
        src = BASE_DIR / rel
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    for src in (BASE_DIR / "profiles").glob("*.yaml"):
        shutil.copy2(src, root / "profiles" / src.name)

    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as tar:
        tar.add(root, arcname="xhs-proxy-cli")

    print(f"[OK] cli_bundle_created={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

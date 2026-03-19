#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()


def stage(title: str) -> None:
    print(f"\n[RELEASE:{title}]")


def run(cmd: list, label: str | None = None) -> None:
    printable = [str(x) for x in cmd]
    if label:
        print(f"[RUN:{label}] {' '.join(printable)}")
    else:
        print("[RUN]", " ".join(printable))
    subprocess.run(printable, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="One-shot release entry: build + package for xhs-proxy-rebuilder"
    )
    parser.add_argument("--profile", default="profiles/huaweicloud-default.yaml", help="Profile YAML path")
    parser.add_argument("--inventory", help="Use an existing inventory YAML directly")
    parser.add_argument("--ip-origin", help="Convert ip_origin.txt first, then build")
    parser.add_argument("--output-dir", help="Generated output directory")
    parser.add_argument("--inventory-output", help="Converted inventory output path when using --ip-origin")
    parser.add_argument("--bundle-dir", default="dist/release-bundle", help="Bundle output directory")
    parser.add_argument("--primary-ip", help="Override primary IP")
    parser.add_argument("--vip", action="append", dest="vip_ips", default=None, help="VIP bind IP (repeatable)")
    parser.add_argument("--start-port", type=int, help="Override starting proxy port")
    parser.add_argument("--default-password", help="Override fallback default password")
    args = parser.parse_args()

    profile_path = resolve(args.profile)
    bundle_dir = resolve(args.bundle_dir)

    print("[RELEASE:START]")
    print(f"profile={profile_path}")
    print(f"bundle_dir={bundle_dir}")

    build_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "build.py"),
        "--profile",
        str(profile_path),
    ]

    if args.inventory:
        build_cmd.extend(["--inventory", str(resolve(args.inventory))])
    if args.ip_origin:
        build_cmd.extend(["--ip-origin", str(resolve(args.ip_origin))])
    if args.output_dir:
        build_cmd.extend(["--output-dir", args.output_dir])
    if args.inventory_output:
        build_cmd.extend(["--inventory-output", args.inventory_output])
    if args.primary_ip:
        build_cmd.extend(["--primary-ip", args.primary_ip])
    if args.start_port is not None:
        build_cmd.extend(["--start-port", str(args.start_port)])
    if args.default_password:
        build_cmd.extend(["--default-password", args.default_password])
    if args.vip_ips:
        for vip in args.vip_ips:
            build_cmd.extend(["--vip", vip])

    stage("BUILD")
    run(build_cmd, "build")

    generated_dir = resolve(args.output_dir) if args.output_dir else None
    inventory_path = resolve(args.inventory_output) if args.inventory_output else None

    if generated_dir is None:
        import yaml
        profile_data = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        defaults = profile_data.get("defaults", {}) if isinstance(profile_data, dict) else {}
        generated_dir = resolve(defaults.get("output_dir", "generated-build"))
        if args.inventory:
            inventory_path = resolve(args.inventory)
        elif inventory_path is None:
            inventory_path = resolve(defaults.get("inventory_output", "inventory/generated-from-profile.yaml"))
    else:
        if args.inventory:
            inventory_path = resolve(args.inventory)
        elif inventory_path is None:
            import yaml
            profile_data = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
            defaults = profile_data.get("defaults", {}) if isinstance(profile_data, dict) else {}
            inventory_path = resolve(defaults.get("inventory_output", "inventory/generated-from-profile.yaml"))

    package_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "package_release.py"),
        "--generated-dir",
        str(generated_dir),
        "--bundle-dir",
        str(bundle_dir),
        "--profile",
        str(profile_path),
        "--inventory",
        str(inventory_path),
        "--quiet",
    ]

    stage("PACKAGE")
    run(package_cmd, "package")

    stage("OK")
    print(f"profile={profile_path}")
    print(f"inventory={inventory_path}")
    print(f"generated_dir={generated_dir}")
    print(f"bundle_dir={bundle_dir}")
    print("[OK] release_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

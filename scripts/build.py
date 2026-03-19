#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml\nInstall with: python3 -m pip install pyyaml", file=sys.stderr)
    raise

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"


def stage(title: str) -> None:
    print(f"\n[BUILD:{title}]")


def run(cmd: list, label: str | None = None) -> None:
    printable = [str(x) for x in cmd]
    if label:
        print(f"[RUN:{label}] {' '.join(printable)}")
    else:
        print("[RUN]", " ".join(printable))
    subprocess.run(printable, check=True)


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()


def infer_output_name(ip_origin_path: Path) -> str:
    stem = ip_origin_path.stem.replace(" ", "-")
    return f"inventory/{stem}.generated.yaml"


def load_profile(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid profile format: {path}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified build entry for HuaweiCloud multi-SOCKS5 generator"
    )
    parser.add_argument("--profile", default="profiles/huaweicloud-default.yaml", help="Profile YAML path")
    parser.add_argument("--inventory", help="Use an existing inventory YAML directly")
    parser.add_argument("--ip-origin", help="Convert ip_origin.txt first, then lint and generate")
    parser.add_argument("--output-dir", help="Directory for generated files")
    parser.add_argument("--inventory-output", help="Output path for converted inventory when using --ip-origin")
    parser.add_argument("--primary-ip", help="Primary bind IP used by convert_ip_origin.py")
    parser.add_argument("--vip", action="append", dest="vip_ips", default=None, help="VIP bind IP (repeatable)")
    parser.add_argument("--start-port", type=int, help="Starting proxy port")
    parser.add_argument("--default-password", help="Default password for generated proxies")
    args = parser.parse_args()

    profile_path = resolve(args.profile)
    profile = load_profile(profile_path)
    defaults = profile.get("defaults", {})

    output_dir = args.output_dir or defaults.get("output_dir", "generated-build")
    primary_ip = args.primary_ip or defaults.get("primary_ip", "192.168.0.10")
    start_port = args.start_port or defaults.get("start_port", 19001)
    default_password = args.default_password or defaults.get("default_password", "123456")
    vip_ips = args.vip_ips or defaults.get("vip_ips", ["192.168.0.11", "192.168.0.12"])
    secondary_nic_ips = defaults.get("secondary_nic_ips", [])
    default_inventory_output = defaults.get("inventory_output")

    if not args.inventory and not args.ip_origin:
        print("[BUILD:ERROR] Must provide either --inventory or --ip-origin", file=sys.stderr)
        return 2
    if args.inventory and args.ip_origin:
        print("[BUILD:ERROR] Use either --inventory or --ip-origin, not both", file=sys.stderr)
        return 2

    print("[BUILD:START]")
    print(f"profile={profile_path}")

    inventory_path: Path

    if args.ip_origin:
        stage("CONVERT")
        ip_origin_path = resolve(args.ip_origin)
        inventory_output = resolve(args.inventory_output) if args.inventory_output else resolve(default_inventory_output or infer_output_name(ip_origin_path))

        convert_cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "convert_ip_origin.py"),
            str(ip_origin_path),
            "--primary-ip",
            primary_ip,
            "--start-port",
            str(start_port),
            "--default-password",
            default_password,
            "--strategy-file",
            str(profile_path),
            "--output",
            str(inventory_output),
        ]
        for vip in vip_ips:
            convert_cmd.extend(["--vip", vip])
        for ip in secondary_nic_ips:
            convert_cmd.extend(["--secondary-nic", ip])
        convert_cmd.append("--quiet")
        run(convert_cmd, "convert")
        inventory_path = inventory_output
    else:
        inventory_path = resolve(args.inventory)
        stage("INPUT")
        print(f"inventory={inventory_path}")

    stage("LINT")
    run([
        sys.executable,
        str(SCRIPTS_DIR / "lint_inventory.py"),
        str(inventory_path),
        "--profile",
        str(profile_path),
        "--quiet",
    ], "lint")

    stage("GENERATE")
    run([
        sys.executable,
        str(SCRIPTS_DIR / "generate.py"),
        str(inventory_path),
        "--output-dir",
        output_dir,
        "--profile",
        str(profile_path),
        "--quiet",
    ], "generate")

    stage("OK")
    print(f"profile={profile_path}")
    print(f"inventory={inventory_path}")
    print(f"generated_dir={resolve(output_dir)}")
    print("[OK] build_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

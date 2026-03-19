#!/usr/bin/env python3
import argparse
import ipaddress
import random
import re
import string
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml\nInstall with: python3 -m pip install pyyaml", file=sys.stderr)
    raise


MAC_RE = re.compile(r"^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


def parse_row(parts: list[str], lineno: int) -> dict:
    if len(parts) != 3:
        raise ValueError(f"Line {lineno}: expected 3 columns, got {len(parts)}")

    ip_str = parts[0]
    try:
        ipaddress.ip_address(ip_str)
    except ValueError as exc:
        raise ValueError(f"Line {lineno}: invalid IP '{ip_str}'") from exc

    second, third = parts[1], parts[2]

    if MAC_RE.match(second) and third.isdigit():
        return {"ip": ip_str, "mac": second.lower(), "vlan": int(third), "source_format": "ip-mac-vlan"}

    if second.isdigit() and MAC_RE.match(third):
        return {"ip": ip_str, "mac": third.lower(), "vlan": int(second), "source_format": "ip-vlan-mac"}

    raise ValueError(
        f"Line {lineno}: unsupported format. Expected either 'IP MAC VLAN' or 'IP VLAN MAC', got: {' '.join(parts)}"
    )


def parse_ip_origin(path: Path) -> list[dict]:
    rows = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        rows.append(parse_row(parts, lineno))
    if not rows:
        raise ValueError("ip_origin.txt contains no usable rows")
    return rows


def build_username(index: int, strategy: dict) -> str:
    mode = (strategy or {}).get("mode", "prefix_counter")
    if mode == "prefix_counter":
        prefix = (strategy or {}).get("prefix", "vip")
        start = int((strategy or {}).get("start", 1))
        return f"{prefix}{start + index - 1}"
    raise ValueError(f"Unsupported username strategy mode: {mode}")


def build_password(index: int, strategy: dict, fallback: str) -> str:
    mode = (strategy or {}).get("mode", "fixed")
    if mode == "fixed":
        return str((strategy or {}).get("value", fallback))
    if mode == "random":
        length = int((strategy or {}).get("length", 12))
        alphabet = (strategy or {}).get("alphabet") or (string.ascii_letters + string.digits)
        rng = random.SystemRandom()
        return "".join(rng.choice(alphabet) for _ in range(length))
    raise ValueError(f"Unsupported password strategy mode: {mode}")


def build_port(index: int, strategy: dict, fallback_start: int) -> int:
    mode = (strategy or {}).get("mode", "incremental")
    if mode == "incremental":
        start = int((strategy or {}).get("start", fallback_start))
        return start + index - 1
    raise ValueError(f"Unsupported port strategy mode: {mode}")


def build_inventory(
    rows: list[dict],
    primary_ip: str,
    vip_ips: list[str],
    secondary_nic_ips: list[str],
    start_port: int,
    default_password: str,
    strategy: dict | None = None,
) -> dict:
    egresses = []
    proxies = []
    strategy = strategy or {}

    egresses.append(
        {
            "id": "main",
            "bind_ip": primary_ip,
            "expected_public_ip": "",
            "kind": "primary",
            "note": "主IP出口",
        }
    )

    for i, vip in enumerate(vip_ips, start=1):
        egresses.append(
            {
                "id": f"vip{i}",
                "bind_ip": vip,
                "expected_public_ip": "",
                "kind": "vip",
                "note": f"虚拟IP {i}",
            }
        )

    for i, ip in enumerate(secondary_nic_ips, start=1):
        egresses.append(
            {
                "id": f"fixed-nic{i}",
                "bind_ip": ip,
                "expected_public_ip": "",
                "kind": "secondary_nic_fixed",
                "note": f"固定辅助弹性网卡 {i}",
            }
        )

    for i, row in enumerate(rows, start=1):
        egresses.append(
            {
                "id": f"nic{i}",
                "bind_ip": row["ip"],
                "expected_public_ip": "",
                "kind": "secondary_nic",
                "note": f"辅助弹性网卡 {i} mac={row['mac']} vlan={row['vlan']}",
                "source_mac": row["mac"],
                "source_vlan": row["vlan"],
                "source_format": row.get("source_format", ""),
            }
        )

    ordered_resource_ids = (
        ["main"]
        + [f"vip{i}" for i in range(1, len(vip_ips) + 1)]
        + [f"fixed-nic{i}" for i in range(1, len(secondary_nic_ips) + 1)]
        + [f"nic{i}" for i in range(1, len(rows) + 1)]
    )

    for idx, rid in enumerate(ordered_resource_ids, start=1):
        bind_ip = next(item["bind_ip"] for item in egresses if item["id"] == rid)
        username = build_username(idx, strategy.get("username", {}))
        password = build_password(idx, strategy.get("password", {}), default_password)
        port = build_port(idx, strategy.get("port", {}), start_port)
        proxies.append(
            {
                "name": f"proxy{idx:02d}",
                "resource_id": rid,
                "listen_ip": bind_ip,
                "port": port,
                "username": username,
                "password": password,
                "account_label": username,
            }
        )

    return {
        "server": {
            "provider": "huaweicloud",
            "region": "",
            "hostname": "",
            "os": "",
        },
        "resources": {
            "egresses": egresses,
        },
        "proxies": proxies,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert ip_origin.txt into V2 HuaweiCloud inventory")
    parser.add_argument("ip_origin", help="Path to ip_origin.txt")
    parser.add_argument("--primary-ip", default="192.168.0.10", help="Primary bind IP")
    parser.add_argument("--vip", action="append", dest="vip_ips", default=None, help="VIP bind IP (can repeat)")
    parser.add_argument("--secondary-nic", action="append", dest="secondary_nic_ips", default=None, help="Fixed secondary NIC bind IP (can repeat)")
    parser.add_argument("--start-port", type=int, default=19001, help="Starting proxy port")
    parser.add_argument("--default-password", default="123456", help="Default password assigned to generated proxies")
    parser.add_argument("--strategy-file", help="Optional YAML file containing strategy.username/password/port")
    parser.add_argument("--output", default="inventory/generated-from-ip-origin.yaml", help="Output inventory path")
    parser.add_argument("--quiet", action="store_true", help="Suppress normal summary output")
    args = parser.parse_args()

    ip_origin_path = Path(args.ip_origin).resolve()
    output_path = Path(args.output).resolve() if Path(args.output).is_absolute() else (Path(__file__).resolve().parents[1] / args.output).resolve()

    vip_ips = args.vip_ips or ["192.168.0.11", "192.168.0.12"]
    secondary_nic_ips = args.secondary_nic_ips or []
    strategy = {}
    if args.strategy_file:
        strategy_path = Path(args.strategy_file).resolve()
        data = yaml.safe_load(strategy_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            strategy = data.get("strategy", data)
            defaults = data.get("defaults", {}) if isinstance(data.get("defaults"), dict) else {}
            if not args.secondary_nic_ips:
                profile_secondary = defaults.get("secondary_nic_ips")
                if isinstance(profile_secondary, list):
                    secondary_nic_ips = [str(x) for x in profile_secondary]

    rows = parse_ip_origin(ip_origin_path)
    inventory = build_inventory(rows, args.primary_ip, vip_ips, secondary_nic_ips, args.start_port, args.default_password, strategy)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(inventory, allow_unicode=True, sort_keys=False), encoding="utf-8")

    if not args.quiet:
        formats = sorted({row.get("source_format", "unknown") for row in rows})
        print(f"Parsed rows: {len(rows)}")
        print(f"Detected formats: {', '.join(formats)}")
        print(f"Generated inventory: {output_path}")
        print(f"Generated proxies: {len(inventory['proxies'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

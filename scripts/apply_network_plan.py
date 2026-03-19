#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

IP_LINE_RE = re.compile(r"^\s+inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+).*")
LINK_LINE_RE = re.compile(r"^\d+:\s+([^:@]+).*")
LINK_MAC_RE = re.compile(r"^\s+link/\S+\s+([0-9a-f:]{17}).*")


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )


def load_plan(path: Path) -> List[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("resource-plan.json must be a list")
    return data


def get_ipv4_map() -> Dict[str, str]:
    out = run(["ip", "-4", "addr", "show"]).stdout
    ip_to_dev = {}  # type: Dict[str, str]
    current_dev = None
    for line in out.splitlines():
        m = LINK_LINE_RE.match(line)
        if m:
            current_dev = m.group(1)
            continue
        m = IP_LINE_RE.match(line)
        if m and current_dev:
            ip_to_dev[m.group(1)] = current_dev
    return ip_to_dev


def get_mac_map() -> Dict[str, str]:
    out = run(["ip", "link", "show"]).stdout
    mac_to_dev = {}  # type: Dict[str, str]
    current_dev = None
    for line in out.splitlines():
        m = LINK_LINE_RE.match(line)
        if m:
            current_dev = m.group(1)
            continue
        m = LINK_MAC_RE.match(line)
        if m and current_dev:
            mac = m.group(1).lower()
            if mac != "00:00:00:00:00:00":
                mac_to_dev[mac] = current_dev
    return mac_to_dev


def ensure_ip_on_dev(ip: str, dev: str, prefix: str = "24") -> Tuple[bool, str]:
    current = get_ipv4_map()
    if ip in current:
        return False, current[ip]
    run(["ip", "addr", "add", "%s/%s" % (ip, prefix), "dev", dev], check=True)
    return True, dev


def ensure_rule(src_ip: str, table: str) -> bool:
    out = run(["ip", "rule", "show"]).stdout
    needle = "from %s lookup %s" % (src_ip, table)
    if needle in out:
        return False
    run(["ip", "rule", "add", "from", src_ip, "table", table], check=True)
    return True


def ensure_default_route(dev: str, gateway: str, table: str) -> bool:
    out = run(["ip", "route", "show", "table", table], check=False).stdout
    needle = "default via %s dev %s" % (gateway, dev)
    if needle in out:
        return False
    run(["ip", "route", "replace", "default", "via", gateway, "dev", dev, "table", table], check=True)
    return True


def set_sysctl(path: str, value: str) -> bool:
    cur = Path(path).read_text(encoding="utf-8").strip()
    if cur == value:
        return False
    Path(path).write_text(value + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply runtime network plan for 4+N HuaweiCloud layout")
    parser.add_argument("--resource-plan", required=True, help="Path to resource-plan.json")
    parser.add_argument("--primary-dev", default="eth0")
    parser.add_argument("--secondary-dev", default="eth1")
    parser.add_argument("--secondary-gateway", default="192.168.0.1")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("must run as root", file=sys.stderr)
        return 2

    plan = load_plan(Path(args.resource_plan))
    current = get_ipv4_map()
    mac_map = get_mac_map()
    actions = []  # type: List[str]

    for item in plan:
        bind_ip = item.get("bind_ip")
        kind = item.get("kind", "")
        if not bind_ip:
            continue
        if bind_ip in current:
            continue
        target_dev = None
        if kind == "vip":
            target_dev = args.primary_dev
        elif kind == "secondary_nic_fixed":
            target_dev = args.secondary_dev
        elif kind == "secondary_nic":
            source_mac = str(item.get("source_mac", "")).lower()
            target_dev = mac_map.get(source_mac)
            if not target_dev:
                actions.append("manual_needed secondary_nic bind_ip=%s mac=%s note=%s" % (bind_ip, source_mac, item.get("note", "")))
                continue
        if target_dev:
            if args.dry_run:
                actions.append("would_add_ip %s/24 dev=%s" % (bind_ip, target_dev))
            else:
                changed, dev = ensure_ip_on_dev(bind_ip, target_dev)
                if changed:
                    actions.append("added_ip %s/24 dev=%s" % (bind_ip, dev))

    secondary_ip = None
    for item in plan:
        if item.get("kind") == "secondary_nic_fixed":
            secondary_ip = item.get("bind_ip")
            break

    if secondary_ip:
        if args.dry_run:
            actions.append("would_set_rpfilter loose for %s" % args.secondary_dev)
            actions.append("would_add_rule from %s table 100" % secondary_ip)
            actions.append("would_add_default_route via %s dev %s table 100" % (args.secondary_gateway, args.secondary_dev))
        else:
            if set_sysctl("/proc/sys/net/ipv4/conf/all/rp_filter", "2"):
                actions.append("set rp_filter all=2")
            if set_sysctl("/proc/sys/net/ipv4/conf/%s/rp_filter" % args.secondary_dev, "2"):
                actions.append("set rp_filter %s=2" % args.secondary_dev)
            if ensure_rule(secondary_ip, "100"):
                actions.append("added rule from %s table 100" % secondary_ip)
            if ensure_default_route(args.secondary_dev, args.secondary_gateway, "100"):
                actions.append("added default route table 100 via %s dev %s" % (args.secondary_gateway, args.secondary_dev))

    print(json.dumps({"actions": actions}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

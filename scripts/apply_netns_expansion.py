#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_netns(name: str, actions: list[str]) -> None:
    out = run(["ip", "netns", "list"], check=False).stdout
    if any(line.split()[0] == name for line in out.splitlines() if line.strip()):
        return
    run(["ip", "netns", "add", name])
    actions.append(f"created_netns {name}")


def link_exists(dev: str) -> bool:
    return run(["ip", "link", "show", "dev", dev], check=False).returncode == 0


def netns_link_exists(netns: str, dev: str) -> bool:
    return run(["ip", "netns", "exec", netns, "ip", "link", "show", "dev", dev], check=False).returncode == 0


def ensure_vlan_link(parent: str, vlan_link: str, vlan_id: int, actions: list[str]) -> None:
    if link_exists(vlan_link):
        return
    run(["ip", "link", "add", "link", parent, "name", vlan_link, "type", "vlan", "id", str(vlan_id)])
    actions.append(f"created_vlan {vlan_link} id={vlan_id} parent={parent}")


def move_link_to_netns(vlan_link: str, netns: str, actions: list[str]) -> None:
    if netns_link_exists(netns, vlan_link):
        return
    run(["ip", "link", "set", vlan_link, "netns", netns])
    actions.append(f"moved_link {vlan_link} -> {netns}")


def ensure_loopback_up(netns: str, actions: list[str]) -> None:
    run(["ip", "netns", "exec", netns, "ip", "link", "set", "lo", "up"])
    actions.append(f"loopback_up {netns}")


def ensure_ip(netns: str, dev: str, bind_ip: str, prefix: int, actions: list[str]) -> None:
    out = run(["ip", "netns", "exec", netns, "ip", "-4", "addr", "show", "dev", dev], check=False).stdout
    needle = f"inet {bind_ip}/{prefix}"
    if needle in out:
        return
    run(["ip", "netns", "exec", netns, "ip", "addr", "add", f"{bind_ip}/{prefix}", "dev", dev])
    actions.append(f"assigned_ip {bind_ip}/{prefix} dev={dev} netns={netns}")


def ensure_link_up(netns: str, dev: str, actions: list[str]) -> None:
    run(["ip", "netns", "exec", netns, "ip", "link", "set", dev, "up"])
    actions.append(f"link_up {dev} netns={netns}")


def ensure_default_route(netns: str, gateway: str, dev: str, actions: list[str]) -> None:
    out = run(["ip", "netns", "exec", netns, "ip", "route", "show", "default"], check=False).stdout
    needle = f"default via {gateway} dev {dev}"
    if needle in out:
        return
    run(["ip", "netns", "exec", netns, "ip", "route", "replace", "default", "via", gateway, "dev", dev])
    actions.append(f"default_route {netns} via={gateway} dev={dev}")


def ensure_resolv_conf(netns: str, nameservers: list[str], actions: list[str]) -> None:
    netns_dir = Path("/etc/netns") / netns
    ensure_dir(netns_dir)
    path = netns_dir / "resolv.conf"
    content = "".join([f"nameserver {ns}\n" for ns in nameservers if ns])
    if not content:
        content = "nameserver 223.5.5.5\n"
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return
    path.write_text(content, encoding="utf-8")
    actions.append(f"resolv_conf {path}")


def build_gost_command(item: dict, gost_bin: str) -> str:
    username = item.get("username", "")
    password = item.get("password", "")
    port = int(item["port"])
    return f"{shlex.quote(gost_bin)} -L socks5://{shlex.quote(username)}:{shlex.quote(password)}@:{port}"


def ensure_gost(netns: str, item: dict, gost_bin: str, actions: list[str]) -> None:
    port = str(int(item["port"]))
    service_name = f"xhs-gost-{netns}.service"
    service_path = Path("/etc/systemd/system") / service_name
    log_path = item.get("log_path") or f"/var/log/xhs-gost-{netns}.log"
    exec_start = f"/usr/sbin/ip netns exec {netns} {build_gost_command(item, gost_bin)}"
    unit = f"""[Unit]\nDescription=XHS netns gost for {netns}\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nType=simple\nExecStart={exec_start}\nRestart=always\nRestartSec=2s\nStandardOutput=append:{log_path}\nStandardError=append:{log_path}\n\n[Install]\nWantedBy=multi-user.target\n"""
    current = service_path.read_text(encoding="utf-8") if service_path.exists() else None
    if current != unit:
        service_path.write_text(unit, encoding="utf-8")
        actions.append(f"wrote_service {service_path}")

    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", "--now", service_name])
    actions.append(f"enabled_service {service_name} port={port}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply VLAN + netns + gost expansion plan")
    parser.add_argument("--plan", required=True, help="Path to netns-expansion-plan.json")
    parser.add_argument("--parent-dev", default="eth0")
    parser.add_argument("--gost-bin", default="/usr/local/sbin/gost")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("must run as root", file=sys.stderr)
        return 2

    if not cmd_exists("ip"):
        print("ip command not found", file=sys.stderr)
        return 2

    plan_path = Path(args.plan)
    data = json.loads(plan_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("plan must be a list")

    if data and not Path(args.gost_bin).exists() and not args.dry_run:
        print(f"gost binary not found: {args.gost_bin}", file=sys.stderr)
        return 3

    actions: list[str] = []
    skipped: list[str] = []

    for item in data:
        bind_ip = item.get("bind_ip")
        vlan_id = int(item.get("source_vlan"))
        netns = item.get("netns_name") or f"ns{vlan_id}"
        vlan_link = item.get("vlan_link") or f"{args.parent_dev}.{vlan_id}"
        nameservers = item.get("nameservers") or ["223.5.5.5"]
        gateway = item.get("gateway") or "192.168.0.1"
        prefix = int(item.get("prefix") or 24)

        if not bind_ip:
            skipped.append(f"skip missing_bind_ip vlan={vlan_id}")
            continue

        if args.dry_run:
            actions.append(f"would_apply netns={netns} vlan_link={vlan_link} bind_ip={bind_ip}/{prefix} port={item.get('port')}")
            continue

        ensure_netns(netns, actions)
        ensure_vlan_link(args.parent_dev, vlan_link, vlan_id, actions)
        move_link_to_netns(vlan_link, netns, actions)
        ensure_loopback_up(netns, actions)
        ensure_ip(netns, vlan_link, bind_ip, prefix, actions)
        ensure_link_up(netns, vlan_link, actions)
        ensure_default_route(netns, gateway, vlan_link, actions)
        ensure_resolv_conf(netns, nameservers, actions)
        ensure_gost(netns, item, args.gost_bin, actions)

    print(json.dumps({"actions": actions, "skipped": skipped}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def systemd_active(name: str) -> str:
    code, out, _ = run(["systemctl", "is-active", name])
    return out if code == 0 else (out or "inactive")


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-install healthcheck for xhs-proxy 4+N deployment")
    parser.add_argument("--generated-dir", default="generated-build", help="Generated/build directory")
    parser.add_argument("--service-name", default="xray")
    args = parser.parse_args()

    generated_dir = Path(args.generated_dir).resolve()
    resource_plan = generated_dir / "resource-plan.json"
    netns_plan = generated_dir / "netns-expansion-plan.json"

    result = {
        "generated_dir": str(generated_dir),
        "xray_service": {
            "name": args.service_name,
            "active": systemd_active(args.service_name),
        },
        "netns": [],
    }

    if netns_plan.exists():
        items = json.loads(netns_plan.read_text(encoding="utf-8"))
        for item in items:
            netns = item.get("netns_name")
            vlan_link = item.get("vlan_link")
            bind_ip = item.get("bind_ip")
            port = item.get("port")
            svc = f"xhs-gost-{netns}.service"

            _, addr_out, _ = run(["ip", "netns", "exec", netns, "ip", "-4", "addr", "show"],)
            _, route_out, _ = run(["ip", "netns", "exec", netns, "ip", "route", "show", "default"],)
            resolv_path = Path("/etc/netns") / netns / "resolv.conf"

            result["netns"].append(
                {
                    "netns": netns,
                    "vlan_link": vlan_link,
                    "bind_ip": bind_ip,
                    "port": port,
                    "gost_service": svc,
                    "gost_active": systemd_active(svc),
                    "has_bind_ip": bind_ip in addr_out,
                    "default_route": route_out,
                    "resolv_conf_exists": resolv_path.exists(),
                }
            )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

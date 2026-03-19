#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate netns expansion routes and proxy endpoints")
    parser.add_argument("--plan", required=True, help="Path to netns-expansion-plan.json")
    parser.add_argument("--endpoint", default="http://ifconfig.me/ip", help="Validation URL")
    parser.add_argument("--timeout", type=int, default=12, help="curl max time seconds")
    parser.add_argument("--proxy-host-field", choices=["bind_ip", "public_listen_ip"], default="bind_ip")
    parser.add_argument("--skip-proxy", action="store_true", help="Only validate direct netns egress")
    args = parser.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    if not isinstance(plan, list):
        raise ValueError("plan must be a list")

    results = []
    failed = False

    for item in plan:
        netns = item["netns_name"]
        bind_ip = item.get("bind_ip", "")
        port = int(item["port"])
        username = item.get("username", "")
        password = item.get("password", "")
        proxy_host = item.get(args.proxy_host_field) or bind_ip
        expected_public_ip = item.get("expected_public_ip", "")

        direct_cmd = [
            "ip", "netns", "exec", netns,
            "curl", "-4", "-sS", "--max-time", str(args.timeout), args.endpoint,
        ]
        d_code, d_out, d_err = run(direct_cmd)
        direct_ok = d_code == 0 and bool(d_out)
        if expected_public_ip:
            direct_ok = direct_ok and d_out.strip() == expected_public_ip

        proxy_ok = None
        p_out = ""
        p_err = ""
        p_code = None
        if not args.skip_proxy:
            proxy_cmd = [
                "curl", "-4", "-sS", "--max-time", str(args.timeout),
                "--socks5-hostname", f"{proxy_host}:{port}",
                "--proxy-user", f"{username}:{password}",
                args.endpoint,
            ]
            p_code, p_out, p_err = run(proxy_cmd)
            proxy_ok = p_code == 0 and bool(p_out)
            if expected_public_ip:
                proxy_ok = proxy_ok and p_out.strip() == expected_public_ip

        ok = direct_ok and (True if args.skip_proxy else bool(proxy_ok))
        if not ok:
            failed = True

        results.append(
            {
                "netns": netns,
                "bind_ip": bind_ip,
                "proxy_host": proxy_host,
                "port": port,
                "expected_public_ip": expected_public_ip,
                "direct": {
                    "ok": direct_ok,
                    "code": d_code,
                    "stdout": d_out,
                    "stderr": d_err,
                },
                "proxy": None if args.skip_proxy else {
                    "ok": proxy_ok,
                    "code": p_code,
                    "stdout": p_out,
                    "stderr": p_err,
                },
                "ok": ok,
            }
        )

    print(json.dumps({"endpoint": args.endpoint, "results": results}, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

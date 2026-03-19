#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], timeout: int = 20) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def load_proxies(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("proxies.json must be a list")
    return data


def test_proxy(proxy: dict, endpoint: str) -> dict:
    listen_ip = proxy["listen_ip"]
    port = proxy["port"]
    username = proxy["username"]
    password = str(proxy["password"])

    cmd = [
        "curl",
        "-sS",
        "--max-time",
        "15",
        "--socks5",
        f"{listen_ip}:{port}",
        "--proxy-user",
        f"{username}:{password}",
        endpoint,
    ]
    code, out, err = run(cmd)
    return {
        "name": proxy["name"],
        "listen": f"{listen_ip}:{port}",
        "username": username,
        "ok": code == 0,
        "result": out,
        "error": err,
        "expected_public_ip": proxy.get("expected_public_ip", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Test generated SOCKS5 proxies with curl")
    parser.add_argument(
        "proxies_json",
        nargs="?",
        default="generated/proxies.json",
        help="Path to generated proxies.json",
    )
    parser.add_argument(
        "--endpoint",
        default="https://api.ipify.org",
        help="HTTP endpoint used to validate proxy egress",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    proxies_path = (base_dir / args.proxies_json).resolve() if not Path(args.proxies_json).is_absolute() else Path(args.proxies_json)

    proxies = load_proxies(proxies_path)
    results = [test_proxy(proxy, args.endpoint) for proxy in proxies]

    failed = False
    for item in results:
        status = "OK" if item["ok"] else "FAIL"
        expected = item["expected_public_ip"]
        extra = f" expected={expected}" if expected else ""
        print(f"[{status}] {item['name']} {item['listen']} user={item['username']} result={item['result']}{extra}")
        if item["error"]:
            print(f"        error={item['error']}")
        if not item["ok"]:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

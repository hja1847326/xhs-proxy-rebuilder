#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def load_json_from_cmd(cmd: list[str]) -> tuple[int, dict | None, str]:
    code, out, err = run(cmd)
    if not out:
        return code, None, err
    try:
        return code, json.loads(out), err
    except Exception as exc:
        return code, None, f"{err}\njson_parse_error={exc}\nraw={out[:1000]}"


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run post-install verification for xhs-proxy 4+N deployment")
    parser.add_argument("--generated-dir", default="generated-build")
    parser.add_argument("--service-name", default="xray")
    parser.add_argument("--endpoint", default="http://ifconfig.me/ip")
    parser.add_argument("--proxy-host-field", choices=["bind_ip", "public_listen_ip"], default="bind_ip")
    parser.add_argument("--skip-proxy", action="store_true")
    parser.add_argument("--skip-direct", action="store_true")
    args = parser.parse_args()

    generated_dir = resolve(args.generated_dir)
    netns_plan = generated_dir / "netns-expansion-plan.json"

    health_cmd = [
        sys.executable,
        str(BASE_DIR / "scripts" / "healthcheck_install.py"),
        "--generated-dir",
        str(generated_dir),
        "--service-name",
        args.service_name,
    ]
    h_code, h_json, h_err = load_json_from_cmd(health_cmd)

    validation = None
    v_code = 0
    v_err = ""
    if netns_plan.exists() and netns_plan.stat().st_size > 0:
        validate_cmd = [
            sys.executable,
            str(BASE_DIR / "scripts" / "validate_netns_expansion.py"),
            "--plan",
            str(netns_plan),
            "--endpoint",
            args.endpoint,
            "--proxy-host-field",
            args.proxy_host_field,
        ]
        if args.skip_proxy:
            validate_cmd.append("--skip-proxy")
        if args.skip_direct:
            validate_cmd.append("--skip-direct")
        v_code, validation, v_err = load_json_from_cmd(validate_cmd)

    summary = {
        "generated_dir": str(generated_dir),
        "service_name": args.service_name,
        "endpoint": args.endpoint,
        "healthcheck": h_json,
        "healthcheck_error": h_err,
        "validation": validation,
        "validation_error": v_err,
        "ok": (h_code == 0) and (v_code == 0),
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

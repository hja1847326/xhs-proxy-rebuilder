#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("preflight result must be a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a human-readable summary from preflight JSON")
    parser.add_argument("input", nargs="?", help="Path to preflight JSON file; omit to read stdin")
    args = parser.parse_args()

    if args.input:
        data = load_json(Path(args.input))
    else:
        raw = sys.stdin.read()
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("preflight result must be a JSON object")

    status = data.get("status", "unknown")
    issues = data.get("issues", []) or []
    warnings = data.get("warnings", []) or []
    suggestions = data.get("suggestions", []) or []
    bind_checks = data.get("bind_checks", []) or []

    print("=== PREFLIGHT SUMMARY ===")
    print(f"status: {status}")
    if data.get("service_name"):
        print(f"service_name: {data['service_name']}")
    if data.get("xray_bin"):
        print(f"xray_bin: {data['xray_bin']}")

    print(f"issues: {len(issues)}")
    for item in issues:
        print(f"  - {item}")

    print(f"warnings: {len(warnings)}")
    for item in warnings:
        print(f"  - {item}")

    print(f"suggestions: {len(suggestions)}")
    for item in suggestions:
        print(f"  - {item}")

    if bind_checks:
        counts: dict[str, int] = {}
        for item in bind_checks:
            s = item.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1
        print("bind_checks:")
        for key in sorted(counts):
            print(f"  - {key}: {counts[key]}")

    if issues:
        print("[FAIL] decision=stop")
        return 1
    if warnings:
        print("[WARN] decision=caution")
        return 0

    print("[OK] decision=proceed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

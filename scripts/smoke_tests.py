#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"
TESTS_DIR = BASE_DIR / "tests"


def run_case(name: str, cmd: list[str], expect_success: bool) -> tuple[bool, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    ok = (proc.returncode == 0) == expect_success
    status = "PASS" if ok else "FAIL"
    output = (proc.stdout or "") + (proc.stderr or "")
    lines = [f"[{status}] {name}", f"  cmd: {' '.join(cmd)}", f"  exit: {proc.returncode}"]
    preview = "\n".join(output.strip().splitlines()[:8]).strip()
    if preview:
        lines.append("  output:")
        for line in preview.splitlines():
            lines.append(f"    {line}")
    return ok, "\n".join(lines)


def main() -> int:
    cases = [
        (
            "invalid duplicate port should fail",
            [sys.executable, str(SCRIPTS_DIR / "lint_inventory.py"), str(TESTS_DIR / "invalid-duplicate-port.yaml")],
            False,
        ),
        (
            "invalid duplicate username should fail",
            [sys.executable, str(SCRIPTS_DIR / "lint_inventory.py"), str(TESTS_DIR / "invalid-duplicate-username.yaml")],
            False,
        ),
        (
            "invalid profile strategy should fail",
            [
                sys.executable,
                str(SCRIPTS_DIR / "lint_inventory.py"),
                str(TESTS_DIR / "invalid-duplicate-port.yaml"),
                "--profile",
                str(TESTS_DIR / "invalid-profile-strategy.yaml"),
            ],
            False,
        ),
        (
            "known good profile+inventory should pass",
            [
                sys.executable,
                str(SCRIPTS_DIR / "lint_inventory.py"),
                str(BASE_DIR / "inventory" / "generated-10ip.yaml"),
                "--profile",
                str(BASE_DIR / "profiles" / "huaweicloud-10ip.yaml"),
            ],
            True,
        ),
    ]

    failed = 0
    for name, cmd, expect_success in cases:
        ok, text = run_case(name, cmd, expect_success)
        print(text)
        print()
        if not ok:
            failed += 1

    if failed:
        print(f"Smoke tests: FAIL ({failed} failed)")
        return 1

    print("Smoke tests: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

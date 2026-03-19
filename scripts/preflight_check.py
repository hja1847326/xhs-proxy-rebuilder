#!/usr/bin/env python3
import argparse
import json
import shutil
import socket
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def probe_bind(bind_ip: str, port: int) -> tuple[str, str]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((bind_ip, port))
        return "bind_ok", "bind available"
    except OSError as e:
        msg = str(e).lower()
        if "cannot assign requested address" in msg or "99" in msg:
            return "ip_not_local", str(e)
        if "address already in use" in msg or "98" in msg:
            return "port_in_use", str(e)
        return "bind_failed", str(e)
    finally:
        s.close()


def load_proxies(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("proxies.json must be a list")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight checks before installing generated xray bundle")
    parser.add_argument("--generated-dir", default="generated-build", help="Generated output directory")
    parser.add_argument("--service-name", default="xray", help="Target systemd service name")
    parser.add_argument("--xray-bin", default="/usr/local/bin/xray", help="Target xray binary path")
    parser.add_argument("--config-target", help="Target config path")
    parser.add_argument("--service-target", help="Target service file path")
    parser.add_argument("--static-only", action="store_true", help="Skip local bind probing; only run static checks")
    parser.add_argument("--gost-bin", default="/usr/local/sbin/gost", help="Target gost binary path for netns expansion")
    args = parser.parse_args()

    generated_dir = (BASE_DIR / args.generated_dir).resolve() if not Path(args.generated_dir).is_absolute() else Path(args.generated_dir)
    service_name = args.service_name
    config_target = Path(args.config_target) if args.config_target else Path(f"/etc/xray/{service_name}.json")
    service_target = Path(args.service_target) if args.service_target else Path(f"/etc/systemd/system/{service_name}.service")

    proxies_path = generated_dir / "proxies.json"
    xray_config_path = generated_dir / "xray-config.json"
    netns_plan_path = generated_dir / "netns-expansion-plan.json"
    issues: list[str] = []
    warnings: list[str] = []
    suggestions: list[str] = []
    bind_checks: list[dict] = []

    if not generated_dir.exists():
        issues.append(f"Generated directory not found: {generated_dir}")
    if not proxies_path.exists():
        issues.append(f"Missing proxies.json: {proxies_path}")
    if not xray_config_path.exists():
        issues.append(f"Missing xray-config.json: {xray_config_path}")

    xray_exists = Path(args.xray_bin).exists() and Path(args.xray_bin).is_file()
    if not xray_exists:
        issues.append(f"xray binary not found: {args.xray_bin}")

    gost_required = False
    if netns_plan_path.exists():
        try:
            netns_items = json.loads(netns_plan_path.read_text(encoding="utf-8"))
            gost_required = isinstance(netns_items, list) and len(netns_items) > 0
        except Exception:
            warnings.append(f"Invalid netns-expansion-plan.json: {netns_plan_path}")
            netns_items = []
    else:
        netns_items = []

    if gost_required and not (Path(args.gost_bin).exists() and Path(args.gost_bin).is_file()):
        warnings.append(f"gost binary not found: {args.gost_bin}")
        suggestions.append("If this bundle includes txt expansion routes, install gost or override GOST_BIN before running install.sh")

    systemctl_exists = shutil.which("systemctl") is not None
    if not systemctl_exists:
        issues.append("systemctl not found; this installer expects a systemd-based system")

    service_exists = service_target.exists()
    config_exists = config_target.exists()
    if service_exists:
        warnings.append(f"Service file already exists: {service_target}")
        if service_name == "xray":
            suggestions.append("Current target is the default xray service; consider SERVICE_NAME=xray-test for side-by-side testing")
    if config_exists:
        warnings.append(f"Config file already exists: {config_target}")

    active_conflicts: list[str] = []
    if systemctl_exists:
        code, out, _ = run(["systemctl", "is-active", service_name])
        if code == 0 and out == "active":
            warnings.append(f"Service is already active: {service_name}")
            suggestions.append("Use AUTO_START=0 for file-only install or switch to a test service name before replacing a live service")
        code, out, _ = run(["systemctl", "list-unit-files", "--type=service", "--no-legend"])
        if code == 0:
            for line in out.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("xray") and not line.startswith(f"{service_name}.service"):
                    active_conflicts.append(line.split()[0])
    if active_conflicts:
        warnings.append(f"Other xray-like services found: {', '.join(active_conflicts)}")
        suggestions.append("If these are production services, prefer sidecar testing with SERVICE_NAME=xray-test")

    port_conflicts: list[str] = []
    nonlocal_ips: list[str] = []
    bind_failures: list[str] = []
    bind_warnings: list[str] = []
    if proxies_path.exists():
        proxies = load_proxies(proxies_path)
        for proxy in proxies:
            bind_ip = proxy.get("listen_ip")
            port = proxy.get("port")
            name = proxy.get("name", "unknown")
            if not isinstance(bind_ip, str) or not isinstance(port, int):
                issues.append(f"Invalid proxy entry in proxies.json: {proxy}")
                continue
            try:
                socket.inet_aton(bind_ip)
            except OSError:
                bind_warnings.append(f"Proxy {name} has invalid bind IP: {bind_ip}")
                continue

            if args.static_only:
                bind_checks.append({"name": name, "listen": f"{bind_ip}:{port}", "status": "skipped_static_only"})
                continue

            status, detail = probe_bind(bind_ip, port)
            bind_checks.append({"name": name, "listen": f"{bind_ip}:{port}", "status": status, "detail": detail})
            if status == "port_in_use":
                port_conflicts.append(f"{name} -> {bind_ip}:{port}")
            elif status == "ip_not_local":
                nonlocal_ips.append(f"{name} -> {bind_ip}:{port}")
            elif status == "bind_failed":
                bind_failures.append(f"{name} -> {bind_ip}:{port} ({detail})")

    if port_conflicts:
        warnings.append(f"Port conflicts detected on this machine: {', '.join(port_conflicts)}")
    if nonlocal_ips:
        warnings.append(f"Target bind IPs are not present on this machine: {', '.join(nonlocal_ips)}")
        suggestions.append("Run preflight on the actual target server, or use --static-only when checking a generated bundle from another machine")
    if bind_failures:
        warnings.append(f"Other bind failures detected: {', '.join(bind_failures)}")
    warnings.extend(bind_warnings)

    result = {
        "generated_dir": str(generated_dir),
        "service_name": service_name,
        "xray_bin": args.xray_bin,
        "gost_bin": args.gost_bin,
        "config_target": str(config_target),
        "service_target": str(service_target),
        "static_only": args.static_only,
        "issues": issues,
        "warnings": warnings,
        "suggestions": suggestions,
        "bind_checks": bind_checks,
        "status": "ok" if not issues else "fail",
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

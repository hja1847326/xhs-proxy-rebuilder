#!/usr/bin/env python3
import argparse
import ipaddress
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml\nInstall with: python3 -m pip install pyyaml", file=sys.stderr)
    raise


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Inventory must be a YAML mapping")
    return data


def validate_ip(value: str, label: str, errors: list[str]) -> None:
    try:
        ipaddress.ip_address(value)
    except Exception:
        errors.append(f"Invalid IP for {label}: {value}")


def lint_profile_strategy(profile: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    strategy = profile.get("strategy", {}) if isinstance(profile, dict) else {}
    if not isinstance(strategy, dict):
        errors.append("profile.strategy must be a mapping")
        return errors, warnings

    username = strategy.get("username", {})
    if username:
        mode = username.get("mode")
        if mode not in (None, "prefix_counter"):
            errors.append(f"Unsupported username strategy mode: {mode}")
        start = username.get("start")
        if start is not None and (not isinstance(start, int) or start < 1):
            errors.append("username.start must be an integer >= 1")
        prefix = username.get("prefix")
        if prefix is not None and not str(prefix):
            errors.append("username.prefix must not be empty")

    password = strategy.get("password", {})
    if password:
        mode = password.get("mode")
        if mode not in (None, "fixed", "random"):
            errors.append(f"Unsupported password strategy mode: {mode}")
        if mode == "fixed":
            if password.get("value") in (None, ""):
                errors.append("password.value must not be empty when mode=fixed")
        if mode == "random":
            length = password.get("length")
            if length is not None and (not isinstance(length, int) or length < 4):
                errors.append("password.length must be an integer >= 4 when mode=random")
            alphabet = password.get("alphabet")
            if alphabet is not None and not str(alphabet):
                errors.append("password.alphabet must not be empty when provided")

    port = strategy.get("port", {})
    if port:
        mode = port.get("mode")
        if mode not in (None, "incremental"):
            errors.append(f"Unsupported port strategy mode: {mode}")
        start = port.get("start")
        if start is not None and (not isinstance(start, int) or not (1 <= start <= 65535)):
            errors.append("port.start must be an integer between 1 and 65535")

    return errors, warnings


def lint_inventory(data: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    proxies = data.get("proxies")
    if not isinstance(proxies, list) or not proxies:
        errors.append("Inventory must contain non-empty 'proxies'")
        return errors, warnings

    resources = data.get("resources", {})
    egresses = resources.get("egresses") if isinstance(resources, dict) else None
    is_v2 = isinstance(egresses, list) and len(egresses) > 0

    resource_ids = set()
    resource_ips = set()
    resource_map = {}
    bind_ip_usage: dict[str, list[str]] = {}
    if is_v2:
        for i, item in enumerate(egresses, start=1):
            rid = item.get("id")
            bind_ip = item.get("bind_ip")
            if not rid:
                errors.append(f"resources.egresses[{i}] missing id")
                continue
            if rid in resource_ids:
                errors.append(f"Duplicate resource id: {rid}")
            resource_ids.add(rid)
            resource_map[rid] = item
            if not bind_ip:
                errors.append(f"resources.egresses[{i}] missing bind_ip")
            else:
                validate_ip(bind_ip, f"resource {rid}.bind_ip", errors)
                if bind_ip in resource_ips:
                    warnings.append(f"Duplicate resource bind_ip detected: {bind_ip}")
                resource_ips.add(bind_ip)
                bind_ip_usage.setdefault(bind_ip, []).append(rid)

    proxy_names = set()
    ports = set()
    usernames = set()
    listen_pairs = set()
    resource_refs = set()

    for i, proxy in enumerate(proxies, start=1):
        name = proxy.get("name")
        listen_ip = proxy.get("listen_ip")
        port = proxy.get("port")
        username = proxy.get("username")
        password = proxy.get("password")
        account_label = proxy.get("account_label")

        if not name:
            errors.append(f"proxies[{i}] missing name")
        elif name in proxy_names:
            errors.append(f"Duplicate proxy name: {name}")
        else:
            proxy_names.add(name)

        if not listen_ip:
            errors.append(f"proxies[{i}] missing listen_ip")
        else:
            validate_ip(listen_ip, f"proxy {name or i}.listen_ip", errors)

        if not isinstance(port, int) or not (1 <= port <= 65535):
            errors.append(f"proxy {name or i} has invalid port: {port}")
        elif port in ports:
            errors.append(f"Duplicate proxy port: {port}")
        else:
            ports.add(port)

        if listen_ip and isinstance(port, int):
            pair = (listen_ip, port)
            if pair in listen_pairs:
                errors.append(f"Duplicate listen endpoint detected: {listen_ip}:{port}")
            else:
                listen_pairs.add(pair)

        if not username:
            errors.append(f"proxy {name or i} missing username")
        elif username in usernames:
            errors.append(f"Duplicate username detected: {username}")
        else:
            usernames.add(username)

        if password in (None, ""):
            errors.append(f"proxy {name or i} missing password")
        elif str(password) in ("123456", "admin", "password"):
            warnings.append(f"proxy {name or i} uses a weak/common password: {password}")

        if not account_label:
            warnings.append(f"proxy {name or i} missing account_label")

        if is_v2:
            resource_id = proxy.get("resource_id")
            if not resource_id:
                errors.append(f"proxy {name or i} missing resource_id")
            elif resource_id not in resource_map:
                errors.append(f"proxy {name or i} references unknown resource_id: {resource_id}")
            else:
                bind_ip = resource_map[resource_id].get("bind_ip")
                resource_refs.add(resource_id)
                if bind_ip and listen_ip and listen_ip != bind_ip:
                    warnings.append(
                        f"proxy {name or i} listen_ip ({listen_ip}) differs from resource {resource_id} bind_ip ({bind_ip})"
                    )
        else:
            send_through = proxy.get("send_through")
            if not send_through:
                errors.append(f"proxy {name or i} missing send_through (V1 format)")
            else:
                validate_ip(send_through, f"proxy {name or i}.send_through", errors)

    if is_v2:
        unused = sorted(set(resource_map.keys()) - resource_refs)
        if unused:
            warnings.append(f"Unused resources detected: {', '.join(unused)}")

    if len(proxies) < 4:
        warnings.append("Proxy count is below 4; for matrix usage this may be too small")

    for ip, ids in bind_ip_usage.items():
        if len(ids) > 1:
            warnings.append(f"Multiple resource ids share the same bind_ip {ip}: {', '.join(ids)}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint HuaweiCloud inventory before generation")
    parser.add_argument("inventory", nargs="?", default="inventory/huaweicloud-v2-sample.yaml")
    parser.add_argument("--profile", help="Optional profile YAML to validate strategy rules")
    parser.add_argument("--quiet", action="store_true", help="Suppress normal output unless errors occur")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    inventory_path = (base_dir / args.inventory).resolve() if not Path(args.inventory).is_absolute() else Path(args.inventory)

    data = load_yaml(inventory_path)
    errors, warnings = lint_inventory(data)

    profile_path = None
    if args.profile:
        profile_path = (base_dir / args.profile).resolve() if not Path(args.profile).is_absolute() else Path(args.profile)
        profile_data = load_yaml(profile_path)
        p_errors, p_warnings = lint_profile_strategy(profile_data)
        errors.extend(p_errors)
        warnings.extend(p_warnings)

    should_print = (not args.quiet) or bool(errors)
    if should_print:
        if profile_path:
            print(f"Profile: {profile_path}")
        print(f"Inventory: {inventory_path}")
        for warning in warnings:
            print(f"WARN: {warning}")
        for error in errors:
            print(f"ERROR: {error}")

    if errors:
        if should_print:
            print(f"Result: FAIL ({len(errors)} errors, {len(warnings)} warnings)")
        return 1

    if not args.quiet:
        print(f"Result: OK ({len(warnings)} warnings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

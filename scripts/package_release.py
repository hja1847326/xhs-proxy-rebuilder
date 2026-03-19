#!/usr/bin/env python3
import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


def copy_if_exists(src: Path, dst: Path) -> bool:
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    return False


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()


def write_bundle_meta(bundle_dir: Path, generated_dir: Path, profile: str | None, inventory: str | None, copied: list[str]) -> None:
    meta = {
        "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bundle_dir": str(bundle_dir),
        "generated_dir": str(generated_dir),
        "profile": str(resolve(profile)) if profile else None,
        "inventory": str(resolve(inventory)) if inventory else None,
        "copied_files": copied,
    }
    (bundle_dir / "bundle-meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_bundle_readme(bundle_dir: Path, profile: str | None, inventory: str | None, copied: list[str]) -> None:
    lines = [
        "# Release Bundle V2",
        "",
        "## 内容说明",
        "",
        "这个目录是一次可交付的构建结果，包含配置、安装脚本、代理清单和来源元数据。",
        "",
        "## 来源",
        "",
        f"- Profile: `{resolve(profile)}`" if profile else "- Profile: 未记录",
        f"- Inventory: `{resolve(inventory)}`" if inventory else "- Inventory: 未记录",
        "",
        "## 已打包文件",
        "",
    ]
    lines.extend([f"- {name}" for name in copied])
    lines.extend([
        "",
        "## 常用操作",
        "",
        "### 安装",
        "```bash",
        "sudo bash install.sh .",
        "```",
        "",
        "### 旁挂测试安装",
        "```bash",
        "sudo SERVICE_NAME=xray-test AUTO_ENABLE=0 bash install.sh .",
        "sudo systemctl restart xray-test",
        "sudo systemctl status xray-test --no-pager",
        "```",
        "",
        "### 查看代理",
        "```bash",
        "cat proxies.txt",
        "```",
    ])
    (bundle_dir / "BUNDLE.README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Package generated output into a releasable bundle")
    parser.add_argument("--generated-dir", default="generated-build", help="Generated output directory")
    parser.add_argument("--bundle-dir", default="dist/release-bundle", help="Bundle output directory")
    parser.add_argument("--profile", help="Profile used to generate this bundle")
    parser.add_argument("--inventory", help="Inventory used to generate this bundle")
    parser.add_argument("--quiet", action="store_true", help="Suppress normal summary output")
    args = parser.parse_args()

    generated_dir = resolve(args.generated_dir)
    bundle_dir = resolve(args.bundle_dir)

    bundle_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []

    file_map = [
        (generated_dir / "xray-config.json", bundle_dir / "xray-config.json"),
        (generated_dir / "xray.service", bundle_dir / "xray.service"),
        (generated_dir / "proxies.txt", bundle_dir / "proxies.txt"),
        (generated_dir / "proxies.csv", bundle_dir / "proxies.csv"),
        (generated_dir / "proxies.json", bundle_dir / "proxies.json"),
        (generated_dir / "INSTALL.md", bundle_dir / "INSTALL.generated.md"),
        (generated_dir / "resource-plan.json", bundle_dir / "resource-plan.json"),
        (generated_dir / "netns-expansion-plan.json", bundle_dir / "netns-expansion-plan.json"),
        (BASE_DIR / "scripts" / "install.sh", bundle_dir / "install.sh"),
        (BASE_DIR / "scripts" / "apply_network_plan.py", bundle_dir / "apply_network_plan.py"),
        (BASE_DIR / "scripts" / "apply_netns_expansion.py", bundle_dir / "apply_netns_expansion.py"),
        (BASE_DIR / "scripts" / "validate_netns_expansion.py", bundle_dir / "validate_netns_expansion.py"),
        (BASE_DIR / "scripts" / "test_proxies.py", bundle_dir / "test_proxies.py"),
        (BASE_DIR / "scripts" / "remote_preflight.sh", bundle_dir / "remote_preflight.sh"),
        (BASE_DIR / "scripts" / "render_preflight_summary.py", bundle_dir / "render_preflight_summary.py"),
        (BASE_DIR / "scripts" / "bootstrap_install.sh", bundle_dir / "bootstrap_install.sh"),
        (BASE_DIR / "scripts" / "install_xhs_proxy_from_url.sh", bundle_dir / "install_xhs_proxy_from_url.sh"),
        (BASE_DIR / "xhs-proxy", bundle_dir / "xhs-proxy"),
        (BASE_DIR / "scripts" / "xhs_proxy_cli.py", bundle_dir / "scripts" / "xhs_proxy_cli.py"),
        (BASE_DIR / "docs" / "netns-validation-v1.md", bundle_dir / "NETNS-VALIDATION.md"),
    ]

    if args.profile:
        file_map.append((resolve(args.profile), bundle_dir / "source-profile.yaml"))
    if args.inventory:
        file_map.append((resolve(args.inventory), bundle_dir / "source-inventory.yaml"))

    for src, dst in file_map:
        if copy_if_exists(src, dst):
            copied.append(dst.name)

    write_bundle_meta(bundle_dir, generated_dir, args.profile, args.inventory, copied)
    copied.append("bundle-meta.json")
    write_bundle_readme(bundle_dir, args.profile, args.inventory, copied)
    copied.append("BUNDLE.README.md")

    if not args.quiet:
        print(f"Bundle created at: {bundle_dir}")
        for name in copied:
            print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

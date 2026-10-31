#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GBA → GBARunner3 slot2patch 跨平台打包核心。

与 make_slot2patch.sh 行为对齐；可在 Windows / macOS / Linux 上只依赖
Python 3 + PatchToolForGbaR3（Windows 为 .exe）。

差分格式与 PatchTool 作者：卧看微尘 (Wokann)
https://github.com/Wokann/PatchToolForGbaR3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# 已知 No-Intro Rev0 SHA（仅当游戏码命中时硬拦／警告）
ORIG_SHA = {
    "BPRJ": "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486",
    "BPGJ": "2957b392dc09fc8df45a660af5493368d7bd378d299862f4cc115998e9da0bf2",
    "BPEJ": "33f5610b9186b4add09fef68895deb00f552b997b3d133b5a961e5123506343c",
}

MAX_PATCH_BLOCKS = 4096

FRIENDLY = {
    "BPRJ": "FireRed",
    "BPRE": "FireRed",
    "BPRP": "FireRed",
    "BPGJ": "LeafGreen",
    "BPGE": "LeafGreen",
    "BPGP": "LeafGreen",
    "BPEJ": "Emerald",
    "BPEE": "Emerald",
    "BPEP": "Emerald",
    "AXVJ": "Ruby",
    "AXVE": "Ruby",
    "AXVP": "Ruby",
    "AXPJ": "Sapphire",
    "AXPE": "Sapphire",
    "AXPP": "Sapphire",
}

RUNNER_COMMIT = "f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9"
PATCH_TOOL_REF = (
    "https://github.com/Wokann/PatchToolForGbaR3/tree/"
    "3250bf37a4a898bede86ce5883bf3ed3d6e9190c"
)


class Die(Exception):
    """用户可见致命错误。"""


def die(msg: str) -> None:
    raise Die(msg)


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rom_game_code(path: Path) -> str:
    with path.open("rb") as f:
        f.seek(0xAC)
        raw = f.read(4)
    if len(raw) != 4:
        die(f"无法从 {path} 读出 GameCode（偏移 0xAC）")
    try:
        code = raw.decode("ascii")
    except UnicodeDecodeError:
        die(f"原版 GameCode 非法: {raw!r}")
    if not all(32 <= ord(ch) < 127 for ch in code):
        die(f"原版 GameCode 非法: {code!r}")
    return code


def rom_version_byte(path: Path) -> int:
    with path.open("rb") as f:
        f.seek(0xBC)
        b = f.read(1)
    if len(b) != 1:
        die(f"无法从 {path} 读出版本字节（偏移 0xBC）")
    return b[0]


def rev_hex(ver_byte: int) -> str:
    return f"{ver_byte:02X}"


def safe_token(s: str, fallback: str) -> str:
    t = s.replace("/", "_").replace(" ", "_")
    t = re.sub(r"[^A-Za-z0-9._-]", "", t)
    return t or fallback


def find_tool(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("PATCH_TOOL")
    if env:
        candidates.append(Path(env))

    # 按平台优先：Windows 要 .exe；Unix 不要误选 PE
    if sys.platform == "win32":
        local_names = ["PatchToolForGbaR3.exe", "PatchToolForGbaR3"]
    else:
        local_names = ["PatchToolForGbaR3", "PatchToolForGbaR3.exe"]
    for n in local_names:
        candidates.append(SCRIPT_DIR / n)

    parent = SCRIPT_DIR.parent / "PatchToolForGbaR3"
    if sys.platform == "win32":
        candidates.append(parent / "PatchToolForGbaR3.exe")
        candidates.append(parent / "PatchToolForGbaR3")
    else:
        candidates.append(parent / "PatchToolForGbaR3")
        candidates.append(parent / "PatchToolForGbaR3.exe")
    candidates.append(Path("/workspace/PatchToolForGbaR3/PatchToolForGbaR3"))

    which = shutil.which("PatchToolForGbaR3") or shutil.which("PatchToolForGbaR3.exe")
    if which:
        candidates.append(Path(which))

    for c in candidates:
        try:
            if not c.is_file():
                continue
            # 跳过明显不适合当前平台的二进制
            if sys.platform == "win32":
                # 允许无扩展名或 .exe
                return c.resolve()
            # Unix：跳过 PE（.exe），避免误执行
            if c.suffix.lower() == ".exe":
                continue
            if os.access(c, os.X_OK):
                return c.resolve()
        except OSError:
            continue
    die(
        "找不到 PatchToolForGbaR3。请 --tool 指定，或把 "
        "PatchToolForGbaR3 / PatchToolForGbaR3.exe 放在本脚本同目录。"
    )


def run_tool(tool: Path, args: list[str]) -> None:
    cmd = [str(tool), *args]
    log(f"    $ {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, check=False)
    except OSError as e:
        die(f"无法启动 PatchTool: {e}")
    if r.returncode != 0:
        die(f"PatchTool 退出码 {r.returncode}")


def compare_applied(applied: Path, target: Path) -> str:
    a = applied.read_bytes()
    t = target.read_bytes()
    if a == t:
        return "exact"
    n = min(len(a), len(t))
    if a[:n] != t[:n]:
        return "mismatch"
    if len(t) > len(a) and all(b == 0xFF for b in t[len(a) :]):
        return "prefix_ff_pad"
    if len(a) > len(t) and all(b == 0xFF for b in a[len(t) :]):
        return "applied_ff_pad"
    return "mismatch"


def check_game_hint(hint: str, code: str) -> None:
    h = hint.strip().lower()
    mapping = {
        "firered": ("BPRJ", "BPRE"),
        "fr": ("BPRJ", "BPRE"),
        "火红": ("BPRJ", "BPRE"),
        "leafgreen": ("BPGJ", "BPGE"),
        "lg": ("BPGJ", "BPGE"),
        "叶绿": ("BPGJ", "BPGE"),
        "emerald": ("BPEJ", "BPEE"),
        "em": ("BPEJ", "BPEE"),
        "绿宝石": ("BPEJ", "BPEE"),
    }
    if h not in mapping:
        die("--game 只能是 firered / leafgreen / emerald（也可直接用 --name）")
    if code not in mapping[h]:
        die(f"--game {hint} 但原版是 {code}")


def build(
    orig: Path,
    cn: Path,
    *,
    version_label: str | None = None,
    friendly_name: str | None = None,
    out_dir: Path | None = None,
    tool_path: str | None = None,
    game_hint: str | None = None,
    force_orig: bool = False,
    skip_verify: bool = False,
) -> Path:
    """打包并返回 ZIP 路径。"""
    if not orig.is_file():
        die(f"请提供有效的 --orig <原版.gba>：{orig}")
    if not cn.is_file():
        die(f"请提供有效的 --cn <目标/汉化.gba>：{cn}")

    tool = find_tool(tool_path)
    code = rom_game_code(orig)
    ver_byte = rom_version_byte(orig)
    cn_code = rom_game_code(cn)
    cn_ver_byte = rom_version_byte(cn)
    rh = rev_hex(ver_byte)
    identity = f"{code}{rh}"

    if cn_code != code:
        die(f"原版与汉化 GameCode 必须相同（原版 {code}，汉化 {cn_code}）")
    if cn_ver_byte != ver_byte:
        log(
            f"警告: 汉化版本字节 {cn_ver_byte} ≠ 原版 {ver_byte}；"
            f"identity 仍按原版 Rev={rh} → {identity}"
        )

    if game_hint:
        check_game_hint(game_hint, code)

    game_name = friendly_name or FRIENDLY.get(code, code)
    expected = ORIG_SHA.get(code)
    orig_sha = sha256_file(orig)
    cn_sha = sha256_file(cn)

    if expected:
        if orig_sha != expected:
            log(f"警告: 原版 SHA 与常见 No-Intro Rev0 不一致（{code}）。")
            log(f"  期望: {expected}")
            log(f"  实际: {orig_sha}")
            if not force_orig:
                die("为防打错卡带补丁，已中止。确认无误请加 --force-orig。")
            log("已 --force-orig，继续。")
    else:
        log(f"提示: {code} 不在内置 No-Intro Rev0 表中，仅校验 GameCode 一致，不强制原版 SHA。")
        log(f"  原版 SHA: {orig_sha}")

    use_cn_stem = not version_label and not friendly_name
    if not version_label:
        version_label = f"custom ({datetime.now().strftime('%Y%m%d')})"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = safe_token(game_name, code)
    work = out_dir if out_dir else SCRIPT_DIR / f"out_{safe_name}_{stamp}"
    work = work.resolve()
    stage = work / "stage"
    titles = stage / "_gba" / "titles"
    titles.mkdir(parents=True, exist_ok=True)
    patch_path = titles / f"{identity}.patch"

    log(f"==> PatchTool: {tool}")
    log(f"==> identity: {identity} （GameCode={code} Rev={rh}） → {identity}.patch")
    log(f"==> 游戏名: {game_name}  版本: {version_label}")

    # 若已有旧文件，先清掉，避免误用
    if patch_path.exists():
        patch_path.unlink()
    json_side = Path(str(patch_path) + ".json")
    if json_side.exists():
        json_side.unlink()

    run_tool(tool, ["-c", str(orig), str(cn), str(patch_path)])
    if not patch_path.is_file():
        die(f"未生成补丁: {patch_path}")
    # 工具会顺带写 .patch.json；SD 不需要
    if json_side.exists():
        json_side.unlink()

    magic = patch_path.read_bytes()[:8]
    if magic != b"PATCHGR3":
        die(f"补丁头不是 PATCHGR3（读到: {magic!r}）")

    patch_sha = sha256_file(patch_path)
    patch_bytes = patch_path.stat().st_size
    header = patch_path.read_bytes()[:28]
    if len(header) < 28:
        die("补丁文件过短，无法读块数")
    patch_blocks = struct.unpack_from("<I", header, 24)[0]

    log(f"==> 补丁: {patch_bytes} 字节，{patch_blocks} 块")

    if patch_blocks >= MAX_PATCH_BLOCKS:
        try:
            patch_path.unlink()
        except OSError:
            pass
        die(
            f"差分块数 {patch_blocks} ≥ {MAX_PATCH_BLOCKS}，过大，不适合 slot2patch"
            f"（PatchTool／GBR3 块数上限约 4096）。可考虑 slot2save 或其他方案。"
        )

    independent_ok = False
    author_apply_ok = False
    if not skip_verify:
        log("==> 还原核对（apply → 与目标比较；尺寸不同时允许目标尾部全 0xFF）")
        verify_rom = work / "verify_apply.gba"
        if verify_rom.exists():
            verify_rom.unlink()
        run_tool(tool, ["-a", str(patch_path), str(orig), str(verify_rom)])
        verify_sha = sha256_file(verify_rom)
        match = compare_applied(verify_rom, cn)
        if match in ("exact", "prefix_ff_pad", "applied_ff_pad"):
            independent_ok = True
            author_apply_ok = True
            log(f"还原一致 ({match}): applied={verify_sha} target={cn_sha}")
        else:
            die(f"还原与目标不一致（applied {verify_sha} ≠ target {cn_sha}）。补丁不可用。")
    else:
        log("已 --skip-verify，跳过还原核对。")

    safe_ver = safe_token(version_label, "custom")
    region_char = code[3] if len(code) >= 4 else ""
    if region_char.upper() == "J":
        zip_basename = f"{safe_name}_JP_CN_{safe_ver}_slot2patch.zip"
    else:
        zip_basename = f"{safe_name}_{identity}_{safe_ver}_slot2patch.zip"
    if use_cn_stem:
        # 未给版本／显示名：直接用汉化 ROM 文件名（去扩展名）
        stem = re.sub(r'[\\/:*?"<>|\s]+', "_", cn.stem).strip("._") or "custom"
        zip_basename = f"{stem}_slot2patch.zip"
    zip_path = work / zip_basename

    info = {
        "game": game_name,
        "version": version_label,
        "identity": identity,
        "game_code": code,
        "rom_version": rh,
        "original_sha256": orig_sha,
        "target_sha256": cn_sha,
        "patch_sha256": patch_sha,
        "patch_bytes": int(patch_bytes),
        "patch_blocks": int(patch_blocks),
        "format": "PATCHGR3 / slot2patch",
        "runner_commit": RUNNER_COMMIT,
        "patch_tool": PATCH_TOOL_REF,
        "independent_exact": independent_ok,
        "author_apply_exact": author_apply_ok,
        "hardware_verified": False,
        "uploaded": False,
        "credit": "差分格式与 PatchTool 作者：卧看微尘 (Wokann)。本打包脚本仅封装调用。",
    }
    (stage / "PATCH_INFO.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (stage / "SHA256.txt").write_text(
        f"{patch_sha}  _gba/titles/{identity}.patch\n", encoding="utf-8"
    )

    usage_md = f"""# {game_name} {version_label}：slot2patch 外挂汉化补丁

由 `slot2patch_core.py` / `make_slot2patch.sh` 生成。差分算法与 `.patch` 格式来自 **卧看微尘** [PatchToolForGbaR3](https://github.com/Wokann/PatchToolForGbaR3)；运行环境为 Wokann GBARunner3 `cache-hicode/slot2patch`（参考提交 `f8ac25c`）。

本包**不是**完整 GBARunner3 教程，不附 NDS 程序／BIOS／ROM／存档。不宣称 GBR3 已正式支持任意 ROM。

## 放到 SD 哪里

把本包里的 `_gba` 合并到烧录卡 SD 根目录：

```text
SD:/_gba/titles/{identity}.patch
```

保持英文文件名。不要叠成 `_gba/_gba/titles`。无需放置 `.patch.json`。

identity 规则：GameCode（ROM 偏移 0xAC）+ Rev（0xBC，两位大写十六进制）→ `{identity}`。

## SHA

- 原版：`{orig_sha}`
- 汉化目标：`{cn_sha}`
- 本补丁：`{patch_sha}`（{patch_bytes} 字节，{patch_blocks} 块）

卡带必须与上述原版一致；能启动不等于卡带完全匹配。

## 限制

- 原版与汉化 GameCode 必须相同。
- 差分块数过大（约 ≥4096）时不适合 slot2patch，可考虑 slot2save。
- 本脚本不保证任意 ROM 都能在实机 GBR3 上运行。

## 安全

- 补丁不会烧进卡带 ROM；游戏内保存仍会写入正版卡存档。
- 首次先读档看画面，重要存档先备份；异常时不要保存。
- `hardware_verified` 默认为 false，实机长测通过后再改口径。
"""
    (stage / "使用说明.md").write_text(usage_md, encoding="utf-8")

    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in ["PATCH_INFO.json", "SHA256.txt", "使用说明.md"]:
            zf.write(stage / name, name)
        for f in sorted(titles.iterdir()):
            if f.is_file() and f.suffix == ".patch":
                zf.write(f, f"_gba/titles/{f.name}")

    log("")
    log("完成:")
    log(f"  ZIP:   {zip_path}")
    log(f"  补丁:  {patch_path}")
    log(f"  信息:  {stage / 'PATCH_INFO.json'}")
    log("请署名卧看微尘；公开完整 GBR3 教程前先征得他同意。")
    return zip_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="任意 GBA ROM → GBARunner3 slot2patch 一键打包（跨平台核心）"
    )
    p.add_argument("--orig", required=True, help="原版 .gba")
    p.add_argument("--cn", required=True, help="目标／汉化 .gba")
    p.add_argument("--version", default="", help='版本标签，如 "v1.13"')
    p.add_argument("--name", default="", help="友好名，如 Emerald")
    p.add_argument("--out", default="", help="输出目录")
    p.add_argument("--tool", default="", help="PatchTool 路径")
    p.add_argument("--game", default="", help="firered / leafgreen / emerald")
    p.add_argument("--force-orig", action="store_true")
    p.add_argument("--skip-verify", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        build(
            Path(args.orig),
            Path(args.cn),
            version_label=args.version or None,
            friendly_name=args.name or None,
            out_dir=Path(args.out) if args.out else None,
            tool_path=args.tool or None,
            game_hint=args.game or None,
            force_orig=args.force_orig,
            skip_verify=args.skip_verify,
        )
        return 0
    except Die as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

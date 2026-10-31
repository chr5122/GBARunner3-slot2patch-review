#!/usr/bin/env bash
# 任意 GBA ROM → GBARunner3 slot2patch 一键打包
# 优先转发到同目录 slot2patch_core.py（跨平台核心）；若无 python3/core 则用内置 bash 实现。
# 核心差分来自卧看微尘 PatchToolForGbaR3（请署名）
# 兼容 macOS Bash 3.2；打包用 python3 zipfile（不依赖 zip 命令）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CORE="$SCRIPT_DIR/slot2patch_core.py"

# 有 Python 核心时直接转发（Windows Git Bash / macOS / Linux 行为一致）
if [ -f "$CORE" ] && command -v python3 >/dev/null 2>&1; then
  exec python3 "$CORE" "$@"
fi

# ---------- 以下为无 core 时的备用 bash 实现 ----------
PATCH_TOOL="${PATCH_TOOL:-}"
VERSION_LABEL=""
OUT_DIR=""
SKIP_VERIFY=0
FORCE_ORIG=0
FRIENDLY_NAME=""
GAME_HINT=""

ORIG_SHA_BPRJ="1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
ORIG_SHA_BPGJ="2957b392dc09fc8df45a660af5493368d7bd378d299862f4cc115998e9da0bf2"
ORIG_SHA_BPEJ="33f5610b9186b4add09fef68895deb00f552b997b3d133b5a961e5123506343c"
MAX_PATCH_BLOCKS=4096

usage() {
  cat <<'U'
用法:
  make_slot2patch.sh --orig <原版.gba> --cn <目标/汉化.gba> \
      [--version "v1.13"] [--name Emerald] [--out <目录>] \
      [--tool <PatchTool路径>] [--force-orig] [--skip-verify]

说明:
  - identity = GameCode(ROM 0xAC 起 4 字节 ASCII) + Rev(ROM 0xBC，两位大写十六进制)
  - 原版与目标 GameCode 必须相同
  - 产出 ZIP：_gba/titles/<identity>.patch + PATCH_INFO.json + SHA256.txt + 使用说明.md
  - 差分块数 ≥ 4096 时中止
  - 差分工具作者：https://github.com/Wokann/PatchToolForGbaR3
U
}

die() { echo "错误: $*" >&2; exit 1; }

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    die "需要 sha256sum 或 shasum"
  fi
}

rom_game_code() { dd if="$1" bs=1 skip=172 count=4 2>/dev/null; }
rom_version_byte() {
  python3 -c "import sys; print(open(sys.argv[1],'rb').read(189)[188])" "$1"
}
rev_hex() { printf '%02X' "$1"; }

friendly_name_for_code() {
  case "$1" in
    BPRJ|BPRE|BPRP) echo "FireRed" ;;
    BPGJ|BPGE|BPGP) echo "LeafGreen" ;;
    BPEJ|BPEE|BPEP) echo "Emerald" ;;
    AXVJ|AXVE|AXVP) echo "Ruby" ;;
    AXPJ|AXPE|AXPP) echo "Sapphire" ;;
    *) echo "$1" ;;
  esac
}

expected_orig_sha_for_code() {
  case "$1" in
    BPRJ) echo "$ORIG_SHA_BPRJ" ;;
    BPGJ) echo "$ORIG_SHA_BPGJ" ;;
    BPEJ) echo "$ORIG_SHA_BPEJ" ;;
    *) echo "" ;;
  esac
}

find_tool() {
  if [ -n "$PATCH_TOOL" ] && [ -x "$PATCH_TOOL" ]; then
    echo "$PATCH_TOOL"; return 0
  fi
  for c in \
    "$SCRIPT_DIR/PatchToolForGbaR3" \
    "$SCRIPT_DIR/PatchToolForGbaR3.exe" \
    "$SCRIPT_DIR/../PatchToolForGbaR3/PatchToolForGbaR3" \
    "/workspace/PatchToolForGbaR3/PatchToolForGbaR3"
  do
    if [ -x "$c" ]; then echo "$c"; return 0; fi
  done
  if command -v PatchToolForGbaR3 >/dev/null 2>&1; then
    command -v PatchToolForGbaR3; return 0
  fi
  die "找不到 PatchToolForGbaR3。请 --tool 指定，或编译后放在脚本同目录。"
}

ORIG=""; CN=""
while [ $# -gt 0 ]; do
  case "$1" in
    --orig) ORIG="${2:-}"; shift 2 ;;
    --cn) CN="${2:-}"; shift 2 ;;
    --version) VERSION_LABEL="${2:-}"; shift 2 ;;
    --name) FRIENDLY_NAME="${2:-}"; shift 2 ;;
    --out) OUT_DIR="${2:-}"; shift 2 ;;
    --tool) PATCH_TOOL="${2:-}"; shift 2 ;;
    --game) GAME_HINT="${2:-}"; shift 2 ;;
    --force-orig) FORCE_ORIG=1; shift ;;
    --skip-verify) SKIP_VERIFY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "未知参数: $1（见 --help）" ;;
  esac
done

[ -n "$ORIG" ] && [ -f "$ORIG" ] || die "请提供 --orig <原版.gba>"
[ -n "$CN" ] && [ -f "$CN" ] || die "请提供 --cn <目标/汉化.gba>"
command -v python3 >/dev/null 2>&1 || die "需要 python3"
command -v dd >/dev/null 2>&1 || die "需要 dd"

TOOL="$(find_tool)"
CODE="$(rom_game_code "$ORIG")"
VER_BYTE="$(rom_version_byte "$ORIG")"
CN_CODE="$(rom_game_code "$CN")"
CN_VER_BYTE="$(rom_version_byte "$CN")"
REV_HEX="$(rev_hex "$VER_BYTE")"
ID="${CODE}${REV_HEX}"

python3 -c "
import sys
c=sys.argv[1]
if len(c)!=4 or not all(32 <= ord(ch) < 127 for ch in c):
    sys.exit('原版 GameCode 非法: %r' % c)
" "$CODE" || die "无法从原版读出合法 GameCode（偏移 0xAC）"

[ "$CN_CODE" = "$CODE" ] || die "原版与汉化 GameCode 必须相同（原版 $CODE，汉化 $CN_CODE）"
if [ "$CN_VER_BYTE" != "$VER_BYTE" ]; then
  echo "警告: 汉化版本字节 $CN_VER_BYTE ≠ 原版 $VER_BYTE；identity 仍按原版 Rev=$REV_HEX → $ID" >&2
fi

if [ -n "$GAME_HINT" ]; then
  case "$GAME_HINT" in
    firered|FR|火红) [ "$CODE" = "BPRJ" ] || [ "$CODE" = "BPRE" ] || die "--game firered 但原版是 $CODE" ;;
    leafgreen|LG|叶绿) [ "$CODE" = "BPGJ" ] || [ "$CODE" = "BPGE" ] || die "--game leafgreen 但原版是 $CODE" ;;
    emerald|EM|绿宝石) [ "$CODE" = "BPEJ" ] || [ "$CODE" = "BPEE" ] || die "--game emerald 但原版是 $CODE" ;;
    *) die "--game 只能是 firered / leafgreen / emerald（也可直接用 --name）" ;;
  esac
fi

if [ -n "$FRIENDLY_NAME" ]; then GAME_NAME="$FRIENDLY_NAME"
else GAME_NAME="$(friendly_name_for_code "$CODE")"; fi

EXPECTED_ORIG="$(expected_orig_sha_for_code "$CODE")"
ORIG_SHA="$(sha256_file "$ORIG")"
CN_SHA="$(sha256_file "$CN")"

if [ -n "$EXPECTED_ORIG" ]; then
  if [ "$ORIG_SHA" != "$EXPECTED_ORIG" ]; then
    echo "警告: 原版 SHA 与常见 No-Intro Rev0 不一致（$CODE）。" >&2
    echo "  期望: $EXPECTED_ORIG" >&2
    echo "  实际: $ORIG_SHA" >&2
    if [ "$FORCE_ORIG" -ne 1 ]; then
      die "为防打错卡带补丁，已中止。确认无误请加 --force-orig。"
    fi
    echo "已 --force-orig，继续。" >&2
  fi
else
  echo "提示: $CODE 不在内置 No-Intro Rev0 表中，仅校验 GameCode 一致，不强制原版 SHA。" >&2
  echo "  原版 SHA: $ORIG_SHA" >&2
fi

[ -z "$VERSION_LABEL" ] && VERSION_LABEL="custom ($(date +%Y%m%d))"
STAMP="$(date +%Y%m%d_%H%M%S)"
SAFE_NAME="$(echo "$GAME_NAME" | tr ' /' '__' | tr -cd 'A-Za-z0-9._-')"
[ -n "$SAFE_NAME" ] || SAFE_NAME="$CODE"
WORK="${OUT_DIR:-$SCRIPT_DIR/out_${SAFE_NAME}_${STAMP}}"
STAGE="$WORK/stage"
mkdir -p "$STAGE/_gba/titles"
PATCH_PATH="$STAGE/_gba/titles/${ID}.patch"

echo "==> PatchTool: $TOOL"
echo "==> identity: $ID （GameCode=$CODE Rev=$REV_HEX） → ${ID}.patch"
echo "==> 游戏名: $GAME_NAME  版本: $VERSION_LABEL"
"$TOOL" -c "$ORIG" "$CN" "$PATCH_PATH"
[ -f "$PATCH_PATH" ] || die "未生成补丁: $PATCH_PATH"
rm -f "${PATCH_PATH}.json"

MAGIC="$(dd if="$PATCH_PATH" bs=1 count=8 2>/dev/null || true)"
[ "$MAGIC" = "PATCHGR3" ] || die "补丁头不是 PATCHGR3（读到: $MAGIC）"

PATCH_SHA="$(sha256_file "$PATCH_PATH")"
PATCH_BYTES="$(wc -c < "$PATCH_PATH" | tr -d ' ')"
PATCH_BLOCKS="$(python3 -c "import struct,sys; print(struct.unpack_from('<I', open(sys.argv[1],'rb').read(28), 24)[0])" "$PATCH_PATH")"
echo "==> 补丁: ${PATCH_BYTES} 字节，${PATCH_BLOCKS} 块"

if [ "$PATCH_BLOCKS" -ge "$MAX_PATCH_BLOCKS" ]; then
  rm -f "$PATCH_PATH"
  die "差分块数 ${PATCH_BLOCKS} ≥ ${MAX_PATCH_BLOCKS}，过大，不适合 slot2patch。"
fi

INDEPENDENT_OK=false; AUTHOR_APPLY_OK=false
if [ "$SKIP_VERIFY" -eq 0 ]; then
  echo "==> 还原核对（apply → 与目标比较；尺寸不同时允许目标尾部全 0xFF）"
  VERIFY_ROM="$WORK/verify_apply.gba"
  "$TOOL" -a "$PATCH_PATH" "$ORIG" "$VERIFY_ROM"
  VERIFY_SHA="$(sha256_file "$VERIFY_ROM")"
  MATCH="$(python3 -c "
import sys
applied=open(sys.argv[1],'rb').read()
target=open(sys.argv[2],'rb').read()
if applied == target: print('exact'); sys.exit(0)
n=min(len(applied), len(target))
if applied[:n] != target[:n]: print('mismatch'); sys.exit(0)
if len(target) > len(applied) and all(b==0xFF for b in target[len(applied):]): print('prefix_ff_pad'); sys.exit(0)
if len(applied) > len(target) and all(b==0xFF for b in applied[len(target):]): print('applied_ff_pad'); sys.exit(0)
print('mismatch')
" "$VERIFY_ROM" "$CN")"
  if [ "$MATCH" = "exact" ] || [ "$MATCH" = "prefix_ff_pad" ] || [ "$MATCH" = "applied_ff_pad" ]; then
    AUTHOR_APPLY_OK=true; INDEPENDENT_OK=true
    echo "还原一致 ($MATCH): applied=$VERIFY_SHA target=$CN_SHA"
  else
    die "还原与目标不一致（applied $VERIFY_SHA ≠ target $CN_SHA）。补丁不可用。"
  fi
else
  echo "已 --skip-verify，跳过还原核对。"
fi

REGION_CHAR="$(printf '%s' "$CODE" | cut -c4)"
SAFE_VER="$(echo "$VERSION_LABEL" | tr '/ ' '__' | tr -cd 'A-Za-z0-9._-')"
[ -n "$SAFE_VER" ] || SAFE_VER="custom"
if [ "$REGION_CHAR" = "J" ] || [ "$REGION_CHAR" = "j" ]; then
  ZIP_BASENAME="${SAFE_NAME}_JP_CN_${SAFE_VER}_slot2patch.zip"
else
  ZIP_BASENAME="${SAFE_NAME}_${ID}_${SAFE_VER}_slot2patch.zip"
fi
ZIP_PATH="$WORK/$ZIP_BASENAME"

export INFO_GAME="$GAME_NAME" INFO_VER="$VERSION_LABEL" INFO_ID="$ID"
export INFO_CODE="$CODE" INFO_REV="$REV_HEX"
export INFO_ORIG="$ORIG_SHA" INFO_CN="$CN_SHA" INFO_PATCH="$PATCH_SHA"
export INFO_BYTES="$PATCH_BYTES" INFO_BLOCKS="$PATCH_BLOCKS"
export INFO_IND="$INDEPENDENT_OK" INFO_AUTH="$AUTHOR_APPLY_OK"
export INFO_OUT="$STAGE/PATCH_INFO.json"
python3 <<'PY'
import json, os
info = {
  "game": os.environ["INFO_GAME"],
  "version": os.environ["INFO_VER"],
  "identity": os.environ["INFO_ID"],
  "game_code": os.environ["INFO_CODE"],
  "rom_version": os.environ["INFO_REV"],
  "original_sha256": os.environ["INFO_ORIG"],
  "target_sha256": os.environ["INFO_CN"],
  "patch_sha256": os.environ["INFO_PATCH"],
  "patch_bytes": int(os.environ["INFO_BYTES"]),
  "patch_blocks": int(os.environ["INFO_BLOCKS"]),
  "format": "PATCHGR3 / slot2patch",
  "runner_commit": "f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9",
  "patch_tool": "https://github.com/Wokann/PatchToolForGbaR3/tree/3250bf37a4a898bede86ce5883bf3ed3d6e9190c",
  "independent_exact": os.environ["INFO_IND"] == "true",
  "author_apply_exact": os.environ["INFO_AUTH"] == "true",
  "hardware_verified": False,
  "uploaded": False,
  "credit": "差分格式与 PatchTool 作者：卧看微尘 (Wokann)。本打包脚本仅封装调用。",
}
open(os.environ["INFO_OUT"], "w", encoding="utf-8").write(
  json.dumps(info, indent=2, ensure_ascii=False) + "\n"
)
PY

echo "$PATCH_SHA  _gba/titles/${ID}.patch" > "$STAGE/SHA256.txt"
cat > "$STAGE/使用说明.md" <<MD
# ${GAME_NAME} ${VERSION_LABEL}：slot2patch 外挂汉化补丁

由 \`make_slot2patch.sh\` / \`slot2patch_core.py\` 生成。差分算法与 \`.patch\` 格式来自 **卧看微尘** [PatchToolForGbaR3](https://github.com/Wokann/PatchToolForGbaR3)。

本包**不是**完整 GBARunner3 教程。SD 路径：\`_gba/titles/${ID}.patch\`。

- 原版：\`${ORIG_SHA}\`
- 汉化：\`${CN_SHA}\`
- 补丁：\`${PATCH_SHA}\`（${PATCH_BYTES} 字节，${PATCH_BLOCKS} 块）
MD

export STAGE ZIP_PATH
python3 <<'PY'
import os, zipfile
from pathlib import Path
stage = Path(os.environ["STAGE"])
zpath = Path(os.environ["ZIP_PATH"])
if zpath.exists(): zpath.unlink()
with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for name in ["PATCH_INFO.json", "SHA256.txt", "使用说明.md"]:
        zf.write(stage / name, name)
    titles = stage / "_gba" / "titles"
    for f in sorted(titles.iterdir()):
        if f.is_file() and f.suffix == ".patch":
            zf.write(f, f"_gba/titles/{f.name}")
PY

echo
echo "完成:"
echo "  ZIP:   $ZIP_PATH"
echo "  补丁:  $PATCH_PATH"
echo "请署名卧看微尘；公开完整 GBR3 教程前先征得他同意。"

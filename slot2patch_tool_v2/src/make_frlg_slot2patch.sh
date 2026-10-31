#!/usr/bin/env bash
# 兼容入口：火红／叶绿一键打包 → 转发到通用 make_slot2patch.sh
# 旧命令参数保持可用；任意 GBA 也请直接用 make_slot2patch.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/make_slot2patch.sh" "$@"

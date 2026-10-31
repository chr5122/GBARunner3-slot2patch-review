#!/bin/bash
# 双击打开 GBA slot2patch 图形界面（源码版）。推荐直接用打包好的「slot2patch工具.app」。
cd "$(dirname "$0")" || exit 1
export LANG="${LANG:-zh_CN.UTF-8}"
msg(){ osascript -e "display dialog \"$1\" buttons {\"好\"} default button 1 with title \"无法启动\"" >/dev/null 2>&1; echo "$1" >&2; }
PY=""
for c in ./.python/bin/python3 "$HOME/.local/bin/python3.12" /Library/Frameworks/Python.framework/Versions/Current/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 python3; do
  [ "$c" = /usr/bin/python3 ] && continue
  p=$(command -v "$c" 2>/dev/null) || continue
  [ "$p" = /usr/bin/python3 ] && continue
  # 只做版本检查，不建窗口；超时 10 秒
  v=$( ( "$p" -c 'import tkinter,sys;print(tkinter.TkVersion)' 2>/dev/null & pid=$!; (sleep 10; kill $pid 2>/dev/null) & wait $pid ) )
  if [ -n "$v" ] && awk "BEGIN{exit !($v>=8.6)}"; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then
  msg "找不到带 Tk 8.6 以上的 Python（系统自带 /usr/bin/python3 是 Tk 8.5，会白屏，已跳过）。\n\n请改用打包好的 slot2patch工具.app，或从 python.org 安装 Python 3.12。"
  exit 1
fi
exec "$PY" ./gui_slot2patch.py

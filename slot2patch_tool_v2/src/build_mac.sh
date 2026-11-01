#!/bin/bash
# 用私有 Python（uv 管理，不动系统 Python）+ PyInstaller 打 macOS .app
set -euo pipefail
cd "$(dirname "$0")"
UV="${UV:-$HOME/.local/bin/uv}"
"$UV" python install 3.12
VENV="$HOME/.cache/slot2patch_build/venv"
[ -x "$VENV/bin/python" ] || "$UV" venv --python 3.12 "$VENV"
"$UV" pip install --python "$VENV/bin/python" pyinstaller
"$VENV/bin/python" -c 'import tkinter;assert tkinter.TkVersion>=8.6,tkinter.TkVersion;print("Tk",tkinter.TkVersion)'
rm -rf build dist
"$VENV/bin/pyinstaller" --noconfirm --windowed --name "slot2patch工具" \
  --osx-bundle-identifier org.gbr3.slot2patch \
  --hidden-import lr_scan --hidden-import slot2patch_core --hidden-import gui_lrscan --hidden-import gui_slot2patch \
  --add-binary "PatchToolForGbaR3:." --add-data "_gba:_gba" --add-data "使用说明.md:." \
  app_main.py
codesign --force --deep -s - "dist/slot2patch工具.app"
echo OK

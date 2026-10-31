@echo off
chcp 65001 >nul
REM 在 Windows 上一键打包 slot2patch工具.exe（需先装 python.org 的 Python 3.12，勾选 tcl/tk）
cd /d "%~dp0"
py -3.12 -m venv .venv || goto :err
.venv\Scripts\python -m pip install --upgrade pyinstaller || goto :err
.venv\Scripts\python -c "import tkinter; assert float(tkinter.TkVersion)>=8.6, tkinter.TkVersion" || goto :err
.venv\Scripts\pyinstaller --noconfirm --windowed --clean --noupx --name "slot2patch工具" ^
  --hidden-import lr_scan --hidden-import slot2patch_core --hidden-import gui_lrscan --hidden-import gui_slot2patch --hidden-import tkinter ^
  --add-binary "PatchToolForGbaR3.exe;." --add-data "_gba;_gba" --add-data "使用说明.md;." app_main.py || goto :err
echo 完成：dist\slot2patch工具\slot2patch工具.exe
echo 发布包由 .github/workflows/slot2patch-windows.yml 在 windows-latest 上打 zip。
pause
exit /b 0
:err
echo 打包失败
pause
exit /b 1

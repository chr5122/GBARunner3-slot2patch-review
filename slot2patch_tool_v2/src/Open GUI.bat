@echo off
REM GBA slot2patch GUI launcher (Windows)
REM Needs Python 3 with Tcl/Tk. Diff tool: Wokann PatchToolForGbaR3.
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set "PY="
where py >nul 2>&1 && (
  py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
)
if not defined PY (
  where python >nul 2>&1 && (
    python -c "import sys" >nul 2>&1 && set "PY=python"
  )
)
if not defined PY (
  where python3 >nul 2>&1 && (
    python3 -c "import sys" >nul 2>&1 && set "PY=python3"
  )
)

if not defined PY (
  echo.
  echo [错误] 找不到 Python 3。
  echo 请从 https://www.python.org/downloads/ 安装，勾选：
  echo   - Add python.exe to PATH
  echo   - tcl/tk and IDLE
  echo 装好后重新双击本文件。
  echo.
  pause
  exit /b 1
)

%PY% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
  echo.
  echo [错误] 当前 Python 没有 tkinter / Tcl/Tk。
  echo 请重新运行安装程序，选 Modify，勾选 tcl/tk and IDLE。
  echo.
  pause
  exit /b 1
)

if not exist "%~dp0gui_slot2patch.py" (
  echo [错误] 找不到 gui_slot2patch.py，请勿单独拷贝 bat。
  pause
  exit /b 1
)

if not exist "%~dp0slot2patch_core.py" (
  echo [错误] 找不到 slot2patch_core.py。
  pause
  exit /b 1
)

if not exist "%~dp0PatchToolForGbaR3.exe" (
  if not exist "%~dp0PatchToolForGbaR3" (
    echo [提示] 本目录没有 PatchToolForGbaR3.exe。
    echo 请把 .exe 放在本目录，或用 MinGW 编译 PatchToolForGbaR3.c：
    echo   gcc PatchToolForGbaR3.c -o PatchToolForGbaR3.exe -O2 -std=c99 -Wall
    echo.
  )
)

echo 正在启动界面...
%PY% "%~dp0gui_slot2patch.py"
if errorlevel 1 (
  echo.
  echo 界面异常退出。
  pause
)

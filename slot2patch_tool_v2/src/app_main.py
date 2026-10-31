"""冻结程序入口：GUI，或以子命令运行后端（--run-lr / --run-core）。
差分格式与 PatchTool 作者：卧看微尘 (Wokann) https://github.com/Wokann/PatchToolForGbaR3
"""
import sys, os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

def _bundle_check():
    """冻结包自检：PatchTool 和 configs 是否落在各脚本用来找文件的目录。不读 ROM。"""
    try:
        import gui_lrscan
        import gui_slot2patch
        import slot2patch_core
        base = slot2patch_core.SCRIPT_DIR
        tool = base / "PatchToolForGbaR3.exe"
        cfg = base / "_gba" / "configs"
        n = len(list(cfg.glob("*.json"))) if cfg.is_dir() else 0
        dirs = [base, gui_lrscan.HERE, gui_slot2patch.SCRIPT_DIR]
        same = len({os.path.normcase(str(p)) for p in dirs}) == 1
        print(f"python={sys.version.split()[0]}")
        print(f"frozen={getattr(sys, 'frozen', False)}")
        print(f"base={base}")
        print(f"same_dir={same}")
        print(f"tool_exists={tool.is_file()}")
        print(f"config_json={n}")
        return 0 if tool.is_file() and n > 0 and same else 1
    except Exception as e:
        print(f"bundle_check_error={type(e).__name__}: {e}")
        return 1

def _main():
    for st in (sys.stdout, sys.stderr):
        try: st.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass
    if len(sys.argv) > 1 and sys.argv[1] == "--bundle-check":
        sys.exit(_bundle_check())
    if len(sys.argv) > 1 and sys.argv[1] == "--run-lr":
        import lr_scan
        sys.exit(lr_scan.main(sys.argv[2:]) or 0)
    if len(sys.argv) > 1 and sys.argv[1] == "--run-core":
        import slot2patch_core
        sys.exit(slot2patch_core.main(sys.argv[2:]) or 0)
    import tkinter
    if float(tkinter.TkVersion) < 8.6:
        print("Tk < 8.6, abort", file=sys.stderr); sys.exit(2)
    import gui_slot2patch
    gui_slot2patch.main()

if __name__ == "__main__":
    import multiprocessing; multiprocessing.freeze_support()
    _main()

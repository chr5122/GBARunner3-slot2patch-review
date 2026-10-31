"""冻结程序入口：GUI，或以子命令运行后端（--run-lr / --run-core）。
差分格式与 PatchTool 作者：卧看微尘 (Wokann) https://github.com/Wokann/PatchToolForGbaR3
"""
import sys, os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

def _bundle_check():
    """冻结包自检：PatchTool 和 configs 是否按脚本目录可见。不读 ROM，不初始化 Tk。"""
    import lr_scan
    import slot2patch_core
    base = slot2patch_core.SCRIPT_DIR
    tool = base / "PatchToolForGbaR3.exe"
    cfg = base / "_gba" / "configs"
    n = len(list(cfg.glob("*.json"))) if cfg.is_dir() else 0
    same = os.path.normcase(str(base)) == os.path.normcase(str(lr_scan.HERE))
    print(f"python={sys.version.split()[0]}")
    print(f"frozen={getattr(sys, 'frozen', False)}")
    print(f"base={base}")
    print(f"lr_here={lr_scan.HERE}")
    print(f"same_dir={same}")
    print(f"tool_exists={tool.is_file()}")
    print(f"config_json={n}")
    ok = tool.is_file() and n > 0 and same
    return 0 if ok else 1

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

"""冻结程序入口：GUI，或以子命令运行后端（--run-lr / --run-core）。
差分格式与 PatchTool 作者：卧看微尘 (Wokann) https://github.com/Wokann/PatchToolForGbaR3
"""
import sys, os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

def _main():
    for st in (sys.stdout, sys.stderr):
        try: st.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass
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

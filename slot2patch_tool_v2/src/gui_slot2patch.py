#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GBA slot2patch 打包工具（图形界面）

优先调用同目录 slot2patch_core.py（Windows / macOS / Linux 通用）；
若无 core 则回退 make_slot2patch.sh（macOS／Linux）。
差分来自卧看微尘 PatchToolForGbaR3。
不宣称任意 ROM 都支持；完整 GBR3 教程请征得卧看同意后再公开。
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import threading
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_SCRIPT = SCRIPT_DIR / "slot2patch_core.py"
MAKE_SCRIPT = SCRIPT_DIR / "make_slot2patch.sh"

CREDIT = "差分工具作者：卧看微尘（Wokann）· PatchToolForGbaR3"
LIMIT_NOTE = (
    "说明：原版与汉化 GameCode 须相同；差分块数过大（≥4096）会失败；"
    "不保证任意 ROM 实机能跑。完整 GBARunner3 教程请先征得卧看同意再公开。"
)


def main() -> None:
    # 无显示器／无 tkinter 时至少能语法检查与冒烟
    if os.environ.get("SLOT2PATCH_GUI_SMOKE") == "1":
        print("gui_slot2patch.py: smoke ok, SCRIPT_DIR=", SCRIPT_DIR)
        print("CORE_SCRIPT exists=", CORE_SCRIPT.is_file())
        print("MAKE_SCRIPT exists=", MAKE_SCRIPT.is_file())
        return

    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, scrolledtext, ttk
    except ImportError:
        print(
            "错误: 当前 Python 没有 tkinter。\n"
            "Windows: 从 python.org 安装，勾选 tcl/tk 与 pip；或用「修改」补装 tcl/tk。\n"
            "macOS: python.org 勾选 Tcl/Tk，或 brew install python-tk",
            file=sys.stderr,
        )
        sys.exit(1)

    class Slot2PatchApp(tk.Tk):
        def __init__(self) -> None:
            super().__init__()
            self.title("GBA slot2patch 打包工具")
            self.minsize(640, 520)
            self.geometry("720x580")
            import queue as _queue
            self._queue_mod = _queue
            self._q = _queue.Queue()
            self.after(100, self._pump)

            self.var_orig = tk.StringVar()
            self.var_cn = tk.StringVar()
            self.var_out = tk.StringVar()
            self.var_force = tk.BooleanVar(value=False)
            self.var_skip = tk.BooleanVar(value=False)
            self.var_export = tk.BooleanVar(value=False)
            self._work: Path | None = None

            self._proc: subprocess.Popen | None = None
            self._running = False
            self._last_zip: Path | None = None

            self._build_ui()
            self._check_deps()

        def _build_ui(self) -> None:
            pad = {"padx": 10, "pady": 4}
            frm = ttk.Frame(self, padding=12)
            frm.pack(fill=tk.BOTH, expand=True)

            ttk.Label(
                frm,
                text="把「原版 .gba + 汉化 .gba」打成 GBARunner3 用的 slot2patch ZIP",
                wraplength=680,
            ).grid(row=0, column=0, columnspan=3, sticky="w", **pad)

            ttk.Label(frm, text="日版／原版 .gba").grid(
                row=1, column=0, sticky="w", **pad
            )
            ttk.Entry(frm, textvariable=self.var_orig, width=56).grid(
                row=1, column=1, sticky="ew", **pad
            )
            ttk.Button(frm, text="选择…", command=self._pick_orig).grid(
                row=1, column=2, **pad
            )

            ttk.Label(frm, text="汉化／目标 .gba").grid(
                row=2, column=0, sticky="w", **pad
            )
            ttk.Entry(frm, textvariable=self.var_cn, width=56).grid(
                row=2, column=1, sticky="ew", **pad
            )
            ttk.Button(frm, text="选择…", command=self._pick_cn).grid(
                row=2, column=2, **pad
            )

            ttk.Label(frm, text="输出目录（可选）").grid(
                row=5, column=0, sticky="w", **pad
            )
            ttk.Entry(frm, textvariable=self.var_out, width=56).grid(
                row=5, column=1, sticky="ew", **pad
            )
            ttk.Button(frm, text="选择…", command=self._pick_out).grid(
                row=5, column=2, **pad
            )

            opt = ttk.Frame(frm)
            opt.grid(row=6, column=0, columnspan=3, sticky="w", **pad)
            ttk.Checkbutton(
                opt,
                text="强制原版 SHA（原版校验不过时仍继续）",
                variable=self.var_force,
            ).pack(side=tk.LEFT, padx=(0, 16))
            ttk.Checkbutton(
                opt,
                text="跳过还原核对（不推荐）",
                variable=self.var_skip,
            ).pack(side=tk.LEFT, padx=(0, 16))
            ttk.Checkbutton(
                opt,
                text="同时导出 BPS 和报告（含修复后 ROM，仅自测用）",
                variable=self.var_export,
            ).pack(side=tk.LEFT)

            btn_row = ttk.Frame(frm)
            btn_row.grid(row=7, column=0, columnspan=3, sticky="ew", **pad)
            self.btn_run = ttk.Button(btn_row, text="生成", command=self._on_run)
            self.btn_run.pack(side=tk.LEFT, padx=(0, 8))
            self.btn_open = ttk.Button(
                btn_row,
                text="打开所在文件夹",
                command=self._open_folder,
                state=tk.DISABLED,
            )
            self.btn_open.pack(side=tk.LEFT, padx=(0, 8))
            ttk.Button(btn_row, text="清空日志", command=self._clear_log).pack(
                side=tk.LEFT
            )

            self.result = tk.Label(frm, text="运行日志", anchor="w", justify=tk.LEFT, wraplength=680)
            self.result.grid(row=8, column=0, columnspan=3, sticky="ew", **pad)
            self._result_bg = self.result.cget("bg")
            log_font = ("Consolas", 10) if sys.platform == "win32" else ("Menlo", 11)
            self.log = scrolledtext.ScrolledText(
                frm, height=16, wrap=tk.WORD, state=tk.DISABLED, font=log_font
            )
            self.log.grid(row=9, column=0, columnspan=3, sticky="nsew", **pad)

            self.status = ttk.Label(frm, text=CREDIT, wraplength=680)
            self.status.grid(row=10, column=0, columnspan=3, sticky="w", **pad)

            ttk.Label(
                frm, text=LIMIT_NOTE, wraplength=680, foreground="#555"
            ).grid(row=11, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 4))

            frm.columnconfigure(1, weight=1)
            frm.rowconfigure(9, weight=1)

        def _backend(self) -> list[str] | None:
            """返回启动命令前缀（不含参数），优先 Python core。"""
            if getattr(sys, "frozen", False):
                return [sys.executable, "--run-core"]
            if CORE_SCRIPT.is_file():
                return [sys.executable, str(CORE_SCRIPT)]
            if MAKE_SCRIPT.is_file() and sys.platform != "win32":
                if not os.access(MAKE_SCRIPT, os.X_OK):
                    try:
                        MAKE_SCRIPT.chmod(MAKE_SCRIPT.stat().st_mode | 0o111)
                    except OSError:
                        pass
                return [str(MAKE_SCRIPT)]
            return None

        def _check_deps(self) -> None:
            backend = self._backend()
            if backend is None:
                self._append_log(
                    "错误: 找不到 slot2patch_core.py"
                    + ("（或 make_slot2patch.sh）" if sys.platform != "win32" else "")
                    + "，请与本界面放在同一目录。\n"
                )
                self.btn_run.configure(state=tk.DISABLED)
                return
            self._append_log(
                f"后端: {' '.join(backend)}\n"
            )
            tool_candidates = [
                SCRIPT_DIR / "PatchToolForGbaR3.exe",
                SCRIPT_DIR / "PatchToolForGbaR3",
                SCRIPT_DIR.parent / "PatchToolForGbaR3" / "PatchToolForGbaR3.exe",
                SCRIPT_DIR.parent / "PatchToolForGbaR3" / "PatchToolForGbaR3",
            ]
            if not any(t.is_file() for t in tool_candidates):
                self._append_log(
                    "提示: 本目录未找到 PatchToolForGbaR3"
                    + (".exe" if sys.platform == "win32" else "")
                    + "；生成时还会再找。Windows 请把 .exe 放在本目录，"
                    "或用 MinGW/MSVC 编译同目录 PatchToolForGbaR3.c。\n"
                )

        def _pick_orig(self) -> None:
            p = filedialog.askopenfilename(
                title="选择日版／原版 .gba",
                filetypes=[("GBA ROM", "*.gba *.GBA"), ("所有文件", "*.*")],
            )
            if p:
                self.var_orig.set(p)

        def _pick_cn(self) -> None:
            p = filedialog.askopenfilename(
                title="选择汉化／目标 .gba",
                filetypes=[("GBA ROM", "*.gba *.GBA"), ("所有文件", "*.*")],
            )
            if p:
                self.var_cn.set(p)

        def _pick_out(self) -> None:
            p = filedialog.askdirectory(title="选择输出目录")
            if p:
                self.var_out.set(p)

        def _clear_log(self) -> None:
            self.log.configure(state=tk.NORMAL)
            self.log.delete("1.0", tk.END)
            self.log.configure(state=tk.DISABLED)

        def _pump(self) -> None:
            try:
                while True:
                    f, a = self._q.get_nowait()
                    f(*a)
            except self._queue_mod.Empty:
                pass
            self.after(100, self._pump)

        def _append_log(self, text: str) -> None:
            self.log.configure(state=tk.NORMAL)
            self.log.insert(tk.END, text)
            self.log.see(tk.END)
            self.log.configure(state=tk.DISABLED)

        def _on_run(self) -> None:
            if self._running:
                return
            orig = self.var_orig.get().strip()
            cn = self.var_cn.get().strip()
            if not orig or not Path(orig).is_file():
                messagebox.showerror(
                    "缺少文件", "请先选择有效的「日版／原版 .gba」。"
                )
                return
            if not cn or not Path(cn).is_file():
                messagebox.showerror(
                    "缺少文件", "请先选择有效的「汉化／目标 .gba」。"
                )
                return
            # 生成前先自动深度扫描（后台跑，结果经队列回主线程，不卡界面）
            self._running = True
            self.btn_run.configure(state=tk.DISABLED)
            self._last_zip = None
            self.btn_open.configure(state=tk.DISABLED)
            self._clear_log()
            self.status.configure(text="生成前深度扫描中…（通常几秒）")
            self._show_result("正在深度扫描…（通常几秒）", "#fff1c2")
            self._append_log("==> 生成前深度扫描（GBR3 返回地址判断，通常几秒）…\n")
            import tempfile
            from gui_lrscan import _lr_prefix
            tmp = Path(tempfile.mkdtemp(prefix="lrscan_"))
            scmd = [*_lr_prefix(), "--rom", cn, "--scan", "--json", "--out", str(tmp), "--orig", orig]

            def work() -> None:
                code = -1
                tail: list = []
                try:
                    env = os.environ.copy()
                    env["PYTHONIOENCODING"] = "utf-8"
                    env["PYTHONUTF8"] = "1"
                    p = subprocess.Popen(scmd, cwd=str(SCRIPT_DIR), stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                         errors="replace", env=env)
                    assert p.stdout is not None
                    for line in p.stdout:
                        tail = (tail + [line])[-15:]
                    code = p.wait()
                except OSError as e:
                    tail.append(f"启动失败: {e}\n")
                self._q.put((self._after_scan, (orig, cn, tmp, code, tail)))

            threading.Thread(target=work, daemon=True).start()

        def _after_scan(self, orig: str, cn: str, tmp: Path, code: int, tail: list) -> None:
            import json as _json
            js = list(tmp.glob("*_LR扫描.json"))
            if code != 0 or not js:
                self._append_log("扫描失败：\n" + "".join(tail))
                shutil.rmtree(tmp, ignore_errors=True)
                if messagebox.askyesno("扫描失败", f"深度扫描失败（退出码 {code}），详情见日志。\n\n是否跳过扫描，直接生成？"):
                    self._generate(orig, cn)
                else:
                    self._idle("已取消")
                return
            items = _json.loads(js[0].read_text(encoding="utf-8"))
            shutil.rmtree(tmp, ignore_errors=True)
            cnt = {k: sum(1 for i in items if i["risk"] == k) for k in ("高", "中", "低", "已修")}
            summ = f"高 {cnt['高']} · 中 {cnt['中']} · 低 {cnt['低']} · 已修 {cnt['已修']}"
            self._append_log(f"扫描完成：{summ}\n")
            if cnt["高"] or cnt["中"]:
                import gui_lrscan
                dlg = gui_lrscan.ChooseDialog(self, items, summ)
                self.dlg = dlg
                dlg.update_idletasks()
                dlg.geometry(f"+{self.winfo_rootx() + 20}+{self.winfo_rooty() + 40}")
                dlg.grab_set()
                self.wait_window(dlg)
                self.dlg = None
                if dlg.choice == "fix":
                    self._append_log(f"选择修复 {len(dlg.ids)} 处：{','.join(map(str, dlg.ids))}\n\n")
                    self._fix_generate(orig, cn, dlg.ids)
                elif dlg.choice == "nofix":
                    self._append_log("选择不修复，直接生成。\n\n")
                    self._generate(orig, cn)
                else:
                    self._idle("已取消")
                    self._show_result("已取消，未生成任何文件。", "#eeeeee")
            else:
                self._append_log("没有高／中风险条目，直接生成。\n\n")
                self._generate(orig, cn)

        def _show_result(self, text: str, bg: str) -> None:
            self.result.configure(text=text, bg=bg, font=("TkDefaultFont", 14, "bold"), padx=8, pady=6)

        def _fix_generate(self, orig: str, cn: str, ids: list) -> None:
            from gui_lrscan import _lr_prefix
            out = self._new_work()
            cmd = [*_lr_prefix(), "--rom", cn, "--orig", orig, "--fix", ",".join(map(str, ids)),
                   "--out", out, "--slot2patch"]
            if self.var_force.get():
                cmd.append("--force-orig")
            if self.var_skip.get():
                cmd.append("--skip-verify")
            self._fixinfo = (out, len(ids))
            self._append_log("$ " + " ".join(shlex.quote(c) for c in cmd) + "\n\n")
            self._running = True
            self.btn_run.configure(state=tk.DISABLED)
            self.status.configure(text=f"正在修复 {len(ids)} 处并生成…")
            self._show_result(f"正在修复 {len(ids)} 处并生成 BPS／报告／slot2patch ZIP…", "#fff1c2")
            threading.Thread(target=self._run_worker, args=(cmd,), daemon=True).start()

        def _idle(self, text: str) -> None:
            self._running = False
            self.btn_run.configure(state=tk.NORMAL)
            self.status.configure(text=text)

        def _generate(self, orig: str, cn: str) -> None:
            backend = self._backend()
            if backend is None:
                messagebox.showerror(
                    "缺少脚本",
                    "找不到 slot2patch_core.py"
                    + (" 或 make_slot2patch.sh" if sys.platform != "win32" else ""),
                )
                self._idle("缺少脚本")
                return

            cmd = [*backend, "--orig", orig, "--cn", cn]
            cmd.extend(["--out", self._new_work()])
            if self.var_force.get():
                cmd.append("--force-orig")
            if self.var_skip.get():
                cmd.append("--skip-verify")

            self._append_log(
                "$ " + " ".join(shlex.quote(c) for c in cmd) + "\n\n"
            )
            self._running = True
            self.btn_run.configure(state=tk.DISABLED)
            self.status.configure(text="正在生成…")
            self._fixinfo = None
            self._show_result("正在生成 slot2patch ZIP…", "#fff1c2")

            threading.Thread(
                target=self._run_worker, args=(cmd,), daemon=True
            ).start()

        def _run_worker(self, cmd: list[str]) -> None:
            env = os.environ.copy()
            env["LANG"] = env.get("LANG") or "zh_CN.UTF-8"
            env["LC_ALL"] = env.get("LC_ALL") or env["LANG"]
            env["PYTHONIOENCODING"] = "utf-8"
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    cwd=str(SCRIPT_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,
                )
                assert self._proc.stdout is not None
                for line in self._proc.stdout:
                    self._q.put((self._append_log, (line,)))
                code = self._proc.wait()
            except OSError as e:
                self._q.put((self._append_log, (f"\n启动失败: {e}\n",)))
                code = -1
            finally:
                self._proc = None

            self._q.put((self._on_done, (code,)))

        def _final_dir(self) -> Path:
            out = self.var_out.get().strip()
            if out:
                return Path(out).expanduser()
            return Path(self.var_cn.get().strip()).expanduser().resolve().parent

        def _new_work(self) -> str:
            """本次生成的临时工作目录（只有它会被整体删除，绝不删用户原有文件）。"""
            import tempfile
            self._cleanup_work()
            self._work = Path(tempfile.mkdtemp(prefix="slot2patch_work_"))
            return str(self._work)

        def _cleanup_work(self) -> None:
            w = self._work
            self._work = None
            if w and w.name.startswith("slot2patch_work_") and w.is_dir():
                shutil.rmtree(w, ignore_errors=True)

        def _harvest(self) -> tuple:
            """把 ZIP（及勾选时的 BPS／报告／修复 ROM）移到输出目录，再删工作目录。"""
            w = self._work
            dest = self._final_dir()
            zip_path, extras = None, []
            if w:
                zs = sorted(w.glob("*_slot2patch.zip")) + sorted(w.glob("slot2patch/*_slot2patch.zip"))
                if zs:
                    dest.mkdir(parents=True, exist_ok=True)
                    zip_path = dest / zs[-1].name
                    shutil.move(str(zs[-1]), str(zip_path))
                if self.var_export.get():
                    for pat in ("*.bps", "*报告.md", "*_GBR3LR修复.gba"):
                        for f in w.glob(pat):
                            t = dest / f.name
                            shutil.move(str(f), str(t))
                            extras.append(t)
            self._cleanup_work()
            return zip_path, extras

        def _on_done(self, code: int) -> None:
            self._running = False
            self.btn_run.configure(state=tk.NORMAL)
            fixinfo = getattr(self, "_fixinfo", None)
            ok = code in (0, 2) if fixinfo else code == 0
            if ok:
                try:
                    zip_path, extras = self._harvest()
                except OSError as e:
                    self._cleanup_work()
                    zip_path, extras = None, []
                    self._append_log(f"移动输出文件失败: {e}\n")
                if zip_path:
                    self._last_zip = zip_path
                    self.btn_open.configure(state=tk.NORMAL)
                    head = f"✅ 已生成（修复了 {fixinfo[1]} 处）" if fixinfo else "✅ 已生成（未修复）"
                    lines = [head, f"ZIP：{zip_path}"]
                    if fixinfo and code == 2:
                        lines.append("⚠ 有条目没能自动修（勾选「同时导出 BPS 和报告」可看原因）。")
                    self._show_result("\n".join(lines), "#dcf5dc")
                    self.status.configure(text=f"成功 · {zip_path}")
                    self._append_log("\n—— 完成 ——\n" + "\n".join(lines) + "\n"
                                     + "".join(f"另导出：{e}\n" for e in extras)
                                     + "中间文件（stage／verify_apply.gba 等）已清理。\n")
                    return
                code = code or -2
            self._cleanup_work()
            self.status.configure(text=f"失败（退出码 {code}）· {CREDIT}")
            self._append_log(f"\n—— 失败（退出码 {code}）——\n临时文件已清理。\n")
            self._show_result(f"❌ 失败（退出码 {code}），请看下面日志。\n"
                              "常见原因：GameCode 不一致、差分块数过大、找不到 PatchTool。", "#ffd6d6")

        def _find_zip_in_log(self) -> Path | None:
            content = self.log.get("1.0", tk.END)
            candidates: list[str] = []
            for line in content.splitlines():
                line = line.strip()
                if ".zip" not in line.lower():
                    continue
                for part in line.replace("：", " ").replace(":", " ").split():
                    if part.lower().endswith(".zip"):
                        candidates.append(part.strip("\"'"))
            for c in reversed(candidates):
                p = Path(c).expanduser()
                if p.is_file():
                    return p.resolve()
                p2 = (SCRIPT_DIR / c).resolve()
                if p2.is_file():
                    return p2
            search_dirs = []
            out = self.var_out.get().strip()
            if out:
                search_dirs.append(Path(out))
            search_dirs.append(SCRIPT_DIR)
            newest: Path | None = None
            newest_mtime = 0.0
            for d in search_dirs:
                if not d.is_dir():
                    continue
                for z in d.glob("*_slot2patch.zip"):
                    try:
                        m = z.stat().st_mtime
                    except OSError:
                        continue
                    if m > newest_mtime:
                        newest_mtime = m
                        newest = z.resolve()
            return newest

        def _open_folder(self) -> None:
            if not self._last_zip or not self._last_zip.is_file():
                messagebox.showwarning("没有文件", "还没有成功生成的 ZIP。")
                return
            folder = str(self._last_zip.parent)
            try:
                if sys.platform == "darwin":
                    subprocess.run(
                        ["open", "-R", str(self._last_zip)], check=False
                    )
                elif sys.platform.startswith("linux"):
                    opener = shutil.which("xdg-open")
                    if opener:
                        subprocess.run([opener, folder], check=False)
                    else:
                        messagebox.showinfo("路径", folder)
                elif sys.platform == "win32":
                    # explorer /select, 可高亮文件；失败时退回打开目录
                    try:
                        subprocess.run(
                            ["explorer", "/select,", str(self._last_zip)],
                            check=False,
                        )
                    except OSError:
                        os.startfile(folder)  # type: ignore[attr-defined]
                else:
                    messagebox.showinfo("路径", str(self._last_zip))
            except OSError as e:
                messagebox.showerror("无法打开", str(e))

    app = Slot2PatchApp()
    app.mainloop()


if __name__ == "__main__":
    main()

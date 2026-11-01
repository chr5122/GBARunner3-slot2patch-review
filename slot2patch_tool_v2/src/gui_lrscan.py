"""深度扫描窗口（GBR3 LR／返回地址门禁）——由 gui_slot2patch.py 调用。

基于卧看微尘的 PatchToolForGbaR3 与 slot2patch 流程；本窗口只负责扫描、勾选、修复，
再把修复后的 ROM 交给原来的 slot2patch 流程。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import queue
import threading
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

HERE = Path(__file__).resolve().parent
LR_SCRIPT = HERE / "lr_scan.py"
RISK_COLOR = {"高": "#ffd6d6", "中": "#fff1c2", "低": "#e8f0ff", "已修": "#dcf5dc"}
RISK_NOTE = ("高＝在用、调用者在低 ROM、没换算（GBR3 上判断会失效）；中＝证据不全（间接调用／栈上取值／范围判断）需人工看；"
             "低＝只有高 ROM 调用者或找不到引用（死代码）；已修＝已有 0x02200000→0x08000000 换算。")


def _lr_prefix():
    if getattr(sys, "frozen", False):
        return [sys.executable, "--run-lr"]
    return [sys.executable, str(LR_SCRIPT)]


def _env():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _run(cmd, on_line, on_done):
    def work():
        code = -1
        try:
            p = subprocess.Popen(cmd, cwd=str(HERE), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace", bufsize=1, env=_env())
            for line in p.stdout:
                on_line(line)
            code = p.wait()
        except OSError as e:
            on_line(f"启动失败: {e}\n")
        on_done(code)
    threading.Thread(target=work, daemon=True).start()


class ScanWindow(tk.Toplevel):
    def __init__(self, app, orig: str, cn: str, out: str, force: bool, skip: bool, preset_json=None):
        super().__init__(app)
        self.app = app
        self.title("深度扫描 · LR／返回地址门禁")
        self.geometry("1080x640")
        self.orig, self.cn, self.force, self.skip = orig, cn, force, skip
        # 后台线程不直接碰 Tk；统一经队列交给主线程（macOS 上跨线程调用 Tk 会卡）
        self._q = queue.Queue()
        self._pump()
        self.out = out or str(Path(cn).with_name(Path(cn).stem + "_LR扫描"))
        self.items = []
        self.checked = set()
        self.busy = False
        self._build()
        if preset_json:
            # 主界面「生成」时已扫过：直接填入结果，不重扫
            self.tmp = Path(preset_json).parent
            self._log(f"（使用刚才的扫描结果：{preset_json}）\n")
            self._scan_done(0)
        else:
            self._scan()

    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.BOTH, expand=True)
        ttk.Label(top, text=RISK_NOTE, wraplength=1040, foreground="#444").pack(anchor="w")
        cols = ("sel", "id", "risk", "addr", "mode", "cap", "pat", "reason", "fix")
        mid = ttk.Frame(top)
        mid.pack(fill=tk.BOTH, expand=True, pady=6)
        self.tv = ttk.Treeview(mid, columns=cols, show="headings", height=14)
        heads = {"sel": "修", "id": "#", "risk": "风险", "addr": "地址", "mode": "态", "cap": "捕获",
                 "pat": "用法", "reason": "判断理由", "fix": "能否自动修"}
        widths = {"sel": 36, "id": 36, "risk": 48, "addr": 96, "mode": 52, "cap": 170, "pat": 130, "reason": 330, "fix": 200}
        for c in cols:
            self.tv.heading(c, text=heads[c])
            self.tv.column(c, width=widths[c], stretch=c in ("reason", "fix"), anchor="w")
        for r, col in RISK_COLOR.items():
            self.tv.tag_configure(r, background=col)
        sb = ttk.Scrollbar(mid, orient=tk.VERTICAL, command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tv.bind("<Button-1>", self._click)
        self.tv.bind("<space>", lambda e: self._toggle(self.tv.focus()))

        row = ttk.Frame(top)
        row.pack(fill=tk.X)
        self.btn_fix = ttk.Button(row, text="修复并生成", command=self._fix, state=tk.DISABLED)
        self.btn_fix.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(row, text="只勾高风险", command=lambda: self._select(lambda it: it["risk"] == "高")).pack(side=tk.LEFT, padx=4)
        ttk.Button(row, text="全不选", command=lambda: self._select(lambda it: False)).pack(side=tk.LEFT, padx=4)
        ttk.Button(row, text="重新扫描", command=self._scan).pack(side=tk.LEFT, padx=4)
        ttk.Button(row, text="打开输出目录", command=self._open_out).pack(side=tk.LEFT, padx=4)
        self.var_s2p = tk.BooleanVar(value=True)
        ttk.Checkbutton(row, text="修复后接着生成 slot2patch ZIP", variable=self.var_s2p).pack(side=tk.LEFT, padx=12)
        self.lbl = ttk.Label(top, text="")
        self.lbl.pack(anchor="w", pady=(4, 0))
        font = ("Consolas", 10) if sys.platform == "win32" else ("Menlo", 11)
        self.log = scrolledtext.ScrolledText(top, height=9, wrap=tk.WORD, font=font)
        self.log.pack(fill=tk.BOTH, expand=False)

    # ---- 日志
    def _pump(self):
        try:
            while True:
                f, a = self._q.get_nowait()
                f(*a)
        except queue.Empty:
            pass
        try:
            self.after(100, self._pump)
        except tk.TclError:
            pass

    def _call(self, f, *a):
        self._q.put((f, a))

    def _log(self, t):
        self._call(self._log_main, t)

    def _log_main(self, t):
        self.log.insert(tk.END, t)
        self.log.see(tk.END)

    # ---- 扫描
    def _scan(self):
        if self.busy:
            return
        self.busy = True
        self.btn_fix.configure(state=tk.DISABLED)
        self.tmp = Path(tempfile.mkdtemp(prefix="lrscan_"))
        cmd = [*_lr_prefix(), "--rom", self.cn, "--scan", "--json", "--out", str(self.tmp)]
        if self.orig:
            cmd += ["--orig", self.orig]
        self.lbl.configure(text="扫描中…（全 ROM 解码，通常几秒）")
        self._log("$ " + " ".join(cmd) + "\n")
        _run(cmd, self._log, lambda c: self._call(self._scan_done, c))

    def _scan_done(self, code):
        self.busy = False
        js = list(self.tmp.glob("*_LR扫描.json"))
        if code != 0 or not js:
            self.lbl.configure(text=f"扫描失败（退出码 {code}），看下面日志")
            return
        self.items = json.loads(js[0].read_text(encoding="utf-8"))
        self.checked = {it["id"] for it in self.items if it["risk"] == "高" and it.get("fixable")}
        self._fill()
        cnt = {k: sum(1 for i in self.items if i["risk"] == k) for k in ("高", "中", "低", "已修")}
        self.lbl.configure(text=f"高 {cnt['高']} · 中 {cnt['中']} · 低 {cnt['低']} · 已修 {cnt['已修']}　"
                                f"（点“修”一列勾选；高风险默认已勾；“需人工”的条目不能勾）")
        self.btn_fix.configure(state=tk.NORMAL)

    def _fill(self):
        self.tv.delete(*self.tv.get_children())
        for it in self.items:
            can = it.get("fixable")
            sel = ("☑" if it["id"] in self.checked else "☐") if can else "—"
            fix = "可以" if can else ("无需" if it["risk"] == "已修" else ("需人工：" + it.get("fix_note", "") if it.get("fix_note") else "-"))
            self.tv.insert("", tk.END, iid=str(it["id"]), tags=(it["risk"],), values=(
                sel, it["id"], it["risk"], it["addr"], it["mode"], it["capture"], it["pattern"], it["reason"], fix))

    def _click(self, ev):
        if self.tv.identify_region(ev.x, ev.y) != "cell":
            return
        if self.tv.identify_column(ev.x) == "#1":
            self._toggle(self.tv.identify_row(ev.y))

    def _toggle(self, iid):
        if not iid:
            return
        i = int(iid)
        it = next((x for x in self.items if x["id"] == i), None)
        if not it or not it.get("fixable"):
            return
        self.checked ^= {i}
        self.tv.set(iid, "sel", "☑" if i in self.checked else "☐")

    def _select(self, pred):
        self.checked = {it["id"] for it in self.items if it.get("fixable") and pred(it)}
        self._fill()

    # ---- 修复
    def _fix(self):
        if self.busy:
            return
        if not self.checked:
            messagebox.showinfo("没勾选", "没有勾选要修的条目。", parent=self)
            return
        s2p = self.var_s2p.get()
        if s2p and not self.orig:
            messagebox.showerror("缺少原版", "生成 slot2patch 需要主界面里的「日版／原版 .gba」。", parent=self)
            return
        ids = ",".join(str(i) for i in sorted(self.checked))
        cmd = [*_lr_prefix(), "--rom", self.cn, "--fix", ids, "--out", self.out]
        if self.orig:
            cmd += ["--orig", self.orig]
        if s2p:
            cmd.append("--slot2patch")
            if self.force: cmd.append("--force-orig")
            if self.skip: cmd.append("--skip-verify")
        self.busy = True
        self.btn_fix.configure(state=tk.DISABLED)
        self.lbl.configure(text="修复中…")
        self._log("\n$ " + " ".join(cmd) + "\n")
        _run(cmd, self._log, lambda c: self._call(self._fix_done, c))

    def _fix_done(self, code):
        self.busy = False
        self.btn_fix.configure(state=tk.NORMAL)
        if code in (0, 2):
            msg = f"完成。输出目录：\n{self.out}\n\n修复后 ROM 只在本地自测用，请分发 BPS／slot2patch ZIP。"
            if code == 2:
                msg += "\n\n有条目没能自动修，原因见报告。"
            self.lbl.configure(text="完成 · " + self.out)
            self.done_ok = True
            messagebox.showinfo("完成", msg, parent=self)
        else:
            self.lbl.configure(text=f"失败（退出码 {code}），看日志")
            messagebox.showerror("失败", "修复或打包失败，请看日志。", parent=self)

    def _open_out(self):
        p = self.out if Path(self.out).exists() else str(Path(self.cn).parent)
        if sys.platform == "win32":
            os.startfile(p)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", p])
        else:
            subprocess.Popen(["xdg-open", p])


class ChooseDialog(tk.Toplevel):
    """生成前的合并窗口：上面列表列出问题（可勾选，默认勾高风险），下面 修复／不修复（直接生成）／取消。
    关闭后 self.choice ∈ {"fix","nofix","cancel"}，self.ids 为勾选的条目编号。"""

    def __init__(self, app, items, summary):
        super().__init__(app)
        self.title("发现返回地址问题 · 选择要修复的条目")
        self.geometry("900x460")
        self.transient(app)
        self.items = items
        self.checked = {it["id"] for it in items if it["risk"] == "高" and it.get("fixable")}
        self.choice, self.ids = "cancel", []
        f = ttk.Frame(self, padding=10)
        f.pack(fill=tk.BOTH, expand=True)
        nh = sum(1 for i in items if i["risk"] == "高"); nm = sum(1 for i in items if i["risk"] == "中")
        ttk.Label(f, text=f"发现 {nh} 条高风险、{nm} 条中风险的返回地址判断，在 GBARunner3 上可能导致显示错误。"
                          f"勾选要修复的条目（高风险已默认勾选）。　{summary}",
                  wraplength=860, justify=tk.LEFT).pack(anchor="w")
        ttk.Label(f, text=RISK_NOTE, wraplength=860, foreground="#555").pack(anchor="w", pady=(2, 6))
        mid = ttk.Frame(f)
        mid.pack(fill=tk.BOTH, expand=True)
        cols = ("sel", "risk", "addr", "reason", "fix")
        self.tv = ttk.Treeview(mid, columns=cols, show="headings", height=10)
        for c, h, w in (("sel", "修", 40), ("risk", "风险", 50), ("addr", "地址", 100),
                        ("reason", "说明", 480), ("fix", "能否自动修", 200)):
            self.tv.heading(c, text=h)
            self.tv.column(c, width=w, stretch=c in ("reason", "fix"), anchor="w")
        for r, col in RISK_COLOR.items():
            self.tv.tag_configure(r, background=col)
        sb = ttk.Scrollbar(mid, orient=tk.VERTICAL, command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        order = {"高": 0, "中": 1, "低": 2, "已修": 3}
        for it in sorted(items, key=lambda x: (order.get(x["risk"], 9), x["id"])):
            can = it.get("fixable")
            sel = ("☑" if it["id"] in self.checked else "☐") if can else "—"
            fix = "可以" if can else ("无需" if it["risk"] == "已修" else ("需人工：" + it.get("fix_note", "") if it.get("fix_note") else "-"))
            self.tv.insert("", tk.END, iid=str(it["id"]), tags=(it["risk"],),
                           values=(sel, it["risk"], it["addr"], it["reason"], fix))
        self.tv.bind("<Button-1>", self._click)
        self.tv.bind("<space>", lambda e: self._toggle(self.tv.focus()))
        row = ttk.Frame(f)
        row.pack(fill=tk.X, pady=(8, 0))
        self.btns = {}
        for key, text in (("cancel", "取消"), ("nofix", "不修复（直接生成）"), ("fix", "修复")):
            b = ttk.Button(row, text=text, command=lambda k=key: self._pick(k))
            b.pack(side=tk.RIGHT, padx=4)
            self.btns[key] = b
        self.lbl = ttk.Label(row, text="")
        self.lbl.pack(side=tk.LEFT)
        self._upd()
        self.protocol("WM_DELETE_WINDOW", lambda: self._pick("cancel"))

    def _upd(self):
        self.lbl.configure(text=f"已勾选 {len(self.checked)} 条（点“修”列或按空格切换）")
        self.btns["fix"].configure(state=tk.NORMAL if self.checked else tk.DISABLED)

    def _click(self, ev):
        if self.tv.identify_region(ev.x, ev.y) == "cell" and self.tv.identify_column(ev.x) == "#1":
            self._toggle(self.tv.identify_row(ev.y))

    def _toggle(self, iid):
        if not iid:
            return
        i = int(iid)
        it = next((x for x in self.items if x["id"] == i), None)
        if not it or not it.get("fixable"):
            return
        self.checked ^= {i}
        self.tv.set(iid, "sel", "☑" if i in self.checked else "☐")
        self._upd()

    def _pick(self, k):
        self.choice, self.ids = k, sorted(self.checked)
        self.destroy()

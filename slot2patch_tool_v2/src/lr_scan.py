#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GBARunner3 LR／返回地址依赖 深度扫描 + 可选二进制修复。

背景：GBR3 把 GBA ROM 前 2MB 搬到 DS 内存 0x02200000 原生执行，低 ROM 里
BL 进来的函数看到的 LR 是 0x022xxxxx（Thumb 时 bit0=1）。汉化 hook 若拿 LR
（或栈上保存的返回地址）去比较写死的 0x08xxxxxx 调用者地址、或按它查表，
在 GBR3 上就不命中。修法：比较前若 LR∈[0x02200000,0x023FFFFF] 则 +0x05E00000；
在真机/mGBA 上不会触发。

纯 Python 3，无第三方依赖，不联网。只读扫描；修复只在副本上进行。
差分格式与 PatchTool 作者：卧看微尘 (Wokann)。本模块为附加的检查工具。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from dataclasses import dataclass, field, asdict
from pathlib import Path

ROM_BASE = 0x08000000
LOW_END = 0x08200000          # GBR3 原生执行的低 ROM 上限
GBR3_LO, GBR3_HI = 0x02200000, 0x02400000
NORM_ADD = 0x05E00000
TOOL_VERSION = "lr_scan 1.0 (2026-10-31)"

# ---------------------------------------------------------------- 基础

def u16(d, o):
    return d[o] | (d[o + 1] << 8)


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def a2o(a):
    return a - ROM_BASE


def o2a(o):
    return o + ROM_BASE


def h(v):
    return "0x%08X" % v


class Thumb:
    """极简 Thumb-1 解码（只覆盖本工具需要的类别）。"""

    @staticmethod
    def is_bl(d, o):
        if o + 4 > len(d):
            return False
        a, b = u16(d, o), u16(d, o + 2)
        return (a & 0xF800) == 0xF000 and (b & 0xF800) == 0xF800

    @staticmethod
    def bl_target(d, o):
        a, b = u16(d, o), u16(d, o + 2)
        off = ((a & 0x7FF) << 12) | ((b & 0x7FF) << 1)
        if off & 0x400000:
            off -= 0x800000
        return o2a(o) + 4 + off

    @staticmethod
    def decode(d, o):
        """返回 dict(kind=..., size=2/4, ...)。"""
        x = u16(d, o)
        pc = o2a(o)
        r = {"op": x, "size": 2, "addr": pc, "kind": "other"}
        if Thumb.is_bl(d, o):
            r.update(kind="bl", size=4, target=Thumb.bl_target(d, o))
            return r
        if (x & 0xF800) == 0xF000 or (x & 0xF800) == 0xF800 or (x & 0xF800) == 0xE800:
            r.update(kind="bad")
            return r
        if (x & 0xF800) == 0x4800:
            la = ((pc + 4) & ~3) + (x & 0xFF) * 4
            r.update(kind="ldrlit", rd=(x >> 8) & 7, lit_addr=la)
            return r
        if (x & 0xF800) == 0x9800:
            r.update(kind="ldrsp", rd=(x >> 8) & 7, imm=(x & 0xFF) * 4)
            return r
        if (x & 0xFF00) == 0x4600:
            rd = (x & 7) | ((x >> 4) & 8)
            rm = (x >> 3) & 0xF
            r.update(kind="movhi", rd=rd, rm=rm)
            if rd == 15:
                r["kind"] = "movpc"
            return r
        if (x & 0xFF00) == 0x4400:
            rd = (x & 7) | ((x >> 4) & 8)
            rm = (x >> 3) & 0xF
            r.update(kind="addhi", rd=rd, rm=rm)
            if rd == 15 or rm == 15:
                r["kind"] = "pcrel"
            return r
        if (x & 0xFF00) == 0x4500:
            rn = (x & 7) | ((x >> 4) & 8)
            rm = (x >> 3) & 0xF
            r.update(kind="cmpr", rn=rn, rm=rm, sets_flags=True)
            if rn == 15 or rm == 15:
                r["kind"] = "pcrel"
            return r
        if (x & 0xFFC0) == 0x4280:
            r.update(kind="cmpr", rn=x & 7, rm=(x >> 3) & 7, sets_flags=True)
            return r
        if (x & 0xF800) == 0x2800:
            r.update(kind="cmpi", rn=(x >> 8) & 7, imm=x & 0xFF, sets_flags=True)
            return r
        if (x & 0xFF80) == 0x4700:
            r.update(kind="bx", rm=(x >> 3) & 0xF, term=True)
            if (x & 0x80):
                r["kind"] = "blx_bad"
            return r
        if (x & 0xFF00) == 0xBD00:
            r.update(kind="poppc", term=True)
            return r
        if (x & 0xFE00) == 0xB400:
            r.update(kind="push")
            return r
        if (x & 0xFE00) == 0xBC00:
            r.update(kind="pop", regs=x & 0xFF)
            return r
        if (x & 0xF800) == 0xE000:
            off = x & 0x7FF
            if off & 0x400:
                off -= 0x800
            r.update(kind="b", target=pc + 4 + off * 2, term=True)
            return r
        if (x & 0xF000) == 0xD000:
            c = (x >> 8) & 0xF
            if c == 0xF:
                r.update(kind="svc")
                return r
            if c == 0xE:
                r.update(kind="bad")
                return r
            off = x & 0xFF
            if off & 0x80:
                off -= 0x100
            r.update(kind="bcc", cond=c, target=pc + 4 + off * 2, reads_flags=True)
            return r
        if (x & 0xF800) == 0xA000:
            r.update(kind="pcrel", adr=((pc + 4) & ~3) + (x & 0xFF) * 4, rd=(x >> 8) & 7)  # adr rd, #imm
            return r
        if (x & 0xF800) == 0x0800:
            r.update(kind="lsr", rd=x & 7, rm=(x >> 3) & 7, imm=(x >> 6) & 31, sets_flags=True)
            return r
        if (x & 0xFE00) == 0x1A00:
            r.update(kind="subr", rd=x & 7, rn=(x >> 3) & 7, rm=(x >> 6) & 7, sets_flags=True)
            return r
        if (x & 0xFE00) == 0x1800:
            r.update(kind="addr", rd=x & 7, rn=(x >> 3) & 7, rm=(x >> 6) & 7, sets_flags=True)
            return r
        if (x & 0xFFC0) == 0x0000:
            r.update(kind="movl", rd=x & 7, rm=(x >> 3) & 7, sets_flags=True)  # lsls rd,rm,#0
            return r
        if (x & 0xFFC0) == 0x1C00:
            r.update(kind="movl", rd=x & 7, rm=(x >> 3) & 7, sets_flags=True)  # adds rd,rn,#0
            return r
        if (x & 0xF800) == 0x6800:
            r.update(kind="ldrimm", rd=x & 7, rn=(x >> 3) & 7, imm=((x >> 6) & 31) * 4)
            return r
        if (x & 0xBF00) == 0xBF00 or x == 0xDEFE:
            r.update(kind="bad")
            return r
        # 其余数据处理：是否设标志
        if (x & 0xE000) == 0x0000 or (x & 0xE000) == 0x2000 or (x & 0xFC00) == 0x4000:
            r["sets_flags"] = True
            if (x & 0xFC00) == 0x4000:
                op = (x >> 6) & 0xF
                if op in (5, 6):  # adc/sbc read C
                    r["reads_flags"] = True
            if (x & 0xF800) == 0x2000:
                r["rd"] = (x >> 8) & 7
            elif (x & 0xE000) == 0x2000:
                r["rd"] = (x >> 8) & 7
        return r


def retaddr_like(d, v):
    """v 是否像 Thumb BL/BLX 的返回地址（奇数、前面紧挨 BL 或 bx/blx reg）。"""
    if not (v & 1) or v < ROM_BASE + 5 or v >= ROM_BASE + len(d):
        return False
    o = a2o(v & ~1)
    if Thumb.is_bl(d, o - 4):
        return True
    x = u16(d, o - 2)
    return (x & 0xFF07) == 0x4700  # bx/blx reg 之后（mov lr,pc; bx rX 形式）


# ---------------------------------------------------------------- 数据结构

@dataclass
class Item:
    id: int
    addr: int                  # 捕获指令地址
    mode: str                  # Thumb / ARM
    capture: str               # mov rX,lr / ldr rX,[sp,#n] / ...
    pattern: str               # 直接比较 / 查表 / 范围比较
    entry: int = 0
    refs: list = field(default_factory=list)
    callers: list = field(default_factory=list)   # 被比较的调用者返回地址
    tables: list = field(default_factory=list)
    normalized: bool = False
    risk: str = ""             # 高 / 中 / 低 / 已修
    reason: str = ""
    fixable: bool = False
    fix_note: str = ""
    region: str = ""           # 原版区/自定义区
    cap_reg: int = -1
    cap_kind: str = ""
    cap_imm: int = 0

    def to_json(self):
        dd = asdict(self)
        dd["addr"] = h(self.addr)
        dd["entry"] = h(self.entry) if self.entry else ""
        dd["callers"] = [h(c) for c in self.callers]
        dd["tables"] = [h(t) for t in self.tables]
        return dd


# ---------------------------------------------------------------- 扫描

class Scanner:
    def __init__(self, data: bytes, orig: bytes | None = None, log=print):
        self.d = data
        self.orig = orig
        self.log = log
        self.n = len(data)

    # 是否与原版不同（自定义区）
    def custom_at(self, o):
        if self.orig is None:
            return None
        if o >= len(self.orig):
            return True
        return self.d[o:o + 16] != self.orig[o:o + 16]

    def table_retaddrs(self, ptr):
        """ptr 指向的表里收集像返回地址的字。"""
        o = a2o(ptr & ~3)
        if o < 0 or o + 4 > self.n:
            return []
        out = []
        miss = 0
        for i in range(256):
            if o + 4 * i + 4 > self.n:
                break
            v = u32(self.d, o + 4 * i)
            if retaddr_like(self.d, v):
                out.append(v)
                miss = 0
            else:
                miss += 1
                if miss > 3 and not out:
                    break
                if miss > 6:
                    break
        return out

    def analyze_window(self, o_cap, rX, max_ins=40, skip_first=True, depth=0):
        """从捕获后线性跟踪，收集证据。depth=1 时为被调函数（可越过返回继续线性看）。"""
        d = self.d
        taint = {rX} if isinstance(rX, int) else set(rX)
        sub = []
        regval = {}
        lits = []
        callers = []
        tables = []
        pattern = set()
        norm = False
        o = o_cap
        first = skip_first
        for _ in range(max_ins):
            if o + 2 > self.n:
                break
            ins = Thumb.decode(d, o)
            k = ins["kind"]
            if first:
                first = False
                o += ins["size"]
                continue
            if k == "bad":
                break
            if k == "ldrlit":
                la = ins["lit_addr"]
                if a2o(la) + 4 <= self.n:
                    v = u32(d, a2o(la))
                    regval[ins["rd"]] = v
                    lits.append(v)
                    taint.discard(ins["rd"])
            elif k == "pcrel" and "adr" in ins:
                regval[ins["rd"]] = ins["adr"]
                taint.discard(ins["rd"])
            elif k == "ldrimm":
                rn = ins["rn"]
                if isinstance(regval.get(rn), int) and ROM_BASE <= regval[rn] < ROM_BASE + self.n:
                    # ldr r3,[r1]  r1=表 → r3 是表项
                    regval[ins["rd"]] = ("tbl", regval[rn])
                else:
                    regval.pop(ins["rd"], None)
                taint.discard(ins["rd"])
            elif k in ("movhi", "movl"):
                if ins["rm"] in taint:
                    taint.add(ins["rd"])
                else:
                    taint.discard(ins["rd"])
                    if ins["rm"] in regval:
                        regval[ins["rd"]] = regval[ins["rm"]]
            elif k == "cmpr":
                a, b = ins["rn"], ins["rm"]
                other = b if a in taint else (a if b in taint else None)
                if other is not None and other in regval:
                    v = regval[other]
                    if isinstance(v, tuple):
                        tables.append(v[1])
                        pattern.add("查表比较")
                    elif ROM_BASE <= v < ROM_BASE + self.n:
                        callers.append(v)
                        pattern.add("直接比较")
            elif k == "lsr":
                if ins["rm"] in taint and ins["imm"] >= 20:
                    pattern.add("范围比较?")
                    taint.add(("shr", ins["rd"]))
                regval.pop(ins["rd"], None)
            elif k == "cmpi":
                if ("shr", ins["rn"]) in taint and ins["imm"] in (0x08, 0x04, 0x10, 0x40, 0x41, 0x20, 0x80, 0x81, 1, 2):
                    pattern.discard("范围比较?")
                    pattern.add("范围比较")
            elif k == "bl":
                # 被捕获值作为参数传入子函数：看已加载的表指针
                if taint & {0, 1, 2, 3} and depth == 0:
                    callee = ins["target"]
                    co = a2o(callee)
                    if 0 <= co < self.n - 2:
                        cx = Thumb.decode(d, co)
                        if cx["kind"] == "bx" and isinstance(regval.get(cx["rm"]), int) and (regval[cx["rm"]] & 1):
                            callee = regval[cx["rm"]] & ~1
                            co = a2o(callee)
                        if 0 <= co < self.n - 2:
                            sw = self.analyze_window(co, taint & {0, 1, 2, 3}, max_ins=96, skip_first=False, depth=1)
                            if sw["pattern"] or sw["norm"]:
                                sub.append(sw)
                                pattern |= {p_ + "(子函数 %s)" % h(callee) for p_ in sw["pattern"]}
                                callers.extend(sw["callers"]); tables.extend(sw["tables"])
                                norm = norm or sw["norm"]
                    for r, v in list(regval.items()):
                        if isinstance(v, int) and v >= LOW_END and v < ROM_BASE + self.n:
                            t = self.table_retaddrs(v)
                            if t:
                                tables.append(v)
                                pattern.add("传参查表")
                regval = {}
                taint = {t for t in taint if t not in (0, 1, 2, 3)}
            elif k in ("subr", "addr"):
                if ins["rn"] in taint or ins["rm"] in taint:
                    for r in (ins["rn"], ins["rm"]):
                        if regval.get(r) in (GBR3_LO, NORM_ADD):
                            norm = True
                regval.pop(ins["rd"], None)
                taint.discard(ins["rd"])
            elif "rd" in ins:
                regval.pop(ins["rd"], None)
                taint.discard(ins["rd"])
            if ins.get("term") and depth == 0:
                break
            if not taint:
                break
            o += ins["size"]
        # 表里的返回地址
        tcallers = []
        for t in tables:
            tcallers.extend(self.table_retaddrs(t))
        allc = sorted(set(callers + tcallers))
        return {
            "pattern": pattern,
            "callers": allc,
            "tables": sorted(set(tables)),
            "norm": norm,
            "lits": lits,
        }

    def find_captures(self):
        d = self.d
        n = self.n
        caps = []
        # Thumb mov rX, lr ：字节 (0x70-0x77|0xF0-0xF7), 0x46
        for o in range(0, n - 2, 2):
            b1 = d[o + 1]
            if b1 == 0x46:
                b0 = d[o]
                if (b0 & 0x78) == 0x70:
                    rd = (b0 & 7) | ((b0 >> 4) & 8)
                    if rd not in (13, 14, 15):
                        caps.append((o, rd, "mov", 0))
            elif b1 & 0xF8 == 0x98:
                caps.append((o, b1 & 7, "ldrsp", d[o] * 4))
        return caps

    def find_arm(self):
        """ARM 态 mov rX, lr（cond=AL）后 16 条内有 ROM 常量比较。"""
        d = self.d
        out = []
        for o in range(0, self.n - 4, 4):
            if d[o + 3] != 0xE1 or d[o] != 0x0E or d[o + 2] != 0xA0:
                continue
            w = u32(d, o)
            if (w & 0xFFFF0FFF) != 0xE1A0000E:
                continue
            rd = (w >> 12) & 0xF
            regval = {}
            callers = []
            for i in range(1, 17):
                q = o + 4 * i
                if q + 4 > self.n:
                    break
                x = u32(d, q)
                if (x & 0xFFFF0000) == 0xE59F0000:
                    la = q + 8 + (x & 0xFFF)
                    if la + 4 <= self.n:
                        regval[(x >> 12) & 0xF] = u32(d, la)
                elif (x & 0x0FF0F000) == 0x01500000:
                    rn, rm = (x >> 16) & 0xF, x & 0xF
                    other = rm if rn == rd else (rn if rm == rd else None)
                    if other is not None and other in regval:
                        v = regval[other]
                        if ROM_BASE <= v < ROM_BASE + self.n:
                            callers.append(v)
                elif (x & 0x0E000000) == 0x0A000000 and (x >> 28) == 0xE:
                    break
                elif (x & 0x0FFFFFF0) == 0x012FFF10:
                    break
            if callers:
                out.append((o, rd, sorted(set(callers))))
        return out

    def references(self, targets):
        """直接 BL 与 4 字节指针（Thumb 奇地址）对 targets 的引用。"""
        d = self.d
        tset = set(targets)
        res = {t: [] for t in targets}
        lo_t = min(targets) if targets else 0
        hi_t = max(targets) if targets else 0
        # BL：前半 0xF000-0xF7FF
        for o in range(0, self.n - 4, 2):
            if (d[o + 1] & 0xF8) == 0xF0 and (d[o + 3] & 0xF8) == 0xF8:
                t = Thumb.bl_target(d, o)
                if t in tset:
                    res[t].append(("BL", o2a(o)))
        # 指针字
        for t in targets:
            pat = struct.pack("<I", t | 1)
            s = 0
            while True:
                i = d.find(pat, s)
                if i < 0:
                    break
                if i % 4 == 0:
                    site = self.ptr_jump_site(i)
                    if site is not None:
                        res[t].append(("指针跳转", site))
                    else:
                        res[t].append(("指针", o2a(i)))
                s = i + 1
        return res

    def ptr_jump_site(self, lit_off):
        """找 ldr rN,[pc,#] 读这个字面量、随后 4 条内 bx rN / mov pc,rN / bl 到 bx rN 小桩 的位置。"""
        d = self.d
        lo = max(0, lit_off - 1024) & ~1
        for o in range(lo, lit_off, 2):
            x = u16(d, o)
            if (x & 0xF800) != 0x4800:
                continue
            if ((o + 4) & ~3) + (x & 0xFF) * 4 != lit_off:
                continue
            rn = (x >> 8) & 7
            q = o + 2
            saw_str = False
            for _ in range(5):
                if q + 4 > self.n:
                    break
                y = u16(d, q)
                if (y & 0xFF87) == 0x4700 and ((y >> 3) & 0xF) == rn:
                    return o2a(q)
                if (y & 0xFF87) == 0x4687 and ((y >> 3) & 0xF) == rn:
                    return o2a(q)
                if (y & 0xF800) == 0x9000 and ((y >> 8) & 7) == rn:
                    saw_str = True  # str rN,[sp,#k] —— 远跳桩
                if (y & 0xFF00) == 0xBD00 and saw_str:
                    return o2a(q)
                if (d[q + 1] & 0xF8) == 0xF0 and (d[q + 3] & 0xF8) == 0xF8:
                    to = a2o(Thumb.bl_target(d, q))
                    if 0 <= to < self.n - 2:
                        z = u16(d, to)
                        if (z & 0xFF87) == 0x4700 and ((z >> 3) & 0xF) == rn:
                            return o2a(q)
                    break
                if Thumb.decode(d, q).get("term"):
                    break
                q += 2
        return None

    def stack_slot_kind(self, o, imm):
        """往回最多 12 条找 push/sub sp，判断 [sp,#imm] 是自己保存的 LR 还是调用者栈参数。"""
        d = self.d
        frame = 0
        lr_slot = None
        p = o
        for _ in range(12):
            p -= 2
            if p < 0:
                break
            x = u16(d, p)
            if (x & 0xFF80) == 0xB080:
                frame += (x & 0x7F) * 4
            elif (x & 0xFE00) == 0xB400:
                n = bin(x & 0xFF).count("1") + (1 if x & 0x100 else 0)
                if x & 0x100:
                    lr_slot = frame + (n - 1) * 4
                frame += n * 4
                break
            elif Thumb.decode(d, p).get("term"):
                return "未知栈布局，疑似返回地址"
        else:
            return "未知栈布局，疑似返回地址"
        if lr_slot is not None and imm == lr_slot:
            return "本函数保存的 LR"
        if imm >= frame:
            return "调用者栈上传入的值，可能是上层的 LR"
        return "栈上局部值，疑似返回地址"

    def scan(self):
        d = self.d
        items = []
        self.log("扫描 Thumb 捕获点 …")
        caps = self.find_captures()
        self.log(f"  候选捕获点 {len(caps)} 个，逐个分析 …")
        seen = set()
        for o, rd, kind, imm in caps:
            if rd > 7 and kind == "mov":
                # 高寄存器也跟踪（例如 mov ip, lr）
                pass
            w = self.analyze_window(o, rd)
            pat = w["pattern"]
            if kind == "ldrsp":
                # 栈上读值：只有出现返回地址样式常量比较/查表时才算
                if not (w["callers"] and any(retaddr_like(d, c) for c in w["callers"])) and not w["norm"]:
                    continue
                if not pat:
                    pat = {"已换算(比较在后续函数)"}
            else:
                if not pat and not w["norm"]:
                    continue
                if not pat and w["norm"]:
                    pat = {"已换算(比较在后续函数)"}
                if pat == {"范围比较?"} and not w["norm"]:
                    continue
            if o in seen:
                continue
            seen.add(o)
            capdesc = "mov r%d, lr" % rd
            if kind == "ldrsp":
                capdesc = "ldr r%d, [sp, #%d]（%s）" % (rd, imm, self.stack_slot_kind(o, imm))
            it = Item(
                id=0, addr=o2a(o), mode="Thumb",
                capture=capdesc,
                pattern="、".join(sorted(pat)),
                callers=w["callers"], tables=w["tables"], normalized=w["norm"],
                cap_reg=rd, cap_kind=kind, cap_imm=imm,
            )
            items.append(it)
        self.log("扫描 ARM 态 …")
        for o, rd, callers in self.find_arm():
            items.append(Item(id=0, addr=o2a(o), mode="ARM", capture="mov r%d, lr" % rd,
                              pattern="直接比较", callers=callers, cap_reg=rd, cap_kind="arm"))
        # 去掉明显非调用者比较：若 callers 全是非返回地址而且无表 → 保留但说明
        # 入口与引用
        self.log(f"  命中 {len(items)} 处，查引用（BL／指针）…")
        ent_map = {}
        for it in items:
            o = a2o(it.addr)
            cands = [it.addr]
            step = 2 if it.mode == "Thumb" else 4
            p = o
            for _ in range(12):
                p -= step
                if p < 0:
                    break
                if it.mode == "Thumb":
                    x = Thumb.decode(d, p)
                    if x.get("term") or x["kind"] in ("bad", "bl"):
                        break
                cands.append(o2a(p))
            ent_map[it.addr] = cands
        alltargets = sorted({c for v in ent_map.values() for c in v})
        refs = self.references(alltargets) if alltargets else {}
        for it in items:
            best = None
            rr = []
            for c in ent_map[it.addr]:
                if refs.get(c):
                    rr.extend((k, a, c) for k, a in refs[c])
                    if best is None:
                        best = c
            it.entry = best or 0
            it.refs = ["%s@%s→%s" % (k, h(a), h(c)) for k, a, c in rr[:12]]
            if it.mode == "Thumb" and self.custom_at(a2o(it.addr)) is not None:
                it.region = "自定义区" if self.custom_at(a2o(it.addr)) else "原版区"
            else:
                it.region = "高ROM" if it.addr >= LOW_END else "低ROM"
        # 分级
        for it in items:
            low = [c for c in it.callers if c < LOW_END]
            has_ref = bool(it.refs)
            ptr_only = has_ref and all(r.startswith("指针") and not r.startswith("指针跳转") for r in it.refs)
            if it.normalized:
                it.risk, it.reason = "已修", "比较前已有 0x02200000/0x05E00000 换算"
            elif not has_ref:
                it.risk = "低"
                it.reason = "全 ROM 找不到 BL 或指针引用，判为死代码（若存在运行时算出的间接调用则可能误判）"
                if low:
                    it.reason += "；注意：调用者在低 ROM 且未换算"
            elif low and "范围比较" not in it.pattern:
                if ptr_only or it.mode == "ARM" or it.cap_kind == "ldrsp":
                    it.risk = "中"
                    it.reason = "调用者在低 ROM 且未换算；但" + (
                        "只有指针引用（间接调用）" if ptr_only else
                        ("ARM 态，模式可能不完整" if it.mode == "ARM" else "返回地址取自栈，需确认栈布局"))
                else:
                    it.risk, it.reason = "高", "在用（有 BL／指针跳转调用），调用者在低 ROM <0x08200000，未换算 → GBR3 上不命中"
            elif "范围比较" in it.pattern:
                it.risk, it.reason = "中", "对返回地址做范围判断（GBR3 上 LR=0x022xxxxx 会落在范围外），需人工确认含义"
            elif it.callers:
                it.risk, it.reason = "低", "被比较的调用者都在高 ROM，GBR3 上地址不变"
            else:
                it.risk, it.reason = "中", "捕获了 LR 但比较模式不完整（未识别出常量或表）"
        items.sort(key=lambda i: ({"高": 0, "中": 1, "已修": 3, "低": 2}[i.risk], i.addr))
        for i, it in enumerate(items, 1):
            it.id = i
        return items


# ---------------------------------------------------------------- 修复

SAVE_RANGES = [(0x0E000000, 0x0E010000), (0x0D000000, 0x0E000000), (0x09FE0000, 0x0A000000)]


class FixError(Exception):
    pass


class Fixer:
    def __init__(self, data: bytes, log=print):
        self.d = bytearray(data)
        self.orig = bytes(data)
        self.log = log
        self.free_ptr = None
        self.free_end = None
        self.used_lit_slots = set()

    # 找空白区（0xFF 优先，其次 0x00），按 ROM 末尾往前
    def find_free(self, need=0x800):
        d = self.orig
        n = len(d)
        for fill in (0xFF, 0x00):
            run_end = None
            o = n - 4
            while o >= 0x200000:
                if d[o] == fill and d[o + 1] == fill and d[o + 2] == fill and d[o + 3] == fill:
                    if run_end is None:
                        run_end = o + 4
                else:
                    if run_end is not None and run_end - (o + 4) >= need + 0x40:
                        start = (o + 4 + 0x20 + 0xF) & ~0xF  # 前面留 32 字节保护
                        return start, run_end - 0x20, fill
                    run_end = None
                o -= 4
        return None

    def alloc(self, size):
        if self.free_ptr is None:
            f = self.find_free()
            if not f:
                raise FixError("ROM 内找不到足够的 0xFF/0x00 空白区放跳板")
            self.free_ptr, self.free_end, fill = f
            self.log(f"  跳板区：{h(o2a(self.free_ptr))} 起（原内容 0x{fill:02X}）")
        a = (self.free_ptr + 3) & ~3
        if a + size > self.free_end:
            raise FixError("空白区不够")
        self.free_ptr = a + size
        return a

    def internal_targets(self, start, end):
        """有没有分支跳进 (start, end) 内部。"""
        d = self.orig
        lo = max(0, start - 0x1000)
        hi = min(len(d) - 4, end + 0x1000)
        bad = []
        for o in range(lo, hi, 2):
            x = Thumb.decode(d, o)
            t = x.get("target")
            if t is not None and x["kind"] in ("b", "bcc", "bl"):
                to = a2o(t)
                if start < to < end:
                    bad.append(o2a(o))
        return bad

    def lit_shared(self, slot, except_o):
        d = self.orig
        for o in range(max(0, slot - 1024), slot, 2):
            if o == except_o:
                continue
            x = u16(d, o)
            if (x & 0xF800) == 0x4800 and ((o2a(o) + 4) & ~3) + (x & 0xFF) * 4 == o2a(slot):
                return True
        for o in range(max(0, (slot - 4096) & ~3), slot, 4):
            x = u32(d, o)
            if (x & 0x0F7F0000) == 0x051F0000 and o + 8 + (x & 0xFFF) == slot:
                return True
        return False

    def flags_dead_after(self, o, limit=64):
        """从 o 起线性看：在读标志前就被重新设置 → True。"""
        d = self.orig
        for _ in range(limit):
            x = Thumb.decode(d, o)
            if x.get("reads_flags"):
                return False
            if x.get("sets_flags"):
                return True
            if x["kind"] in ("bl", "bx", "poppc", "b", "bad", "movpc", "pcrel", "svc"):
                return x["kind"] in ("bl", "bx", "poppc")  # 跨调用/返回标志不保留
            o += x["size"]
        return False

    def touches_save(self, o):
        d = self.orig
        # 只看 ±0x100 内 ldr rX,[pc,#] 真正读取的字面量（避免把指令字节误当地址）
        for q in range(max(0, o - 0x100), min(len(d) - 2, o + 0x100), 2):
            x = u16(d, q)
            if (x & 0xF800) != 0x4800:
                continue
            la = ((q + 4) & ~3) + (x & 0xFF) * 4
            if la + 4 > len(d):
                continue
            v = u32(d, la)
            for lo, hi in SAVE_RANGES:
                if lo <= v < hi:
                    return True
        return False

    def plan(self, it: Item):
        """检查能否安全自动修复，返回方案或抛 FixError。"""
        if it.mode != "Thumb":
            raise FixError("ARM 态，暂不自动修")
        if it.normalized:
            raise FixError("已带换算，无需修")
        rX = it.cap_reg
        if rX > 7:
            raise FixError("捕获到高寄存器 r%d，需人工" % rX)
        A = a2o(it.addr)
        if self.touches_save(A):
            raise FixError("附近出现存档区地址（0x0E/0x0D/0x09FE），为免碰存档逻辑不自动修")
        d = self.orig
        # 收集覆盖指令
        def collect(min_bytes):
            ins = []
            o = A
            while o - A < min_bytes:
                x = Thumb.decode(d, o)
                ins.append(x)
                o += x["size"]
                if x.get("term") and o - A < min_bytes:
                    return None
            return ins
        variants = []
        # 方案1：4 字节 + 复用被搬走 ldr 的字面量槽
        ins4 = collect(4)
        if ins4:
            for x in ins4[1:]:
                if x["kind"] == "ldrlit":
                    slot = a2o(x["lit_addr"])
                    base = (o2a(A) + 4) & ~3
                    if slot >= a2o(base) and slot - a2o(base) <= 1020 and not self.lit_shared(slot, a2o(x["addr"])) and slot not in self.used_lit_slots:
                        variants.append(("slot", ins4, slot))
        # 方案2：内联字面量
        lit_off = ((A + 4 + 3) & ~3)
        need = lit_off + 4 - A
        insN = collect(need)
        if insN:
            variants.append(("inline", insN, lit_off))
        if not variants:
            raise FixError("覆盖区遇到返回/跳转，空间不够搬迁")
        errs = []
        for kind, ins, slot in variants:
            end = ins[-1]["addr"] + ins[-1]["size"]
            try:
                for x in ins[1:]:
                    if x["kind"] in ("pcrel", "movpc", "bad", "blx_bad", "svc"):
                        raise FixError("覆盖区含 PC 相关/特殊指令 %04X" % x["op"])
                    if x["kind"] == "bx" and x["rm"] == 15:
                        raise FixError("覆盖区含 bx pc")
                    if x["kind"] in ("b", "bcc"):
                        if A <= a2o(x["target"]) < a2o(end):
                            raise FixError("覆盖区内的分支跳回覆盖区")
                    if x["kind"] == "ldrlit":
                        la = a2o(x["lit_addr"])
                        if A <= la < a2o(end):
                            raise FixError("字面量落在覆盖区内")
                    if x["kind"] == "movhi" and x["rm"] == 15:
                        raise FixError("读 PC")
                if kind == "inline" and slot + 4 > a2o(end):
                    raise FixError("内联字面量超出覆盖区")
                bad = self.internal_targets(A, a2o(end))
                if bad:
                    raise FixError("有分支跳进覆盖区内部：" + ",".join(h(b) for b in bad[:3]))
                return {"kind": kind, "ins": ins, "slot": slot, "end": end, "A": A}
            except FixError as e:
                errs.append(str(e))
        raise FixError("；".join(errs))

    # ---- 编码
    @staticmethod
    def t_bl(src, dst):
        off = dst - (src + 4)
        if not (-0x400000 <= off < 0x400000):
            raise FixError("BL 超出 ±4MB")
        off >>= 1
        return struct.pack("<HH", 0xF000 | ((off >> 11) & 0x7FF), 0xF800 | (off & 0x7FF))

    def build_tramp(self, it: Item, p, use_arm: bool):
        rX = it.cap_reg
        scratch = [r for r in range(8) if r != rX][:2]
        c, s = scratch
        code = bytearray()
        lits = []          # (pos_of_ldr, value, rd)
        fixups = []

        def T(x):
            code.extend(struct.pack("<H", x))

        def ldr_lit(rd, value):
            lits.append((len(code), value, rd))
            T(0x4800 | (rd << 8))

        def far_jump(target_thumb):
            T(0xB081)            # sub sp,#4
            T(0xB401)            # push {r0}
            ldr_lit(0, target_thumb | 1)
            T(0x9001)            # str r0,[sp,#4]
            T(0xBC01)            # pop {r0}
            T(0xBD00)            # pop {pc}

        if use_arm:
            # ARM 段：保存标志，按条件换算，恢复标志
            assert len(code) % 4 == 0
            W = lambda w: code.extend(struct.pack("<I", w))
            W(0xE92D0000 | (1 << c) | (1 << s))           # stmfd sp!,{c,s}
            W(0xE10F0000 | (c << 12))                     # mrs c,cpsr
            if it.cap_kind == "mov":
                W(0xE1A0000E | (rX << 12))                # mov rX,lr
            else:
                W(0xE59D0000 | (rX << 12) | (it.cap_imm + 8))  # ldr rX,[sp,#n+8]
            W(0xE2400622 | (rX << 16) | (s << 12))        # sub s,rX,#0x02200000
            W(0xE3500602 | (s << 16))                     # cmp s,#0x00200000
            W(0x3280065E | (rX << 16) | (rX << 12))       # addlo rX,rX,#0x05E00000
            W(0xE128F000 | c)                             # msr cpsr_f,c
            W(0xE28F0001 | (s << 12))                     # add s,pc,#1 → 下一条后的 Thumb（pc=本条+8）
            W(0xE12FFF10 | s)                             # bx s
            T(0xBC00 | (1 << c) | (1 << s))               # pop {c,s}（Thumb）
        else:
            # Thumb 段（标志已确认在后面被重新设置）
            if it.cap_kind == "mov":
                T(0x4670 | rX)                            # mov rX,lr
            else:
                T(0x9800 | (rX << 8) | (it.cap_imm // 4))  # ldr rX,[sp,#n]
            T(0xB400 | (1 << s))                          # push {s}
            ldr_lit(s, GBR3_LO)
            T(0x1A00 | ((s) << 6) | (rX << 3) | s)        # subs s,rX,s
            T(0x0D40 | (s << 3) | s)                      # lsrs s,s,#21
            T(0xD101)                                     # bne +2 条
            ldr_lit(s, NORM_ADD)
            T(0x1800 | (s << 6) | (rX << 3) | rX)         # adds rX,rX,s
            T(0xBC00 | (1 << s))                          # pop {s}
        # 搬迁其余指令
        ins = p["ins"]
        ended = False
        for x in ins[1:]:
            k = x["kind"]
            if k == "ldrlit":
                ldr_lit(x["rd"], u32(self.orig, a2o(x["lit_addr"])))
            elif k == "b":
                far_jump(x["target"]); ended = True
            elif k == "bcc":
                inv = x["cond"] ^ 1
                # b<inv> 跳过后面 6 条（12 字节）的远跳：目标 = 本条+2+12 = 本条+4+imm*2 → imm=5
                T(0xD000 | (inv << 8) | 5)
                far_jump(x["target"])
            elif k == "bl":
                fixups.append((len(code), x["target"]))
                code.extend(b"\0\0\0\0")
            else:
                T(x["op"])
                if x.get("term"):
                    ended = True
        if not ended:
            far_jump(p["end"])
        # 字面量池
        while len(code) % 4:
            T(0x46C0)
        pool = {}
        tail = bytearray()
        return code, lits, fixups, tail

    def apply(self, it: Item):
        p = self.plan(it)
        A = p["A"]
        use_arm = not self.flags_dead_after(A + 2) if it.cap_kind == "mov" else not self.flags_dead_after(A + 2)
        code, lits, fixups, _ = self.build_tramp(it, p, use_arm)
        # 估算大小
        size = len(code) + 4 * len(lits) + 8
        base = self.alloc(size)
        # 回填字面量
        pool_off = len(code)
        pool = bytearray()
        for pos, val, rd in lits:
            la = pool_off + len(pool)
            pool.extend(struct.pack("<I", val & 0xFFFFFFFF))
            ins_addr = o2a(base) + pos
            off = (o2a(base) + la) - ((ins_addr + 4) & ~3)
            if off < 0 or off % 4 or off > 1020:
                raise FixError("字面量池超出范围")
            code[pos:pos + 2] = struct.pack("<H", 0x4800 | (rd << 8) | (off // 4))
        for pos, tgt in fixups:
            code[pos:pos + 4] = self.t_bl(o2a(base) + pos, tgt)
        blob = bytes(code + pool)
        self.d[base:base + len(blob)] = blob
        # 补丁点
        tramp_addr = o2a(base) | (0 if use_arm else 1)
        rX = it.cap_reg
        slot = p["slot"]
        endo = a2o(p["end"])
        patch = bytearray()
        for q in range(A, endo, 2):
            patch.extend(b"\xC0\x46")  # mov r8,r8
        off = o2a(slot) - ((o2a(A) + 4) & ~3)
        patch[0:2] = struct.pack("<H", 0x4800 | (rX << 8) | (off // 4))
        patch[2:4] = struct.pack("<H", 0x4700 | (rX << 3))
        self.d[A:endo] = patch
        if p["kind"] == "inline":
            self.d[slot:slot + 4] = struct.pack("<I", tramp_addr)
        else:
            self.d[slot:slot + 4] = struct.pack("<I", tramp_addr)
            self.used_lit_slots.add(slot)
        return {
            "id": it.id, "addr": h(it.addr), "方式": ("ARM 保标志跳板" if use_arm else "Thumb 跳板（标志随后被重设）"),
            "跳板": h(o2a(base)), "跳板长度": len(blob), "覆盖": "%s..%s" % (h(o2a(A)), h(p["end"])),
            "字面量": ("复用 " if p["kind"] == "slot" else "内联 ") + h(o2a(slot)),
        }


# ---------------------------------------------------------------- BPS

def _vlq(n):
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            break
        out.append(x)
        n -= 1
    return bytes(out)


def make_bps(src: bytes, dst: bytes, meta: str = "") -> bytes:
    out = bytearray(b"BPS1")
    out += _vlq(len(src)) + _vlq(len(dst)) + _vlq(len(meta.encode())) + meta.encode()
    i = 0
    n = len(dst)
    while i < n:
        # SourceRead 段
        j = i
        while j < n and j < len(src) and src[j] == dst[j]:
            j += 1
        if j > i:
            out += _vlq(((j - i - 1) << 2) | 0)
            i = j
            continue
        j = i
        while j < n and not (j < len(src) and src[j] == dst[j] and j + 8 <= n and src[j:j + 8] == dst[j:j + 8] if j + 8 <= min(n, len(src)) else False):
            j += 1
        out += _vlq(((j - i - 1) << 2) | 1) + dst[i:j]
        i = j
    out += struct.pack("<I", zlib.crc32(src) & 0xFFFFFFFF)
    out += struct.pack("<I", zlib.crc32(dst) & 0xFFFFFFFF)
    out += struct.pack("<I", zlib.crc32(bytes(out)) & 0xFFFFFFFF)
    return bytes(out)


def apply_bps(src: bytes, patch: bytes) -> bytes:
    p = 4
    def rd():
        nonlocal p
        data, shift = 0, 1
        while True:
            x = patch[p]; p += 1
            data += (x & 0x7F) * shift
            if x & 0x80:
                return data
            shift <<= 7
            data += shift
    ss, ts, ms = rd(), rd(), rd()
    p += ms
    out = bytearray()
    so = to = 0
    end = len(patch) - 12
    while p < end:
        v = rd(); cmd = v & 3; ln = (v >> 2) + 1
        if cmd == 0:
            out += src[len(out):len(out) + ln]
        elif cmd == 1:
            out += patch[p:p + ln]; p += ln
        elif cmd == 2:
            v2 = rd(); so += (-1 if v2 & 1 else 1) * (v2 >> 1)
            out += src[so:so + ln]; so += ln
        else:
            v2 = rd(); to += (-1 if v2 & 1 else 1) * (v2 >> 1)
            for _ in range(ln):
                out.append(out[to]); to += 1
    assert struct.unpack_from("<I", patch, len(patch) - 8)[0] == zlib.crc32(bytes(out)) & 0xFFFFFFFF, "BPS 校验失败"
    return bytes(out)


# ---------------------------------------------------------------- 报告 / CLI

RISK_ORDER = ["高", "中", "低", "已修"]


def summarize(items):
    c = {k: 0 for k in RISK_ORDER}
    for it in items:
        c[it.risk] += 1
    return c


def report_md(rom: Path, sha: str, items, fixes=None, failed=None, extra=""):
    c = summarize(items)
    L = [f"# GBR3 LR／返回地址 深度扫描报告", "",
         f"- 工具：{TOOL_VERSION}",
         f"- ROM：`{rom.name}`  SHA256 `{sha}`",
         f"- 汇总：高 {c['高']} · 中 {c['中']} · 低 {c['低']} · 已修 {c['已修']}", "",
         "风险说明：高＝在用且调用者在低 ROM、未换算（GBR3 上会不命中）；中＝引用或模式不确定；"
         "低＝死代码或调用者都在高 ROM；已修＝已有 +0x05E00000 换算。", "",
         "| # | 风险 | 地址 | 模式 | 捕获 | 比较方式 | 入口 | 引用 | 低ROM调用者 | 理由 | 可自动修 |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for it in items:
        low = [h(x) for x in it.callers if x < LOW_END]
        L.append("| %d | %s | %s | %s | `%s` | %s | %s | %s | %s | %s | %s |" % (
            it.id, it.risk, h(it.addr), it.mode, it.capture, it.pattern,
            h(it.entry) if it.entry else "-", "<br>".join(it.refs[:4]) or "无",
            (", ".join(low[:6]) + (" …共%d" % len(low) if len(low) > 6 else "")) or "-",
            it.reason, ("是" if it.fixable else ("需人工：" + it.fix_note if it.fix_note else "-"))))
    if fixes is not None:
        L += ["", "## 修复记录", ""]
        for f in fixes:
            L.append("- #%s %s：%s，跳板 %s（%d 字节），覆盖 %s，%s" % (
                f["id"], f["addr"], f["方式"], f["跳板"], f["跳板长度"], f["覆盖"], f["字面量"]))
        for i, why in (failed or []):
            L.append(f"- #{i} 未修：{why}")
    L += ["", "## 局限", "",
          "- 静态扫描：运行时算出的地址、间接调用、复杂的栈布局可能漏报或误判；最终以实机画面为准。",
          "- ARM 态命中只报告，不自动修。",
          "- 修复只改汉化 hook 代码，不改存档相关代码与数据；附近出现存档地址时拒绝自动修。",
          "- 修复后的 ROM 只用于本地生成补丁，请勿分发 ROM。"]
    if extra:
        L += ["", extra]
    return "\n".join(L) + "\n"


def sha256b(b):
    return hashlib.sha256(b).hexdigest()


def do_scan(rom: Path, orig: Path | None = None, log=print):
    data = rom.read_bytes()
    od = orig.read_bytes() if orig else None
    sc = Scanner(data, od, log=log)
    items = sc.scan()
    fx = Fixer(data, log=lambda *a: None)
    for it in items:
        if it.risk in ("高", "中") and not it.normalized:
            try:
                fx.plan(it)
                it.fixable = True
            except FixError as e:
                it.fix_note = str(e)
        elif it.risk == "低" and not it.normalized and any(c < LOW_END for c in it.callers):
            try:
                fx.plan(it); it.fixable = True
            except FixError as e:
                it.fix_note = str(e)
    return data, items


def do_fix(rom: Path, data: bytes, items, ids, out_dir: Path, log=print):
    out_dir.mkdir(parents=True, exist_ok=True)
    fx = Fixer(data, log=log)
    fixes, failed = [], []
    byid = {it.id: it for it in items}
    for i in ids:
        it = byid.get(i)
        if not it:
            failed.append((i, "无此编号")); continue
        try:
            r = fx.apply(it)
            fixes.append(r)
            log(f"  已修 #{i} {h(it.addr)} → 跳板 {r['跳板']}（{r['方式']}）")
        except FixError as e:
            failed.append((i, str(e)))
            log(f"  #{i} {h(it.addr)} 不能自动修：{e}")
    fixed = bytes(fx.d)
    stem = rom.stem
    fixed_rom = out_dir / f"{stem}_GBR3LR修复.gba"
    fixed_rom.write_bytes(fixed)
    bps = make_bps(data, fixed, meta=f"GBR3 LR fix by {TOOL_VERSION}")
    assert apply_bps(data, bps) == fixed
    bps_path = out_dir / f"{stem}_GBR3LR修复.bps"
    bps_path.write_bytes(bps)
    # 修复后复扫
    rescan = Scanner(fixed, log=lambda *a: None).scan()
    c2 = summarize(rescan)
    extra = (f"## 文件\n\n- 原汉化 ROM SHA256 `{sha256b(data)}`\n- 修复后 ROM SHA256 `{sha256b(fixed)}`（仅本地使用）\n"
             f"- BPS 补丁 `{bps_path.name}` SHA256 `{sha256b(bps)}`（打在上面的原汉化 ROM 上）\n\n"
             f"## 修复后复扫\n\n高 {c2['高']} · 中 {c2['中']} · 低 {c2['低']} · 已修 {c2['已修']}\n")
    rep = report_md(rom, sha256b(data), items, fixes, failed, extra)
    (out_dir / f"{stem}_LR扫描修复报告.md").write_text(rep, encoding="utf-8")
    return fixed_rom, bps_path, fixes, failed, rescan


def add_configs(zp: Path, configs: str):
    """按发布惯例把完整 _gba/configs/ 一起放进 ZIP。"""
    import zipfile
    here = Path(__file__).resolve().parent
    cands = [Path(configs)] if configs else [here / "_gba" / "configs", here / "configs"]
    cdir = next((c for c in cands if c.is_dir() and any(c.glob("*.json"))), None)
    if not cdir:
        print("提示：没找到 GBR3 的 configs 目录，ZIP 里没带 _gba/configs/。发布前请用 --configs 指定，"
              "或把 GBR3 的 _gba/configs 放到本工具目录下。")
        return
    n = 0
    with zipfile.ZipFile(zp, "a", zipfile.ZIP_DEFLATED) as z:
        have = set(z.namelist())
        for f in sorted(cdir.rglob("*")):
            if f.is_file():
                arc = "_gba/configs/" + f.relative_to(cdir).as_posix()
                if arc not in have:
                    z.write(f, arc); n += 1
    print(f"已把 {cdir} 下 {n} 个文件放进 ZIP 的 _gba/configs/")


def main(argv=None):
    ap = argparse.ArgumentParser(description="GBR3 LR／返回地址 深度扫描与修复（中文）")
    ap.add_argument("--rom", required=True, help="汉化 .gba")
    ap.add_argument("--orig", default="", help="原版 .gba（可选：用于标记自定义区；做 slot2patch 时必填）")
    ap.add_argument("--scan", action="store_true", help="只扫描并输出报告")
    ap.add_argument("--fix", default="", help="要修复的编号，逗号分隔，如 1,3")
    ap.add_argument("--fix-high", action="store_true", help="修复全部可自动修的高风险条目")
    ap.add_argument("--out", default="", help="输出目录")
    ap.add_argument("--json", action="store_true", help="同时输出 JSON")
    ap.add_argument("--slot2patch", action="store_true", help="修复后接着调用 slot2patch_core 生成 GBR3 补丁包（需 --orig）")
    ap.add_argument("--version", default="")
    ap.add_argument("--name", default="")
    ap.add_argument("--force-orig", action="store_true")
    ap.add_argument("--skip-verify", action="store_true")
    ap.add_argument("--configs", default="", help="GBR3 的 _gba/configs 目录；给了就整个打进 ZIP（默认自动找本目录/_gba/configs 或 configs）")
    a = ap.parse_args(argv)
    rom = Path(a.rom)
    orig = Path(a.orig) if a.orig else None
    out = Path(a.out) if a.out else rom.parent / (rom.stem + "_LR扫描")
    out.mkdir(parents=True, exist_ok=True)
    data, items = do_scan(rom, orig)
    c = summarize(items)
    print(f"汇总：高 {c['高']} · 中 {c['中']} · 低 {c['低']} · 已修 {c['已修']}")
    for it in items:
        print(f"  #{it.id:<3} [{it.risk}] {h(it.addr)} {it.mode} {it.capture} | {it.pattern} | {it.reason}"
              + ("" if it.fixable or it.risk in ("低", "已修") else f" | 需人工：{it.fix_note}"))
    if a.json:
        jp = out / f"{rom.stem}_LR扫描.json"
        jp.write_text(json.dumps([i.to_json() for i in items], ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"JSON：{jp}")
    ids = [int(x) for x in a.fix.split(",") if x.strip()] if a.fix else []
    if a.fix_high:
        ids += [it.id for it in items if it.risk == "高" and it.fixable]
    ids = sorted(set(ids))
    if a.scan or not ids:
        (out / f"{rom.stem}_LR扫描报告.md").write_text(report_md(rom, sha256b(data), items), encoding="utf-8")
        print(f"报告：{out / (rom.stem + '_LR扫描报告.md')}")
        if not ids:
            if a.slot2patch:
                print("没有要修的条目；如需直接打 slot2patch，请用原来的生成按钮。")
            return 0
    fixed_rom, bps, fixes, failed, rescan = do_fix(rom, data, items, ids, out)
    print(f"修复后 ROM（仅本地）：{fixed_rom}")
    print(f"BPS 补丁：{bps}")
    if a.slot2patch:
        if not orig:
            print("错误: --slot2patch 需要 --orig", file=sys.stderr)
            return 1
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import slot2patch_core as core
        try:
            zp = core.build(orig, fixed_rom, version_label=(a.version or None), friendly_name=(a.name or None),
                            out_dir=out / "slot2patch", force_orig=a.force_orig, skip_verify=a.skip_verify)
        except core.Die as e:
            print(f"错误: {e}", file=sys.stderr)
            return 1
        add_configs(Path(zp), a.configs)
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())

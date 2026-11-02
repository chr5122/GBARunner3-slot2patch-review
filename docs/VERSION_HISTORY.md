# 版本沿革与整合记录

**2026-11-02 社区 PATCH 主线已整合 H1＋SR2**（含跨行状态一致采样加固）。[整合记录](../h1_sr2_mainline/README.md) · [完整源码](https://github.com/chr5122/GBARunner3/tree/65866604e5fd4e90c51eb32e6ea34bb251d075c4)。H1/SR2 分别有用户实机成功反馈；最终组合通过电脑回归，仍待实机复测。A2 未加入，save 线本轮未改。

[返回首页](../README.md) · [完整产物哈希](VERSIONS.md) · [验证状态](STATUS.md)

## 当前入口

| 类型 | 当前整理候选 | 原文件名 | 父本／关系 |
|---|---|---|---|
| patch | `GBARunner3_PATCH_B3.nds` | `B3_THUMB_BX_STRICT_RAM_TEST.nds` | R1 + B3 |
| save | `GBARunner3_SAVE_G1S_B3.nds` | `G1S_B3_TEST.nds` | G1S + B3 移植 |
| 电脑工具 | slot2patch tool v2，PR #5 | Mac arm64 / Windows x64 两包 | 基于 Wokann PatchToolForGbaR3 的封装、扫描与打包 |

这里集中的是查看和维护入口。运行器 NDS 尚未提供下载，本地正式基线仍为 R1；名称整理没有改变任何已测二进制，也不代表上游正式版本号。

## 两条运行器演进线

- **patch：** 固定 Wokann slot2patch → X1 / D1 / D2 运行期写盘对照及自动 PRE → G1 音频处理 → romopt 无占位启动 → R1 读取失败保护 → B3 跳转快捷处理。
- **save：** 固定 Wokann slot2save → G1S 音频移植 → G1S+B3。
- B1 / B2、E 系列声音诊断等属于历史研究阶段，不列为当前推荐运行文件。保留已有报告、源码阅读副本和计数，不把它们混入日常运行包。

这些箭头说明功能演进，不是一套可以盲目连续应用的公共构建命令。每份 diff 的父本见 [VERSIONS](VERSIONS.md)；R1 完整公共前置材料仍待补齐。

## 本轮合并

- [#2](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/2)：G1S 音频移植材料已合入。
- [#3](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/3)：patch B3 / save G1S+B3 两套材料已合入。
- [#5](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/5)：新版工具材料和已有 Mac / Windows 包已合入。
- [#4](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/4)：早期重复工具 PR 已关闭，并指向 #5；分支、旧包和讨论保留。

使用 merge commit 保留原功能提交，没有压成一个丢失功能边界的大提交。#2 的根校验清单冲突仅合并双方新增字段，保留 main 既有 romopt 记录和全部 G1S 字段。

## 固定的历史入口

| 内容 | 固定提交／备份 |
|---|---|
| 整合前 main | [`2357c761`](https://github.com/chr5122/GBARunner3-slot2patch-review/tree/2357c761b48148e9d7484b19088631b6a11d225b)；另保留分支 `archive/main-before-consolidation-20261101` |
| G1S 原材料 | [`52cc8992`](https://github.com/chr5122/GBARunner3-slot2patch-review/tree/52cc8992b6d84fe8c30f0bdc2d5db9d5190a8954/g1s_dma_wrap) |
| B3 两模式原材料 | [`ef30682f`](https://github.com/chr5122/GBARunner3-slot2patch-review/tree/ef30682f928dfc59a8edd49dd858faee53a59603) |
| 工具早期 PR #4 | [`cd314492`](https://github.com/chr5122/GBARunner3-slot2patch-review/tree/cd3144928496fd9995e2b6317d50a103b6ef536c/slot2patch_tool_v2) |
| 工具当前 PR #5 | [`53f27641`](https://github.com/chr5122/GBARunner3-slot2patch-review/tree/53f27641a881ab4941cb81b5eca1feda6a48a328/slot2patch_tool_v2) |
| D2 / G1 旧首页 | [历史文稿](HISTORY_D2_README.md) · [原始字节副本](archive/README_D2_G1.original.txt) |

现有功能分支继续保留，不删除历史记录。无需为了阅读完整材料切分支；作者以后仍可通过这些提交和 PR 单独审核。

本轮没有重编译运行器、改变默认配置、上传游戏 ROM / BIOS / 存档 / NDS，或创建正式运行器 Release。没有向 Wokann / Gericom 仓库合并任何改动。


## 2026-11-02：H1＋SR2 合入社区 PATCH 主线

用户确认 SR2 实机验证成功并要求与 H1 一同并入主线。以准确 H1 为父本整合 SR2；首次组合回归发现 H1 分开读取行号／状态的跨行误过滤，补充一致采样后重新通过大小光圈与软重启回归。完整源码 commit `65866604e5fd4e90c51eb32e6ea34bb251d075c4`；不含 A2，不改变 save。上游独立 PR #9 保留供作者审阅，本仓库 main 的整合不等于上游已合并。

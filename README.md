# GBARunner3 社区改进记录：patch / save

这里整理 CHONG 512 的 GBARunner3 Slot-2 实验、源码差异与验证记录，供 Wokann（卧看微尘）和其他贡献者审阅。

**来源：** GBARunner3 基础项目来自 [Gericom 与原项目贡献者](https://github.com/Gericom/GBARunner3)；Slot-2 存档、外挂补丁及相关分支基于 [Wokann/GBARunner3](https://github.com/Wokann/GBARunner3)。本仓库记录在这些工作之上的社区修改，不代表上游已经采纳。

## 先选运行方式

| 方式 | 游戏程序与中文内容来自哪里 | Slot-2 卡带在本项目测试中的作用 | 入口 |
|---|---|---|---|
| **patch：slot2patch** | 正版卡原 ROM + SD 上的外挂补丁；修改块经 PRE 缓存读取 | 提供原版 ROM 和卡带存档 | [patch 项目](docs/PATCH.md) |
| **save：slot2save** | SD 上完整的游戏 ROM，可使用汉化 ROM | 使用对应正版卡的存档 | [save 项目](docs/SAVE.md) |

两条线有各自的 NDS、父本和测试记录。**G1S 是 save 版；G1、R1、B3 是这里的 patch 版命名。** G1S+B3 是把 B3 思路移植到 save 的另一个产物。

## 当前统一入口

声音修复、B3 和新版打包工具的材料已汇总到 `main`，无需为阅读不同功能来回切换分支。patch / save 仍是两个独立运行文件；这次整合不重编译 NDS、不改变本地 R1 基线，也没有创建正式 NDS Release。

| 要看什么 | 当前入口 | 对应产物／范围 |
|---|---|---|
| patch 最新候选 | [B3 材料](b3_thumb_bx_strict_ram/README.md) · [模式说明](docs/PATCH.md) | `GBARunner3_PATCH_B3.nds`，原名 `B3_THUMB_BX_STRICT_RAM_TEST.nds` |
| save 最新候选 | [G1S+B3 材料](g1s_b3_thumb_bx/README.md) · [模式说明](docs/SAVE.md) | `GBARunner3_SAVE_G1S_B3.nds`，原名 `G1S_B3_TEST.nds` |
| 电脑补丁打包工具 | [工具入口](docs/TOOLS.md) · [源码和已有 Mac / Windows 包](slot2patch_tool_v2/README.md) | 工具包已在仓库；扫描／自动修复仍按工具的已知限制使用 |
| 历史版本和诊断材料 | [版本沿革](docs/VERSION_HISTORY.md) · [产物哈希](docs/VERSIONS.md) | 保留原目录、提交、历史分支及回退关系 |

这两份 NDS 只记录名称和哈希，**尚未在本仓库提供下载**。工具目录里的 ZIP 是电脑端打包工具，不是 NDSL 上运行的 GBR3 安装包。

## 当前材料与进度

| 模式 | 版本/改动 | 目前证据 | 在哪里看 |
|---|---|---|---|
| patch | D2：启动自动生成 PRE，运行期关闭日志/周期写盘 | 有用户实机、缓存生成及保存互通反馈。2026-11-01 用户实机确认正常（火红、绿宝石） | [说明](docs/PATCH.md#d2-pre) |
| patch | G1：m4a PCM 声音 DMA 回绕 | 有用户反馈切场景爆音消失。2026-11-01 用户实机确认正常（火红、绿宝石） | [G1 原始记录](G1_AUDIO_POP_FIX.md) · [PR #1，已合并到本仓库](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/1) |
| patch | 占位 ROM 可选（romopt，2026-10-28）：从菜单直接启动时 SD 根目录不再需要占位 `rom.gba` | melonDS 模拟器对照；2026-11-01 用户实机确认正常（火红、绿宝石）。此行为由 R1、B3 继承，见状态页 | [说明](docs/PATCH.md#rom-optional) · [试验材料](rom_gba_optional/README.md) |
| patch | R1：SD 读取结果传递、失败缓存禁止发布、嵌套缓冲保护 | 本地正式基线；电脑验证及用户实机成功反馈。2026-11-01 用户实机确认正常（火红、绿宝石） | [R1 状态与材料边界](docs/PATCH.md#r1-read-guard) |
| patch | B3：缓存内 Thumb BX 快捷处理，目标限标准 RAM/低 ROM | 电脑复核通过；用户反馈两模式实机体验良好，分项验收见状态页。2026-11-01 用户实机确认正常（火红、绿宝石） | [B3 材料](b3_thumb_bx_strict_ram/README.md) · [合并记录 #3](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/3) |
| save | G1S：移植 m4a PCM DMA 回绕 | 有用户 NDSL 实机反馈，切场景“咔”声消失。2026-11-01 用户实机确认正常（火红、绿宝石） | [G1S 材料](g1s_dma_wrap/README.md) · [合并记录 #2](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/2) |
| save | G1S+B3：在 G1S 上移植 BX 快捷处理 | 已有电脑模型结果及用户两模式实机体验反馈；保存往返待分项补录。2026-11-01 用户实机确认正常（火红、绿宝石） | [G1S+B3 材料](g1s_b3_thumb_bx/README.md) |

- [验证状态与结果](docs/STATUS.md)：区分模型、独立复核、用户实机和未测项目。
- [版本与 SHA256](docs/VERSIONS.md)：准确区分 NDS、父本、补丁基准。
- [作者审阅入口](docs/REVIEW.md)：按功能查看源码差异，避免叠错补丁。
- [历史 D2/G1 首页](docs/HISTORY_D2_README.md)：原有详细记录完整保留。

## 最新模型结果

| 模式与固定场景 | 对照 | 候选 | 指标 |
|---|---|---|---|
| patch，绿宝石八地址配置 | R1：60 / 81 / 127 | B3：38 / 37 / 37 | 三次训练家卡翻面模型帧数 |
| save，绿宝石八地址配置 | G1S：63 | G1S+B3：41 | 首次训练家卡翻面模型帧数 |

**这是两组分别匹配输入的电脑模型对照，不是 NDSL 实机 FPS，也不能横向比较两种模式的绝对速度。**

## 发布准备（2026-10-31）

两份原始测试文件已核对哈希，并在本地分别固定候选包、升级教程、回退版和源码快照。二进制没有重新编译或设为默认。

[发布准备与剩余验收](docs/RELEASE_PREPARATION.md)：当前没有上架 NDS 下载或创建正式 Release，保存/重启/原生 GBA 互通按候选分别记录。

## 仓库如何使用

本仓库是审阅材料和部分源码阅读副本，**不是完整、可单独编译的源码 checkout**。目前没有在这里发布 NDS 安装包或正式 Release。

PR #2、#3、#5 已合入本仓库 `main`；重复的早期工具 PR #4 已关闭并指向 #5。下载 `main` 的 ZIP 可得到这些材料和工具文件，但不是完整的运行器源码或 NDS 安装包。各功能的提交与讨论仍可独立查看；本仓库合并不等于 Wokann 或 Gericom 已合入其项目。

原补丁、构建 JSON 和旧 SHA 清单按历史记录保留。新增导航文件的当前哈希单列在 [DOCS_SHA256.json](DOCS_SHA256.json)，维护规则见 [docs/MAINTENANCE.md](docs/MAINTENANCE.md)。

旧的诊断、布局、失败注入、音频及硬件范围说明仍可从原始文档查阅；运行期 SD 只读也不表示卡带存档被写保护。来源与原文件声明见 [NOTICE.md](NOTICE.md)。

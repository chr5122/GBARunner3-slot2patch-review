# GBARunner3 社区改进：PATCH / SAVE

**最新更新：2026-11-04｜新增 A17 PATCH 音频测试版下载；社区代码主线仍为此前 H1＋SR2 整合。**

**[下载 A17 NDS](audio_a17/GBARunner3_PATCH_A17.nds?raw=true) · [下载 A17 ZIP](audio_a17/GBARunner3_PATCH_A17.zip?raw=true) · [A17 改进、源码与验证范围](audio_a17/README.md)**

[当前整合与验证记录](h1_sr2_mainline/README.md) · [完整 PATCH 源码](https://github.com/chr5122/GBARunner3/tree/65866604e5fd4e90c51eb32e6ea34bb251d075c4) · [上游 PR 状态](docs/UPSTREAM_PRS.md) · [版本与 SHA256](docs/VERSIONS.md)

这里整理 CHONG 512 的 Slot-2 社区改进。基础项目来自 [Gericom 与原项目贡献者](https://github.com/Gericom/GBARunner3)，Slot-2 save／patch 分支来自 [Wokann（卧看微尘）](https://github.com/Wokann/GBARunner3)。社区 main 的整合不代表上游已经合并。

## 当前版本与验收状态

| 项目 | 当前版本／状态 | 入口 |
|---|---|---|
| **PATCH 代码主线** | **H1＋SR2＋跨行状态一致采样加固**；保留 B3 及其前置功能，未加入 A2 | [整合记录](h1_sr2_mainline/README.md) · [完整源码](https://github.com/chr5122/GBARunner3/tree/65866604e5fd4e90c51eb32e6ea34bb251d075c4) |
| PATCH 实机反馈 | 用户分别确认 H1、SR2 成功；**新组合及新增采样加固仍待实机复测** | [验证证据](h1_sr2_mainline/integration_results.json) |
| SAVE 候选 | G1S＋B3；本轮没有移植 H1／SR2，也没有修改 save 代码 | [SAVE 项目](docs/SAVE.md) · [G1S＋B3 材料](g1s_b3_thumb_bx/README.md) |
| **PATCH 音频测试下载** | **A17**：已有用户实机试听改善反馈，多游戏验收未完成；未替换代码主线，未创建正式 Release | [NDS／ZIP／源码与说明](audio_a17/README.md) |

当前 PATCH 构建文件名：`GBARunner3_PATCH_H1_SR2.nds`，228864 字节。SHA256：

```text
1aa3ab06bd34c140c260bd833f3777714324ec1b50e24d8e0513628e16125199
```

这是最终组合文件的指纹，不能与单独 H1、单独 SR2 或上游 PR 的独立构建混用。

## 这次合入了什么

- **H1：共享 HBlank 时序与窗口 DMA 维护。** 问题所在路径在全游戏运行中共用，不依赖洞穴地图；洞穴光圈只是更容易观察错行的复现场景。维护仍限已审计的窗口 DMA0 配置，其他效果不宣称全部修复。
- **SR2：high-ROM SWI 半字选择修复。** 修正绿宝石软重启前 SWI1 被误读成存档 SWI 0x8D 的路径，避免该路径进入 PC=4 白屏。根因排查来自用户提供的 Grok 交接。
- **跨行采样加固。** 合并回归发现行号和状态分开读取可能跨扫描线；现在一致读取 DISPSTAT／VCOUNT，避免误过滤一次正常 HBlank。

[三文件完整差异（B3 → 当前组合）](h1_sr2_mainline/B3_TO_H1_SR2.diff) · [构建与范围核对](h1_sr2_mainline/verification.json) · [原始 H1 材料](h1_window_dma/README.md)

## 最新组合回归结果

| 测试 | 最终组合结果 |
|---|---|
| 大光圈：静止、走动、停下 | 446/446 帧与原 H1 画面一致，越界 0；每帧 DMA0 160 次 |
| 小光圈：静止、走动、停下 | 446/446 帧与原 H1 画面一致，越界 0；每帧 DMA0 160 次 |
| 每组卡带复制审计 | 205 次复制、27 次分段、86 次维护；内容错误、提前发布／重入和未完成复制均未发现 |
| 软重启对照 | 原 H1 误派发 SWI 0x8D、最终 PC=4；新组合正确进入 SWI1／SWI0、BIOS SoftReset 并返回开场 |
| 实际 ARM 指令检查 | SR2 解码 8192 例；一致采样 guard 10240 例通过 |
| 测试期间的写入 | 虚拟 SD 写入、保存持久化请求及虚拟 Flash 变化均为 0，原输入哈希不变 |

**以上是电脑模型结果，不是 NDSL 实机耗时或 FPS。** H1、SR2 分别的用户实机成功反馈已记录；最终组合尚未实机复测，完整通关名单也未在本轮重跑。这组回放没有新增真实卡带保存验收。

## 向 Wokann 提交的 PR

| 内容 | 状态 |
|---|---|
| H1 共享 HBlank 时序及后续一致采样加固 | **已提交 [Wokann PR #9](https://github.com/Wokann/GBARunner3/pull/9)，Draft，待作者审阅** |
| SR2 SWI 解码 | **已合入咱们社区主线，尚未单独向 Wokann 提 PR** |
| 对齐、声音、B3、运行期日志、读取失败保护 | 已按功能拆成独立 Draft PR，见[完整索引](docs/UPSTREAM_PRS.md) |

PR #9 只含独立 H1 及采样加固，**不含 SR2 或整套社区组合功能**。PR 构建与本页组合构建有各自的哈希和验证范围。Wokann／Gericom 是否采纳由上游决定。

## 先选运行方式

| 方式 | 游戏程序与中文内容 | Slot-2 正版卡的作用 | 说明 |
|---|---|---|---|
| **PATCH：slot2patch** | 卡带原 ROM＋SD 外挂补丁；修改块经 PRE 提供 | 原版 ROM 与卡带存档 | [PATCH 项目](docs/PATCH.md) |
| **SAVE：slot2save** | SD 中完整游戏 ROM，可使用汉化 ROM | 使用对应卡带存档 | [SAVE 项目](docs/SAVE.md) |

两种模式使用不同 NDS。G1S 是 save 版；G1、R1、B3、H1＋SR2 在本页 PATCH 沿革中分别记录，不能混用产物。

## 继承功能与历史材料

当前 PATCH 主线继承 D2 自动 PRE／运行期日志调整、G1 声音回绕、可选占位 ROM、R1 读取失败保护、hicode 对齐和 B3 缓存 Thumb BX 快捷处理。旧记录与原构建 JSON 保留，后续反馈不回写历史证据。

| 材料 | 入口 |
|---|---|
| D2、G1 与早期实机记录 | [PATCH 沿革](docs/PATCH.md) · [实机历史](FIELD_TESTS.md) · [G1 音频记录](G1_AUDIO_POP_FIX.md) |
| B3 与原 save 候选 | [PATCH B3](b3_thumb_bx_strict_ram/README.md) · [SAVE G1S](g1s_dma_wrap/README.md) · [SAVE G1S＋B3](g1s_b3_thumb_bx/README.md) |
| 历史翻卡性能对照 | [验证状态](docs/STATUS.md)；PATCH R1 60/81/127 → B3 38/37/37，SAVE G1S 63 → G1S＋B3 41，均为各自模型帧数，不横比两模式速度 |
| 电脑补丁打包工具 | [工具入口](docs/TOOLS.md) · [源码与已有 Mac／Windows 工具包](slot2patch_tool_v2/README.md) |
| 版本、验收与审阅导航 | [版本沿革](docs/VERSION_HISTORY.md) · [版本哈希](docs/VERSIONS.md) · [验证状态](docs/STATUS.md) · [审阅入口](docs/REVIEW.md) |
| 历史首页与维护规则 | [D2/G1 首页存档](docs/HISTORY_D2_README.md) · [维护约定](docs/MAINTENANCE.md) · [来源与声明](NOTICE.md) |

本仓库 `main` 是审阅材料与源码阅读副本；**可编译的完整 PATCH 源码在 [chr5122/GBARunner3 的 community/slot2patch](https://github.com/chr5122/GBARunner3/tree/community/slot2patch)**，当前固定提交为 `65866604e5fd4e90c51eb32e6ea34bb251d075c4`。构建需要原项目工具链和 libtwl submodule，步骤见[整合记录](h1_sr2_mainline/README.md)。

运行器测试包请使用上方 A17 下载入口；工具目录的 ZIP 是电脑端工具。A17 为 PATCH 测试版，SAVE 下载状态不变。本仓库没有打包游戏 ROM、BIOS、存档或汉化资源。历史根 `SHA256.json` 保留旧含义，当前导航文件摘要见 [DOCS_SHA256.json](DOCS_SHA256.json)。


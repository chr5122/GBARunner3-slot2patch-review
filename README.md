# GBARunner3 社区改进记录：patch / save

这里整理 CHONG 512 的 GBARunner3 Slot-2 实验、源码差异与验证记录，供 Wokann（卧看微尘）和其他贡献者审阅。

**来源：** GBARunner3 基础项目来自 [Gericom 与原项目贡献者](https://github.com/Gericom/GBARunner3)；Slot-2 存档、外挂补丁及相关分支基于 [Wokann/GBARunner3](https://github.com/Wokann/GBARunner3)。本仓库记录在这些工作之上的社区修改，不代表上游已经采纳。

## 先选运行方式

| 方式 | 游戏程序与中文内容来自哪里 | Slot-2 卡带在本项目测试中的作用 | 入口 |
|---|---|---|---|
| **patch：slot2patch** | 正版卡原 ROM + SD 上的外挂补丁；修改块经 PRE 缓存读取 | 提供原版 ROM 和卡带存档 | [patch 项目](docs/PATCH.md) |
| **save：slot2save** | SD 上完整的游戏 ROM，可使用汉化 ROM | 使用对应正版卡的存档 | [save 项目](docs/SAVE.md) |

两条线有各自的 NDS、父本和测试记录。**G1S 是 save 版；G1、R1、B3 是这里的 patch 版命名。** G1S+B3 是把 B3 思路移植到 save 的另一个产物。

## 当前材料与进度

| 模式 | 版本/改动 | 目前证据 | 在哪里看 |
|---|---|---|---|
| patch | D2：启动自动生成 PRE，运行期关闭日志/周期写盘 | 有用户实机、缓存生成及保存互通反馈 | [说明](docs/PATCH.md#d2-pre) |
| patch | G1：m4a PCM 声音 DMA 回绕 | 有用户反馈切场景爆音消失 | [G1 原始记录](G1_AUDIO_POP_FIX.md) · [PR #1，已合并到本仓库](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/1) |
| patch | R1：SD 读取结果传递、失败缓存禁止发布、嵌套缓冲保护 | 本地正式基线；电脑验证及用户实机成功反馈 | [R1 状态与材料边界](docs/PATCH.md#r1-read-guard) |
| patch | B3：缓存内 Thumb BX 快捷处理，目标限标准 RAM/低 ROM | 电脑复核通过；用户反馈两模式实机体验良好，分项验收见状态页 | [PR #3](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/3) |
| save | G1S：移植 m4a PCM DMA 回绕 | 有用户 NDSL 实机反馈，切场景“咔”声消失 | [PR #2](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/2) |
| save | G1S+B3：在 G1S 上移植 BX 快捷处理 | 已有电脑模型结果及用户两模式实机体验反馈；保存往返待分项补录 | [PR #3](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/3) |

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

PR #2、#3 的材料尚未合入 `main`，所以首页通过 PR 和固定提交链接提供入口。仅下载 `main` 的 ZIP 不会得到这些 PR 的全部文件。PR 合并到本材料仓库，也不等于 Wokann 或 Gericom 已合入其项目。

原补丁、构建 JSON 和旧 SHA 清单按历史记录保留。新增导航文件的当前哈希单列在 [DOCS_SHA256.json](DOCS_SHA256.json)，维护规则见 [docs/MAINTENANCE.md](docs/MAINTENANCE.md)。

旧的诊断、布局、失败注入、音频及硬件范围说明仍可从原始文档查阅；运行期 SD 只读也不表示卡带存档被写保护。来源与原文件声明见 [NOTICE.md](NOTICE.md)。

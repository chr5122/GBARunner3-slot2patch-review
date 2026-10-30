# 作者审阅入口

[返回首页](../README.md) · [版本指纹](VERSIONS.md) · [验证状态](STATUS.md)

## 按功能审阅

| 功能 | 模式 | 主要材料 | 入口 |
|---|---|---|---|
| 运行期只读、启动自动 PRE | patch | 10_/20_ 差异、IMPLEMENTATION、PATCH_VERIFICATION | [历史首页](HISTORY_D2_README.md) |
| m4a 音频 DMA 回绕 | patch | 30_ 差异、G1_AUDIO_POP_FIX、布局摘要 | [PR #1](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/1) |
| m4a 音频 DMA 回绕移植 | save | g1s_dma_wrap 目录、BUILD_INFO、源码 diff | [PR #2](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/2) |
| B3 Thumb BX 快捷处理 | patch 与 save 两个构建 | 两套 README、源码差异、报告、独立复核 | [PR #3](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/3) |

## 当前 PR 状态

- #1 已合并到本材料仓库。
- #2、#3 是本仓库内部的材料整理 PR，仍待审，尚未合入 main。
- 这些状态都不是 Wokann/Gericom 仓库的合并状态；没有把仓库内部 PR 当成上游已采纳。

首页引用固定提交文件，便于在 PR 尚未合并时阅读；PR 主页面保留后续讨论和修改。

## 各类文件的作用

- README、状态页：当前入口和后续反馈。
- SOURCE.patch / diff：代码审核；先核对父本。
- build.json、BUILD_INFO、SHA256SUMS：冻结的构建与产物记录。
- REPORT、独立复核：当时的测试过程和证据范围，后续实机另列。
- `source/`：D2 阶段部分改动文件的阅读副本，不是完整、当前候选可独立构建的源码树。

R1 的公共前置构建材料尚未补齐。当前可以审查 B3 的设计和局部实现，但不能据此称本仓库已提供从原上游一键重建 B3 的完整流程。

本次整理只更新导航、状态说明及来源署名，不合并待审 PR，不发布 NDS/Release，也不把候选晋升为基线。

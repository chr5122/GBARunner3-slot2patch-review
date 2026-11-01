# 作者审阅入口

[返回首页](../README.md) · [版本指纹](VERSIONS.md) · [验证状态](STATUS.md) · [历史版本](VERSION_HISTORY.md)

## 按功能审阅

| 功能 | 模式 | 当前材料 | 原 PR／讨论 |
|---|---|---|---|
| 运行期只读、启动自动 PRE | patch | [实现与差异](PATCH.md#d2-pre) | [历史首页](HISTORY_D2_README.md) |
| m4a 音频 DMA 回绕 | patch | [G1 记录](../G1_AUDIO_POP_FIX.md) · [D2 → G1](../30_G1_vs_D2_review.patch) | [#1，已合并](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/1) |
| m4a 音频 DMA 回绕移植 | save | [G1S 目录](../g1s_dma_wrap/README.md) | [#2，已合并](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/2) |
| B3 Thumb BX 快捷处理 | patch | [B3 目录](../b3_thumb_bx_strict_ram/README.md) | [#3，已合并](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/3) |
| B3 Thumb BX 移植 | save | [G1S+B3 目录](../g1s_b3_thumb_bx/README.md) | 同 #3，两个产物分别记录 |
| 无占位 ROM 启动 | patch | [试验目录](../rom_gba_optional/README.md) · [后续继承关系](PATCH.md#rom-optional) | 原分支与固定提交见版本沿革 |
| 电脑端补丁工具 v2 | 工具 | [工具入口](TOOLS.md) · [源码与已有包](../slot2patch_tool_v2/README.md) | [#5，已合并](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/5)；[#4 已由 #5 替代](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/4) |

以上 PR 是本仓库内部材料整合，均不表示 Wokann 或 Gericom 已审核通过或合入。作者之后仍可逐项审阅原提交和差异，无需把整套社区改动一次性接收。

## 各类文件的作用

- 首页、模式页、状态页：当前入口和后续反馈。
- SOURCE.patch / diff：局部代码审核；先核对父本。
- build.json、BUILD_INFO、各目录 SHA256SUMS：原构建和产物记录，不因整合回写历史测试结论。
- REPORT、独立复核：当时过程及证据范围，后续反馈另见 STATUS。
- `source/`：D2 阶段部分改动文件的历史阅读副本，不是最新候选的完整源码。
- `slot2patch_tool_v2/src/`：电脑工具源码，与上面的运行器源码阅读副本是不同内容。

R1 的公共前置构建材料仍未补齐。可以审查 B3 的设计和局部实现，但本仓库还没有从裸上游一键重建当前 B3 NDS 的完整流程。

本轮只整合现有材料及工具、更新入口并关闭重复 PR；没有重新编译运行器、改默认配置、改变本地基线、上传 NDS 或创建正式运行器 Release。

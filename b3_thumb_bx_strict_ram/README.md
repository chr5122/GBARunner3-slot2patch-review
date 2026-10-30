# B3：Thumb BX 快捷处理（patch）

基于 Gericom 与原项目贡献者的 GBARunner3，以及 Wokann（卧看微尘）的 `slot2patch` 分支。这里整理 CHONG 512 的社区实验材料，供作者审阅，不表示上游已经采纳。

[patch 项目入口](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/main/docs/PATCH.md) · [统一验证状态](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/main/docs/STATUS.md) · [版本与 SHA256](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/main/docs/VERSIONS.md)

## 实机测试（2026-10-30）

用户反馈 B3（patch）和 G1S+B3（save）两模式在 NDSL 实机体验良好；本页只记录对应产物，模型数值分开列出，不当作实机耗时。当前候选的保存、重启与原生 GBA 读档互通尚未逐项补录。

## 改动

- 仅在 Thumb 预取异常路径处理缓存内的 `BX r0-r3`。
- 目标限标准 EWRAM（0x02000000–0x0203FFFF）、IWRAM（0x03000000–0x03007FFF）和低 2MB ROM（0x08000000–0x081FFFFF）。
- 其他编码、地址和缓存缺失回到原路径。
- 未修改声音、存档、SD 或 MSR/IRQ 处理器。

对照是 **R1 patch**。`SOURCE.patch` 相对 R1；`B2_TO_B3.patch` 相对 B2。它们不是直接相对 Wokann 裸分支的一键构建步骤；R1 的完整公共前置材料尚未在本仓库补齐。

## 结果与后续反馈

固定绿宝石八地址配置下，三次翻卡模型帧为 R1 60/81/127 → B3 38/37/37；首次映射重建 24219 → 1376。模型、指令等价和独立复核记录见 [REPORT.md](REPORT.md)、[DESIGN.md](DESIGN.md)、[B3_INDEPENDENT_REVIEW.md](B3_INDEPENDENT_REVIEW.md)。

构建 JSON 仍保留生成时的“未实机”历史状态。已实机初步验证（仅绿宝石；火红叶绿未测）。测试前备份存档。

## 产物

`B3_THUMB_BX_STRICT_RAM_TEST.nds`，228352 字节，SHA256：

`f2d5f8bedf024a694b00ee3bcb1eaebdda2eb21644b20e06c063f5f499f5dbad`

NDS 不入库。本项目本地正式基线仍为 R1；未提供正式 Release，未代表其他游戏或完整动态 JIT 已通过。

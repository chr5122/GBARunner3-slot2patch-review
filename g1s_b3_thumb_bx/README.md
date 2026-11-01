# G1S+B3：Thumb BX 快捷处理（save）

整理：碧蓝（代 CHONG 512 整理）。基础 GBARunner3 来自 Gericom 和原项目贡献者；相关 `slot2save` 分支来自 Wokann（卧看微尘）。本目录为在这些工作之上的社区实验材料，供作者审阅。

[save 项目入口](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/main/docs/SAVE.md) · [统一验证状态](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/main/docs/STATUS.md) · [版本与 SHA256](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/main/docs/VERSIONS.md)

## 实机测试（2026-10-30）

用户反馈 B3（patch）和 G1S+B3（save）两模式在 NDSL 实机体验良好；本页只记录对应产物，模型数值分开列出，不当作实机耗时。当前候选的保存、重启与原生 GBA 读档互通尚未逐项补录。

## 父本与改动

父本为 Wokann `cache-hicode/slot2save` @ `1f9b601395c96b0b62a7e0cffd9b7711ce6283bc` 加上 G1S m4a DMA 回绕。G1S 前置材料见 [PR #2](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/2)。

控制包逐字节复现 G1S_DMA_WRAP.nds。新增 B3 Thumb BX 快捷处理：`PrefetchAbort.s` 一处调用及 `CachedThumbBx.s`，目标范围为标准 EWRAM、IWRAM、低 ROM。DMA 修复保持原样。源码差异见 [G1S_B3_vs_G1S.patch](G1S_B3_vs_G1S.patch)。

## 已记录模型结果

绿宝石 BPEJ v1.13、save 模式：

| 首次翻卡 | G1S | G1S+B3 |
|---|---:|---:|
| 八地址配置 | 63 模型帧 | 41 模型帧 |
| 关闭 JIT | 41 模型帧 | 41 模型帧 |

SD 写入、存档变更为零；这组回放没有实际保存验证。详细记录见 [RESULT.md](RESULT.md)。

G1S 的“咔”声消失反馈属于音频版 G1S，不自动继承为本 G1S+B3 构建的声音验收。

## 产物与未测范围

候选 `G1S_B3_TEST.nds`，211968 字节，SHA256：

`74077023e82769f5a56fe8b091725d23042736d771b75df013d62aa196e30048`

NDS 不入库；[SHA256SUMS.txt](SHA256SUMS.txt) 和 build.json 按原构建记录保留。

已实机初步验证（仅绿宝石；火红叶绿未测）。测试前备份存档。存档往返、RTC、声音、其他游戏、完整动态 JIT、第二/三次翻卡，当前没有单独完整确认。不是上游已合入或正式发行的声明。

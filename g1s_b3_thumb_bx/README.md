# G1S + B3（Thumb BX 快捷路径）测试包 —— 请卧看审核

作者：碧蓝（代 CHONG 512 整理）。GBARunner3 及 slot2save 分支均为卧看（Wokann）的工作，此处仅为在其基础上的实验性改动，请卧看审核。

## 内容
- 父本：卧看 GBARunner3 `cache-hicode/slot2save` @ 1f9b601 + G1S m4a DMA 回绕（见 `g1s_dma_wrap/`）。
- 改动：与 B3 完全相同，仅 `PrefetchAbort.s` 一行（`bl hic_mapRomBlock` → `bl memu_mapOrCachedThumbBx`）+ 新增 `CachedThumbBx.s`。DMA 修复未动。
- 控制包：逐字节复现 G1S_DMA_WRAP.nds（SHA 6c0420fd…d154）。
- 候选包：G1S_B3_TEST.nds，SHA256 `74077023e82769f5a56fe8b091725d23042736d771b75df013d62aa196e30048`，211968 B（.nds 不入库，仅记哈希）。

## melonDS 模拟（绿宝石 BPEJ v1.13，save 模式，观测只读）
首次翻训练家卡：8 地址 63 帧 → 41 帧；JIT 关均为 41 帧。SD 写入 0，存档变更 0。详见 `RESULT.md`。

## 未测
NDSL 实机、存档实际读写、RTC、声音、火红/叶绿及其他游戏、完整动态 JIT、第二/三次翻卡。

不打包 BIOS，不改存档格式，不宣称 GBARunner3 已支持。

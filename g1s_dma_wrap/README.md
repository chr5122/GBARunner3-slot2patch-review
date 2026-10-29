# G1S_DMA_WRAP：slot2save 移植 m4a 声音 DMA 回绕

供 **卧看（Wokann）** 审阅。slot2save 方案的作者是卧看，上游仓库是 [Wokann/GBARunner3](https://github.com/Wokann/GBARunner3)，分支 `cache-hicode/slot2save`。感谢卧看的 slot2save 实现，以及 Gericom 和其他 GBARunner3 贡献者的基础工作。

这是在父本 `1f9b601395c96b0b62a7e0cffd9b7711ce6283bc` 上，只改 `DmaTransfer.c`，把补丁模式日常版 G1 的 m4a PCM DMA 回绕移植过来。请卧看先审核。同意之后，再向他的 `cache-hicode/slot2save` 提合并请求。这次不向 [Wokann/GBARunner3](https://github.com/Wokann/GBARunner3) 开合并请求。

本目录没有 BIOS、游戏 ROM、游戏补丁、存档或 `.nds` 本体。

## 是什么

日常版 G1（`G1_DMA_WRAP`）在补丁模式 slot2patch 上。这份构建把同一段 m4a 声音 DMA 回绕接到 slot2save，存档路径仍是 slot2save 原来的路径。没有新增 SD 写入，固件和时钟也保持原样。产物文件名是 `G1S_DMA_WRAP.nds`，日常版 `G1_DMA_WRAP.nds` 仍留在原处。

## 改动摘要

差异见 [g1s_vs_slot2save.diff](g1s_vs_slot2save.diff)。原文件名 `G1S_vs_slot2save_DmaTransfer.patch`，放入本目录时只改了名，字节未改。

- 新增 `M4A_PCM_BUF_SIZE 0x630`、`sSoundStart[3]`、`sSoundWrap`
- `dma_dmaSound`：源地址越过 0x630 时回绕到缓冲起点
- `dmaStartSound`：移出 ITCM，启动时记录起点，并判断双路 FIFO 是否为 m4a 布局

仅对识别为 m4a 双路 FIFO（间距 0x630）的声音 DMA 生效：DMA1 与 DMA2 都在声音 FIFO 模式，且 DMA2 的起始地址等于 DMA1 的起始地址加 0x630。每次启动都重新判断。

## 验证

2026-10-30 已实机验证：NDSL，save 模式，切场景的“咔”声消失。

[BUILD_INFO.json](BUILD_INFO.json) 是构建时的 `g1s_build.json`，字段原样保留。其中 `hardware_tested` 仍是 `false`，那是写出该文件时的状态。本页的实机结果没有回写进去。

## 产物

`G1S_DMA_WRAP.nds`：211968 字节，SHA-256 `6c0420fda11c0668a558e89f2c56cecbddf5df26e8e066fcc91c50cdd9fbd154`。

沿本仓库 G1 惯例，NDS 不提交。需要这个文件时索取。

已提交文件的 SHA-256 在 [SHA256SUMS](SHA256SUMS)，其中列出 `.nds` 与 diff 的哈希。在本目录执行 `sha256sum -c SHA256SUMS` 可以核对已提交的文件。该清单不含自身；自身哈希记在仓库根的 [SHA256.json](../SHA256.json)。diff 只改名、不改内容时，哈希不变。

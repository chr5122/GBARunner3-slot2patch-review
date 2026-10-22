# G1_DMA_WRAP — 切场景爆音记录

| | |
|---|---|
| Build | 记录中的 `G1_DMA_WRAP.nds`：227840 B，SHA-256 `eefe98a0d2369d18a78e02450e56a50a45c79e20b8f4887e2d1adc1e4063502d`。NDS 不在本仓库。 |
| Parent / 回退基线 | D2 `D2_AUTO_PRE.nds`：227328 B，SHA-256 `7965f4b1a2381a7ad325b1c618cc3b3511fc1287489291243cc8e296ddf6f76b` |
| Base | Wokann fork `cache-hicode/slot2patch` @ `f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9` |
| Change | ARM9 源码差异只有 `code/core/arm9/source/Peripherals/DmaTransfer.c`（补丁计 +17/−1）。见 [30_G1_vs_D2_review.patch](30_G1_vs_D2_review.patch)。 |

构建说明另记 ARM7 与 D2 相同。本仓库没有这两份 NDS，不能在这里再对 ARM7 做字节核对。

## 1. 观察到的现象

在这套 GBARunner3（含 slot2 存档的日版 ROM）上，宝可梦火红/叶绿切换场景时（例如岩山隧道进出），画面全黑、音乐已经淡出的瞬间出现“咔/啪”爆音。同一张正版卡在 NDSL 原生 GBA 模式下没有这声爆音。

## 2. 排查里已经记下的结果

1. **A1/A2**：A1 只留 PCM（Direct Sound）仍有爆音；A2 只留 PSG 则没有。当时把范围收到 PCM 路径。
2. **E1D/E1E/E1F**：FIFO 没有断供（E1F：A/B empty 0，最长连续空 0，长断供次数 0）；没有 FIFO RESET，也没有总开关切换（RESET 0，master 0）。相邻采样跳变：走路 D MAX 11136 / HI 65；切场景 D MAX 23808 / HI 292。
3. **F1S/F2S/F4S**：在 ARM7 混音输出端限制跳变，或加约 3 ms 线性过渡，对这声爆音基本无效（F2S 还把 BIOS 开机音拖慢）。当时的判断是：爆音更像一小段错误数据，而不是单个采样的阶跃。
4. **E1G**：抓取最大跳变前后 32 个混音采样。每个字为 `XXYYLLLL`（XX = FIFO B 原始字节，YY = FIFO A 原始字节，LLLL = 左声道输出）。

   ```
   00FEFF00 03FF0100 03FF0100 03FF0100 C8FEE300 C8FEE300 50FE2700 50FE2700
   50FE2700 BDFEDD80 BDFEDD80 00FDFE80 00FDFE80 BEFFDE80 BEFFDE80 BEFFDE80
   78FF3B80(jump) 78FF3B80 CDFFE600 CDFFE600 CDFFE600 0DFF0600 0DFF0600  then 9x 00000000
   CTX 04413302: SOUNDCNT_H=0x3302, master on, FIFO A cnt 4, FIFO B cnt 4, no DMA request
   ```

   淡出后的静音期间，A 停在 −1/−2（FE/FF），B 输出约 9 个看起来无规律的字节（03 C8 50 BD 00 BE 78 CD 0D），不到 1 ms。随后游戏清零缓冲并停 DMA，采样变成全 0。

## 3. 推断出来的原因

`dma_dmaSound()` 每次 FIFO 请求从 `curSrc` 搬 16 字节，然后 `curSrc += 16`。`curSrc` 只在 DMA 启动时从 SAD 锁存，没有上限，也不回绕。这段只增不回绕的逻辑在 fork 基点 `f8ac25c` 里已经存在，源自上游 Gericom 的 GBARunner3 代码。有说法称它自 2023 年起就是这样；这一点没有在本记录里重新核实。

m4a 的 PCM 缓冲 `PCM_DMA_BUF_SIZE` 为 0x630（1584 B），FIFO B 的缓冲位于 FIFO A 的缓冲加 0x630。游戏在 VBlank 里每隔若干帧停开 DMA，把读取位置拉回开头。13379 Hz 下一个周期大约用掉 1568 B，余量大约 16 B。

与 E1G 波形和上述代码相符的推断是：切场景时，slot2 卡带读取或载入让模拟的 VBlank 处理偏晚，DMA 在被拉回之前读过了缓冲末尾。A 读进 B 的缓冲时仍是安静数据，听不出来；B 读进缓冲之后的无关内存，短促的乱码字节成为爆音。同一卡带在原生 GBA 模式没有这声爆音。**VBlank 迟到是推断出来的原因**，本记录没有单独测量 VBlank 时刻。专门统计越界次数的 E1H 曾经构建，没有上机跑。G1 实机上爆音消失，与这个推断相符，并不把它证实成唯一原因。

是否影响原版 GBARunner3 尚未测试。本机结果停在这条 fork 上。

## 4. G1 改了什么

`dmaStartSound()` 每次启动 DMA 时记下该通道的起始 SAD。只有 **m4a 特征**成立时才打开回绕：DMA1 和 DMA2 都处于声音 FIFO 模式，且 `DMA2 SAD == DMA1 SAD + 0x630`。每次启动或重启都重新判断。

`dma_dmaSound()` 在每次搬 16 B 之前，若 `curSrc - SAD >= 0x630`，就把 `curSrc` 拉回 SAD。0x630 = 99×16，回绕点和 16 B 步进对齐。

源码注释里的 “If the game's VBlank restart is late” 写的是上一节的推断。

D2 的 ITCM 剩余 8 B。G1 把 `dmaStartSound()` 从 ITCM 移到 EWRAM，并标成 `noinline`。它在游戏启动 DMA 时调用，不在每次 16 B 搬运的路径上；ITCM 经链接器跳转桩调用它。

布局副作用见 [MAP_DIFF_SUMMARY.md](MAP_DIFF_SUMMARY.md)：`.ewram` 越过 16 KiB 后，4 KiB 对齐的 `.ewram.bss` 从 `0x02044000` 挪到 `0x02045000`，堆从约 20 KiB 降到约 16 KiB。随附审查称没有写死 `0x02044000`。本仓库的 `source/` 不是完整构建树，没有在这里重做全库地址搜索。

非 m4a、或只有一路声音 DMA 时，回绕保持关闭，这条路径与 D2 相同。

## 5. 随附静态审查，以及本仓库复核了什么

随附审查记下四项，结论是通过：

1. 内存布局：没有写死 `0x02044000`；crt0 和堆使用链接器符号；各段不重叠。
2. 回绕边界：非 m4a、单路 DMA、中途重启、修改 SAD、固定步进按该审查是安全的。递减步进同时又满足 m4a 特征，被标成理论风险。
3. 移出 ITCM：只在启动 DMA 时调用。D2 里已有 ITCM 调 EWRAM 的跳转桩（例如 `gbas_writeSoundRegister`）。调用前会先执行 `ic_invalidateAll`。
4. 相对 D2 的源码差异只有 `DmaTransfer.c`。存档、slot2、`.pre` 读取和运行期 SD 只读不在这个补丁里。

本仓库另外核对了两件事：

- `git apply -p1 --check 30_G1_vs_D2_review.patch` 可以通过。补丁应用到 D2 的 `DmaTransfer.c` 之后，结果与 G1 全文逐字节相同。D2 全文 SHA-256 `16bf3c402aa1bab06411cb2eadd0f7abdfdfa220b8fdc758060113b744159751`，G1 全文 SHA-256 `750fd43e19e76617b3eff4e5799352b1a65ecc091afeb68868edfab861127b9d`。
- [MAP_DIFF_SUMMARY.md](MAP_DIFF_SUMMARY.md) 里的段地址和长度与当时的 arm9 map 段行一致。

`source/` 下没有 `DmaTransfer.c`。D2 的阅读副本只收了相对上游有改动的文件，这个文件不在其中，所以没有往 `source/` 放入 G1 版本。

## 6. 用户实机反馈

用户确认：切场景没有爆音；长时间游玩正常；存档写回正版卡。证据等级与 [FIELD_TESTS.md](FIELD_TESTS.md) 的其他条目相同，是用户反馈。BIOS 开机音、宝可梦叫声和战斗音效没有被单独记成已确认项。

## 7. 尚未构建的可选加固

开启回绕时再要求 DMA 源地址是递增步进（`srcStep == +1`），用来排除“递减步进碰巧满足 m4a 布局”的理论情况。这一步还没有构建。

## 8. 和上游代码的关系

只增不回绕的 `curSrc` 在 fork 基点 `f8ac25c` 中已经存在，源自上游 Gericom 的代码。是否影响原版 GBARunner3 尚未测试。这里不把本机 G1 的结果写成原版已经复现，或原版已经排除。

## 相关文件

- [30_G1_vs_D2_review.patch](30_G1_vs_D2_review.patch)：D2 → G1 的 `DmaTransfer.c` 差异，取自构建时的 `diff -ru`。在已含 D2 文件的树根上用 `git apply -p1`。
- [MAP_DIFF_SUMMARY.md](MAP_DIFF_SUMMARY.md)：ARM9 map 摘要。全文 map 含本机构建路径，未放入本仓库。
- [BUILD_REVIEW.md](BUILD_REVIEW.md)、[FIELD_TESTS.md](FIELD_TESTS.md)：追加的构建套用说明和实机反馈。

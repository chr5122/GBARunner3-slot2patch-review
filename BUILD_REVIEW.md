# 如何核对这份源码差异

本仓库不是可独立构建的完整 checkout。先从 Wokann/GBARunner3 获取固定提交和子模块，再应用 **20_FULL_vs_f8ac25c_review.patch**。

```sh
git clone https://github.com/Wokann/GBARunner3.git
cd GBARunner3
git checkout f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9
git submodule update --init --recursive
git apply --check /path/to/20_FULL_vs_f8ac25c_review.patch
git apply /path/to/20_FULL_vs_f8ac25c_review.patch
```

libtwl 固定提交应为 e069645bed14a93e149e873e9273f04851e3a04e。
完整差异含所有新增源文件、font include 和 linker 修改；没有游戏 ROM、PRE、BIOS 或存档。
不要再应用 D1 → D2 的 10_ patch，两个是不同基准的替代视图。

沿用上游 Makefile 和 devkitARM/libnds/libtwl 构建方式（code/ 下 make）。
实测候选使用本地 devkitARM r65/GCC 14.2、libnds 1.8.3、ndstool 2.3.1；原上游 CI 镜像为 devkitpro/devkitarm:20241104。
本仓库不安装/分发 SDK。不同工具链输出和菜单 banner 不保证二进制同哈希；实测 NDS 的菜单标题在链接后另行定制。

重编译不是自动继承实测结论：本构建 VRAM 尾部余量仅 268 B，EWRAM 代码距原 BSS 起点仅 56 B。
必须核对 ELF/map 段界限、2 KiB hicode 对齐、关键 EWRAM BSS 地址、1 MiB cache、20 KiB heap 和栈使用，再做独立实机短测。
本包的 PATCH_VERIFICATION.json 证明差异 apply 后内容正确，不是新工具链构建/运行已经成功的保证。

source/ 目录只是变更文件的网页阅读副本，非完整构建树。
构建/主机/布局检查的说明见 IMPLEMENTATION.md；907 条检查多数是逐文件校验，不是 907 个实机场景。

## G1_DMA_WRAP（套在 D2 树上）

上面按 20_ 得到的是 D2 源码树。G1 的补丁是 [30_G1_vs_D2_review.patch](30_G1_vs_D2_review.patch)，父本是这份 D2，只涉及 `code/core/arm9/source/Peripherals/DmaTransfer.c`。它与 10_、20_ 的基准都不同，单独套用。

补丁来自 `diff -ru`，路径带 `d2_source/` 与 `g1_source/` 前缀。在已经含有 D2 版该文件的检出根目录：

```sh
git apply --check -p1 /path/to/30_G1_vs_D2_review.patch
git apply -p1 /path/to/30_G1_vs_D2_review.patch
```

本仓库已做这次核对：应用到 D2 全文后，结果与 G1 全文逐字节相同。`source/` 没有 `DmaTransfer.c`，因此没有把 G1 版本放进阅读副本。细节和哈希见 [G1_AUDIO_POP_FIX.md](G1_AUDIO_POP_FIX.md)。

记录中的 G1_DMA_WRAP.nds 为 227840 B，SHA-256 `eefe98a0d2369d18a78e02450e56a50a45c79e20b8f4887e2d1adc1e4063502d`。回退基线仍是 D2（227328 B，`7965f4b1a2381a7ad325b1c618cc3b3511fc1287489291243cc8e296ddf6f76b`）。两份 NDS 都不在本仓库。随附构建说明称 ARM7 与 D2 相同，且没有新增诊断、SD 写入或存档路径改动；源码补丁本身只有 `DmaTransfer.c`。

G1 的链接布局相对 D2 有变化：`.ewram` 越过 16 KiB 后，`.ewram.bss` 从 0x02044000 移到 0x02045000，堆从约 20 KiB 降到约 16 KiB，`dmaStartSound` 改放到 EWRAM。上文 D2 的 VRAM 尾部余量 268 B、EWRAM 代码距原 BSS 起点 56 B，是 D2 的数字。重编译 G1 后仍要核对 ELF/map、2 KiB hicode 对齐、BSS、1 MiB cache 和堆。摘要见 [MAP_DIFF_SUMMARY.md](MAP_DIFF_SUMMARY.md)。

VBlank 迟到是推断出来的原因。不回绕的 `curSrc` 源自上游 Gericom 的代码；是否影响原版 GBARunner3 尚未测试。


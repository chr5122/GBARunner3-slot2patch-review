# B3：Thumb BX 快速路径（目标限 EWRAM / IWRAM / 低 ROM）—— 请卧看审核

这是 GBARunner3 `slot2patch` 上的 **B3** 实验材料，供原作者 **卧看（Wokann）** 审核。GBARunner3 与 slot2patch 都是卧看的工作；这里只是在其基础上的实验记录，不是正式发行，也不表示上游已经采纳。

## 实验

在 Thumb 预取异常路径上加一条 BX 快速路径：

- 只处理 `BX r0`、`BX r1`、`BX r2`、`BX r3`。
- 目标地址只限三段：标准 EWRAM（`0x02000000`–`0x0203FFFF`）、标准 IWRAM（`0x03000000`–`0x03007FFF`）、低 2MB ROM（`0x08000000`–`0x081FFFFF`）。
- 其余指令和其余地址（含内存镜像、DS 私有内存和搬移地址）全部回到原有映射/执行路径。

对照包是 **R1**。`SOURCE.patch` 是相对 R1 的差异：`PrefetchAbort.s` 改一处调用，并新增 `CachedThumbBx.s`。`B2_TO_B3.patch` 是相对 B2 只收紧目标范围的差异。材料写明本实验不改存档、声音、SD 和 JIT/MSR/IRQ。

## 二进制

`B3_THUMB_BX_STRICT_RAM_TEST.nds` **不入库**，只记哈希。

SHA256 前缀：`f2d5f8be…dbad`（228,352 字节；完整值在 `build.json`）。

## 验证

**尚未实机验证。** 目录里的指令测试和电脑回放不能代替 NDSL 实测。上机前请先备份存档。

设计、复测和独立复核见 `DESIGN.md`、`REPORT.md`、`B3_INDEPENDENT_REVIEW.md`。正式基线仍是 R1。

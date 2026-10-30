# B3 独立复核（2026-10-30）

对象：`gbr3_thumb_bx_strict_ram_20261030/output/B3_THUMB_BX_STRICT_RAM_TEST.nds`
SHA256 `f2d5f8bedf024a694b00ee3bcb1eaebdda2eb21644b20e06c063f5f499f5dbad`（核对一致，228,352 字节）。
R1/B2/B3 原目录未写入任何文件；未运行会改写 B3 `validation/verification.json` 的 `verify.py`。未上传、未改默认、未升基线；无实机/卡带/固件操作。

## 结论
没有发现正确性缺陷。B3 相对 B2 只改了目标范围判断，三段白名单实现正确，边界、下溢、DS 私有区和 0x022xxxxx 均完整回退。38/37/37、mapNewBlock 1376/1438/1471、1388/770 全部独立复现，且回放输出与原 B3 运行逐字节一致（仅 launch.json 路径、stderr 不同）。**可以作为 NDSL 对照候选（绿宝石场景）**，正式基线仍为 R1。

## 1. 相对 B2 的差异范围（独立确认）
- 源码：B2→B3 全树（.s/.c/.cpp/.h/.inc/.ld/Makefile）只有 `CachedThumbBx.s` 不同；diff 只在范围判断段及注释（与 `B2_TO_B3.patch` 一致）。函数入口、模式/对齐检查、缓存查表、`ldrh` 取实际缓存内容、BX 编码判断、寄存器取值、T 位/对齐处理、`str [sp,#20]`、`msr spsr`、回退 `ldr pc,=hic_mapRomBlock` 全部不变。
- 二进制：B2/B3 core ELF 各 1626 个函数，1475 个字节完全相同，149 个仅地址差异（helper 由 188→196 字节，其后符号平移 8/12 字节，原因是链接对齐），语义不同的只有 `memu_mapOrCachedThumbBx` 本身和 `_init`（后者只是尾部少了一个 0xffffffff 对齐填充字）。见 `analysis/disasm_diff_summary.txt`、`analysis/nm_shift.txt`。
- `validation/helper.bin`（sha 37c6b7d4…7b87）在 B3 NDS 中恰好出现 1 次，确认单元测试执行的是实际打包的字节。

## 2/3. 范围判断审查
```
cmp r2,#0x08000000 ; blo 2f
cmp r2,#0x08200000 ; bhs 9f(回退) ; b 1f(放行)
2: sub r3,r2,#0x02000000 ; cmp r3,#0x40000 ; blo 1f
   sub r3,r2,#0x03000000 ; cmp r3,#0x8000  ; bhs 9f
1: ...
```
- 正好放行 [0x02000000,0x02040000)、[0x03000000,0x03008000)、[0x08000000,0x08200000)。
- 下溢：target<base 时 `target-base` 无符号为极大值，`cmp/blo|bhs` 判为越界，正确；三段均不跨 2^32 回绕。
- r3 被覆盖不影响后续（之后只用 r1/r2），与 B2 一致。
- 自补单元用例（`unit/unit_bx_extra.cpp`，在原 unit_bx 后追加，不改原计数）：46 个目标 × 4 寄存器 × 4 取指 PC × 3 组标志，包括 0x0、0x1、0x01FFFFFF、0x0203FFFF/0x02040000/0x02040001、0x02200000/0x02200001/0x022FFFFF、0x027FF000/0x027FFFFF、0x02400000/1、0x02800001、0x02FFFFFF、0x03007FFF/0x03008000/0x03008001、0x03800000/1、0x0380FFFF、0x03FFFFFF、0x04000000/1、0x05000001、0x06000000、0x06800001、0x07000001、0x07FFFFFF、0x081FFFFF、0x08200000/1、0x09FFFFFF、0x0A000001、0x0DFFFFFF、0x0E000001、0x0FFFFFFF、0x80000001、0xFFFF0000/1、0xFFFFFFFE、0xFFFFFFFF；外加 ARM 目标 bit1=1 / bit1=0 的 9 个地址 × 16。
  结果：**新增 288 组原生等价、2064 组完整回退，全部通过**（合计 1676/2834）。私有 melonDS ARM946 解释器（irq_attribution model_build），见 `unit/extra_b3.json`。
- ARM 目标 bit1=1：helper `bic #3`，与该解释器的原生 BX 一致；ARMv5 上这属于架构未定义行为（UNPREDICTABLE），模型等价不代表实机必然一致。游戏回放中所有快捷目标都是 Thumb（bit0=1），没有遇到。

## 4. 独立复现
- 原 unit_bx 重跑：1388 等价 / 770 回退，pass。
- 回放（`run_independent_case.py`，沿用 B2 复核方法，只换 NDS 与输出目录）：

| 指标 | R1 | B2 | B3 原报告 | **B3 本次复核** |
|---|---|---|---|---|
| 八地址三次翻卡（模型帧） | 60/81/127 | 39/37/37 | 38/37/37 | **38/37/37** |
| 首窗 mapNewBlock | 24,219 | 1,416 | 1,376 | **1,376**（后两窗 1,438/1,471，与 B2 相同） |
| 关 JIT 首翻 | 38 | 37 | 37 | **37** |
| 观察器关闭首翻 | – | – | 38 | **38**，14 项检查点状态逐字节一致 |
| 八地址 helper 调用/快捷/回退/错误 | – | 212,754/90,820/121,934/0 | 同右 | **212,484/90,554/121,930/0** |
| 关 JIT 调用/快捷/回退 | – | 120,463/48,292/72,171 | 同右 | **120,454/48,287/72,167** |
| SD 写/保存请求/存档变化 | 0 | 0 | 0 | **0/0/0**，PRE 前后逐字节一致 |
| 关键帧与 R1 参考图 | – | 一致 | 9 项一致 | **9 项一致**（2494/2677/3226/3775/4021 + off 2494/2677） |

- 输入哈希全部符合 `INPUTS.json`：BPEJ00.gba 33f5610b…343c、bios fd254772…6570、cn113/BPEJ00.patch 5f2b3789…bb3bb、BPEJ00_native16.pre 17b92398…602、flash128k.sav 8567d397…4c72、config8.json 5c10f190…ed4e；按键回放 keys.txt 6737718e…8a4e（与 B2 复核同一份），关 JIT 用截短版 c370f05c…41b7。
- B3 快捷目标全部落在低 ROM（0x0800xxxx–0x0819xxxx）。B2→B3 快捷次数少 266 次，**并非有目标被新判断拒绝**：B2 的快捷目标同样全在低 ROM，差异来自首窗少一帧带来的调用总数变化。

## 5. 性能代价（静态估计，非实测）
- 低 ROM 目标：B2 需 8 条判断，B3 为 4 条 + 1 次跳转，不更慢。EWRAM 约 5 条，IWRAM 约 7 条，略多于 B2 但可以忽略。
- 范围判断在 BX 编码判断之后，非 BX 回退（占绝大多数）的路径与 B2 完全相同。
- 相对 R1 的纯回退开销：非 BX 回退要多走约 23 条指令（含 3 次读取，其中 1 次查缓存表）再进 `hic_mapRomBlock`。**未测**：本场景快捷命中太多，无法单独量化；需要一个几乎不命中的游戏或一个只计开销的只读观察器。

## 发现的问题 / 注意事项（都不阻塞）
1. 原单元测试的期望值（supportedTarget）和实现出自同一份规格，不是独立预言；本次另按规格手审汇编，并加了 2352 组用例补上这一点。
2. B2 与 B3 的 `runner_attribution` 源码相同，二进制哈希却不同（f3a734c2… 与 2abce743…），应是重新编译所致。观察器关闭时状态一致，回放结果也确定可复现，因此不影响结论，但跨版本比较帧数时用的不是同一个可执行文件。
3. ARM 目标 bit1=1 的行为只与模型等价（见上）。

## 未测
火红、叶绿及其他游戏；全动态 JIT；slot2save 构建；EWRAM/IWRAM 目标在游戏中的真实命中（仅单元覆盖）；真实 IRQ 注入及 MPU/缓存时序；纯回退开销；实际存档与回原生 GBA 读档；NDSL 实机。

## 是否上 NDSL 实机
值得，条件如下：只测绿宝石 BPEJ + 中文 v1.13 + 八地址配置；用 R1 作对照；测反复翻卡、战斗、菜单/地图切换、声音；先备份存档；不升基线、不设默认。其他游戏要等各自有了核对过哈希的输入并复测后再说。

## 复现
```
cd /Users/chong/Documents/Codex/2026-08-20/git-status
python3 gbr3_b3_independent_review_20261030/run_independent_case.py eight_long   # 及 off / observer_off（输出目录需不存在）
gbr3_thumb_bx_strict_ram_20261030/validation/unit_bx gbr3_thumb_bx_strict_ram_20261030/validation/helper.bin
gbr3_b3_independent_review_20261030/unit/unit_bx_extra gbr3_thumb_bx_strict_ram_20261030/validation/helper.bin
```
编译 extra：`clang++ -std=c++17 -O2 -fwrapv -DARCHITECTURE_ARM64=1 -I gbr3_irq_attribution_20261030/model_source/src -I …/model_build/src unit_bx_extra.cpp B3/validation/platform_romopt.cpp …/libcore.a …/libteakra.a`。
汇总：`analysis/replay_summary.json`、`analysis/b2_b3_bx_compare.txt`、`analysis/hashes.txt`。

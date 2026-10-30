# GBARunner3 B2 短跳转优化 — 独立复核报告

- 复核目录：`gbr3_b2_independent_review_20261030/`
- 复核日：2026-10-30（Asia/Shanghai）
- 立场：证据优先，可推翻原结论；不修改原 R1/B2；不上传、不升基线、不写卡带/固件。

---

## 1. 结论摘要

| 项 | 结论 |
|---|---|
| 实现范围 | **确认**：仅改 `PrefetchAbort.s` 一处 BL + 新增 `CachedThumbBx.s`；ARM7 逐字节一致 |
| BX 编码识别 | **确认正确**：只接受 `0x4700/4708/4710/4718`；不误认 BLX / BX r4+ / JIT 改写形 |
| 绿宝石八地址三次翻卡 | **独立复现** R1 `60/81/127` → B2 `39/37/37`；mapNewBlock 首窗 `24219` → `1416` |
| 画面/观察器 | **通过**：五个关键帧 ppm 与 R1、B2 原跑一致；observer_off 帧与状态一致 |
| 指令单元 | **复跑通过**：812 等价 + 290 回退；私有 melonDS ARM946，非 Unicorn |
| 正确性缺陷（阻塞） | **未发现**足以否定绿宝石场景正确性的缺陷 |
| 残余风险 | **有**：WRAM 目标窗过宽（见 §4）；低位 ROM 可能多一次线性 remap（性能，非错） |
| 火红/叶绿/其它 | **未测**（本树无对等固定回放输入） |
| 是否值得 NDSL 实机 | **有条件：是** — 先做绿宝石八地址翻卡对照；升基线前建议收紧 WRAM 窗 |

---

## 2. 版本与输入哈希（已核实）

### 2.1 NDS

| 角色 | 路径 | SHA256 | 字节 |
|---|---|---|---|
| R1 基线 | `gbr3_read_guard_r1_20261029/output/GBARunner3_R1_SD_READ_GUARD.nds` | `46eda7a79321bb24213b8d39f4e77079e84bb0cc3436cc5964749aaeb134d808` | 228352 |
| B2 候选 | `gbr3_thumb_bx_lowtarget_20261030/output/B2_THUMB_BX_LOWTARGET_TEST.nds` | `c9b8492b2a583a3112de5b99b98d26da271320d81a0cb61a3fe4b40d462ce10d` | 228352 |

未使用 `gbr3_thumb_bx_research_20261030` 的 B1。

### 2.2 固定游戏输入（`gbr3_melonds_feasibility_20261028/game_inputs/`）

| 文件 | SHA256 |
|---|---|
| `BPEJ00.gba` | `33f5610b9186b4add09fef68895deb00f552b997b3d133b5a961e5123506343c` |
| `bios.bin` | `fd2547724b505f487e6dcb29ec2ecff3af35a841a77ab2e85fd87350abd36570` |
| `cn113/BPEJ00.patch` | `5f2b37897367e9bdc78c8a460053a10b518d647c6ec464378fa89dcb2b0bd3bb` |
| `cn113/BPEJ00.pre` | `f346282f5792d804fcabb2ff813e462065f482995b75c03604a1e17dca3cd0c7` |
| `user_save/BPEJ00_flash128k.sav` | `8567d3975e5f85b05bb4630c240fc8cab7cffd889ff5ab8f2f78065544264c72` |
| `user_save/BPEJ00_config8.json` | `5c10f190b28b4f6e791a8338f439c9ed96a6cc3d5d7c1166e86eee4cef8aed4e` |

复跑脚本：`run_independent_case.py`（调用 B2 目录既有 runner，输出写到本复核 `validation/`）。

---

## 3. 实现审查（独立，不只跑 verifier）

### 3.1 改动面

`SOURCE.patch`（78 行）与源树 diff 一致，仅：

1. `PrefetchAbort.s`：`bl hic_mapRomBlock` → `bl memu_mapOrCachedThumbBx`
2. 新增 `CachedThumbBx.s`（约 184B VRAM + 链接器 8B ITCM veneer）

构建仍断言并省略末尾 228 字节诊断尾；功能复制长度 `131300`，core `131528`。ARM7 段一致。未改游戏/补丁/PRE/存档/ARM7/音频/MSR·IRQ/八地址 JSON。

### 3.2 BX r0–r3 编码

条件：`(inst & ~0x18) == 0x4700` → 仅 `0x4700/08/10/18`。

| 指令 | 编码 | B2 |
|---|---|---|
| BX r0–r3 | 0x4700–0x4718 | 接受 |
| BX r4–r15 | ≥0x4720 | 回退 |
| BLX Rm | 0x4780 系 | 回退 |
| JIT 改写形 | `0xB100\|(Rm<<4)` | 回退 |

证据：`analysis/encoding_audit.txt`；单元 `logs/unit_bx_rerun.json`（812/290）。

Guest Rm 从 abort 帧 `[sp + (Rm*4)]` 读取（`push {r0-r3,r12,lr}`），与 handler 临时 r1/r2/r3 分离；**整段快路径不改写 r0**，回退 `ldr pc,=hic_mapRomBlock` 时 r0 仍为故障 PC。

### 3.3 缓存内容

`ldrh` 来自 `sdc_romBlockToCacheBlock` 已命中块；未命中则回退，**不**在此发 SD 读或 `mapNewBlock`。读到的是补丁/既有流程写入 cache 的实际字节。JIT 原地改写 BX 后，B2 因编码不匹配必回退（见 `analysis/jit_interaction_note.txt`）。

### 3.4 CPSR / 对齐 / 模式

- 入口要求 SPSR 模式字节 `0x30`（User + Thumb）；否则回退。
- 按目标 bit0 只改 SPSR.T；`msr spsr_cxsf` 保留 NZCVQ 与 IRQ/FIQ mask、其它模式位。
- ARM：`bic #3`；Thumb：`bic #1`。
- 写回仅 `[sp,#20]`（retry PC）+ SPSR；**不扩栈**；银行寄存器不碰；返回仍走原 `ldmfd … pc^`。

### 3.5 回退完整性

不适用（非 User+Thumb、非半字对齐 ROM 故障 PC、cache miss、非 BX r0–r3、目标不在窗内）均 `9: → hic_mapRomBlock`。高位→高位跳板不走快路径（目标 ≥`0x08200000` 回退），避免 B1 类饥饿问题。

### 3.6 JIT / undefined / 缓存替换

- 块被 JIT 改写后：B2 不命中 → 原路径（含 `hic_undefinedHicodeMiss` → `hic_mapRomBlock`）。
- 快路径**不**对目标做 ensure-jitted；目标按原生 GBA 语义执行直到其它路径 JIT——语义正确，可能少一次 JIT 机会（性能偏好，非错误）。
- 快路径不碰 LRU/发布；块被替换后下次 miss 自然回退。
- 全动态 JIT 其它游戏：**未测**。

### 3.7 目标范围（发现问题）

允许：

- `0x02000000 ≤ tgt < 0x04000000`（整窗「工作 RAM」）
- `0x08000000 ≤ tgt < 0x08200000`（低 2MB ROM）

**问题 A（中，正确性/安全边界）**  
真机 GBA：EWRAM 仅 `0x02000000–0x0203FFFF`，IWRAM 仅 `0x03000000–0x03007FFF`。DS 上 `0x02200000` 起是 GBR3 线性 ROM 镜像与主存；`0x03008000–0x03FFFFFF` 在 MPU 上被标成大块 IWRAM 区。若 guest `BX` 落到这些地址，B2 会放行并 `LDM^` 进去，可能执行宿主映射内容。真 GBA 无对应有效代码。  
**本轮绿宝石实测**：90820 次快路径目标 **100% 低位 ROM**，0 次落入可疑 WRAM 缝（`analysis/target_range_audit.txt`）。故 **不否定本场景结果**，但 **升基线前应收紧**。

**建议最小修复（副本上改，勿动原 B2）：**

```
EWRAM: 0x02000000–0x0203FFFF
IWRAM: 0x03000000–0x03007FFF
low ROM: 0x08000000–0x081FFFFF（保持）
```

**问题 B（低，性能）**  
快路径把 **GBA** 低位 ROM 地址写入 retry PC。`PrefetchAbort` 线性路径会把 `0x08xxxxxx` 转成 `0x022xxxxx` 再跑。因此快→低 ROM 可能仍多一次**廉价**线性 abort，但已避开昂贵 `mapNewBlock`。可在 B2 内直接写 DS 地址以再省一次（可选优化，非正确性必须）。见 `analysis/lowrom_resume_note.txt`。

### 3.8 ITCM / VRAM / 228 尾

ITCM veneer +8B，未破 32KB；VRAM 新函数在既有 `.text`；228 诊断尾省略策略与 R1 构建断言一致，**安全**。

### 3.9 中断饥饿 / 嵌套

快路径立刻回到 guest，不再为该 BX 建 hicode 映射；嵌套仍走原 abort 栈。绿宝石窗内 `gba_dispatches ≈ gba_returns`，无异常堆积迹象。无独立 IRQ 注入测试（单元限制已写明）。

---

## 4. 独立复测结果

引擎：私有 melonDS ARM946（Unicorn 本机映射崩溃，**不**把工具故障算成候选故障）。

### 4.1 八地址 · 三次翻卡（`validation/eight_long/`）

| 指标 | R1 | B2 独立 | B2 原跑 |
|---|---|---|---|
| 翻卡帧 | 60 / 81 / 127 | **39 / 37 / 37** | 39 / 37 / 37 |
| mapNewBlock（三窗） | 首窗 24219（audit `eight`） | **1416 / 1438 / 1471** | （与独立一致） |
| bx entered / fast / fallback / err | — | 212754 / 90820 / 121934 / **0** | 同 |
| 翻卡窗 bx fast | — | 24902 | 同 |
| SD 写 / 存档变更 | 0 | **0 / 0** | 0 |
| 关键帧 ppm vs R1 | — | **5/5 一致** | 5/5 |

原始对照 JSON：`analysis/eight_long_compare.json`。  
日志：`logs/run_eight_long.stdout`（墙钟约 271s，rc0）。

### 4.2 关 JIT（`validation/off/`）

| 指标 | R1 | B2 独立 |
|---|---|---|
| 首窗帧 | 38（attribution 三窗 38/36/37） | **37** |
| mapNewBlock | 3467（audit） | **1349** |
| bx fast/fallback/err | — | 48292 / 72171 / 0 |

关 JIT 时 BX 不被改写，快路径仍大量命中；帧数与 R1 同量级并略好，**未见回退检查拖慢到差于 R1**。

### 4.3 观察器关闭（`validation/observer_off/`）

首窗 **39** 帧；与 B2 开观察器八地址首窗一致；既有 14 项状态检查在原 `verify.py` 复跑中通过（`logs/verify_rerun.json`）。观察器为只读计数，不改模拟时间语义（与 B2 设计一致）。

### 4.4 性能解读（非 NDSL 实机时间）

- 收益主要来自：**高位 ROM 上 BX→低位 ROM/工作区时跳过反复 `mapNewBlock`**。
- 不是笼统「全面 FPS+」；热点与 `gbr3_hicode_mapping_audit_20261030` 描述一致。
- 模型帧 ≠ 实机毫秒；实机槽2延迟仍可能不同。

---

## 5. 通用性与回退成本

| 对象 | 状态 |
|---|---|
| BPEJ 日版绿 + 中文 v1.13 + 八地址 | **已独立复测** |
| 同配置关 JIT | **已测** |
| 火红 / 叶绿 / 其它 | **未测** — `game_inputs` 仅有 BPEJ；不凭源码推断通过 |
| 全动态 JIT 配置 | **未测** |
| save 模式 / 实卡存档 | **未测**（本轮无存档写入，符合诊断约束） |
| NDSL 实机 | **未测** |

回退成本：每次 abort 多一轮 SPSR/编码/cache 探查；绿宝石关 JIT 与八地址下净收益仍明显，**本场景未见净负**。其它游戏需有固定回放后再测。

---

## 6. 是否进入 NDSL 实机

**有条件：是。**

条件：

1. **实机包**：仅用已哈希的 `B2_THUMB_BX_LOWTARGET_TEST.nds`，对照 `GBARunner3_R1_SD_READ_GUARD.nds`；同一 BPEJ + cn113 + 用户存档 + 八地址配置。
2. **必测**：训练家卡翻面三次手感/是否花屏错乱；进战斗、开关菜单、保存一次（确认存档格式仍为日版兼容，本优化不应改存档路径）。
3. **通过后再谈升基线**；升基线前在**副本**上落地 WRAM 窗收紧（问题 A），再跑同一套模型回放确认帧与画面不回退。
4. 不把 B2 当默认包分发；不上传 GitHub，除非用户另行授权。

若实机出现与 R1 不同的死机/错跳，保留 `.nds` 哈希与复现步骤，优先怀疑目标窗或低 ROM resume，而不是先放宽正确性。

---

## 7. 缺陷与修复建议（不改原 R1/B2）

| ID | 严重度 | 触发 | 建议 |
|---|---|---|---|
| A | 中 | guest BX 目标落入 `0x02040000–0x02FFFFFF` 或 `0x03008000–0x03FFFFFF` | 收紧为真 EWRAM/IWRAM 边界（见 §3.7） |
| B | 低 | 快路径目标为低位 ROM | 可选：写入 `tgt - 0x08000000 + 0x02200000` 免一次线性 remap |
| C | 信息 | JIT 后 BX 走 undefined，不经 B2 | 设计如此；若要 JIT 后仍加速需另案，不在本优化范围 |

未发现：BLX 误认、guest/handler 寄存器互相污染、SPSR 其它位被清、回退丢 r0、扩栈、改存档/SD 写、动 ARM7。

---

## 8. 可复现步骤

```bash
# 在 Mac，工作根 git-status
REV=gbr3_b2_independent_review_20261030
B2=gbr3_thumb_bx_lowtarget_20261030

# 哈希
shasum -a 256 gbr3_read_guard_r1_20261029/output/GBARunner3_R1_SD_READ_GUARD.nds
shasum -a 256 $B2/output/B2_THUMB_BX_LOWTARGET_TEST.nds

# 单元 + 官方 verifier（B2 目录）
python3 $B2/verify.py   # 或复跑日志 logs/verify_rerun.json

# 独立 case（本目录脚本）
python3 $REV/run_independent_case.py eight_long
python3 $REV/run_independent_case.py off
python3 $REV/run_independent_case.py observer_off
```

产物：`validation/{eight_long,off,observer_off}/`，分析见 `analysis/`，日志见 `logs/`。

---

## 9. 独立确认的事实 / 问题 / 未测（清单）

**事实**

- 源码改动面与设计一致；编码白名单正确；单元与绿宝石回放独立复现原报告数量级收益。
- 画面与 R1 关键帧一致；无 SD 写、无存档脏字节；观察器开关不改变帧结论。
- 快路径在本场景几乎全是「高位 BX → 低位 ROM」。

**问题**

- WRAM 目标窗过宽（A）；低 ROM resume 可再省一次 abort（B）。

**未测**

- 火红/叶绿/其它游戏；全动态 JIT；NDSL 实机；长时间游玩；故意 cache 失效压力；真 IRQ 注入。

---

## 10. 文件索引

| 路径 | 说明 |
|---|---|
| `REVIEW.md` | 本报告 |
| `SOURCE.patch` | B2 补丁副本 |
| `run_independent_case.py` | 独立复跑入口 |
| `analysis/eight_long_compare.json` | R1/B2 帧与画面对照 |
| `analysis/encoding_audit.txt` | 编码白名单 |
| `analysis/target_range_audit.txt` | 快路径目标分布 |
| `analysis/lowrom_resume_note.txt` | 低 ROM 返回路径 |
| `analysis/jit_interaction_note.txt` | 与 JIT 交互 |
| `logs/unit_bx_rerun.json` | 单元复跑 |
| `logs/verify_rerun.json` | verifier 复跑 |
| `logs/nds_sha256.txt` | NDS 哈希 |
| `validation/eight_long/` | 八地址长回放 |
| `validation/off/` | 关 JIT |
| `validation/observer_off/` | 关观察器 |

# H1：共享 HBlank 时序与窗口 DMA 维护

2026-11-02。基于 Gericom 与原项目贡献者的 GBARunner3、Wokann 的 Slot-2 分支。H1 处理共享 ROM 缓存加载／HBlank 服务路径的两项时序问题，不依赖洞穴地图；暗洞光圈是便于观察异常的复现场景。

## 影响范围与已验证范围

问题所在的缓存加载与 HBlank 入口在整个游戏运行过程中共用。只要读卡临界区与逐行任务重叠，就可能在洞外或其他阶段触发；普通画面未必明显，不能将它限定为洞穴专属 bug，也不能反过来说每个场景、每一帧都会出错。

H1 不检查地图编号。帧首过滤作用于共享 HBlank DMA 入口；复制期间的维护仅适用于下述严格匹配的窗口 DMA0。其他窗口、滚动、仿射、调色板等逐行效果可能受同类延迟影响，但尚未逐项证明，也未全部得到 H1 的维护能力。当前量化画面验收仍是大小光圈的固定重放。

详见 [范围说明](SCOPE.md)。

## 已实测的社区 H1

底本：冻结 PATCH B3。H1 相对 B3 只改 `HBlankIrq.s` 和 `SdCache.c`，不包含 A2 或 SR2；保留 B3 已有声音修复。NDS 为 228,864 字节，SHA256：

`7e77a51d32f2e7d34ac865b462dec887eb8fb9c582cb2c116c3c28ae26de48f6`

本目录 `tested-combination/` 保留这两个源文件、相对 B3 的完整差异、构建时独立核对结果和后续用户反馈。源文件是阅读副本，不能单独编译；完整前置项目和本地测试模型未在本目录打包。

| 固定现场 | B3 | H1 |
|---|---|---|
| 大光圈静止／行走／停下 | 7/446 帧越界 | 0/446；每帧 160 次 DMA0 |
| 小光圈静止／行走／停下 | 7/446 帧越界 | 0/446；每帧 160 次 DMA0 |

每组检查 205 次卡带复制，27 次符合分段条件，维护 DMA 96 次；未见错误内容、提前发布、重入或未完成复制。逐指令检查 IRQ 始终关闭；本场景 Hicode 栈保护字前仍余 132 字节。这些是电脑模型数据，不是实机耗时或通用栈上界。

用户随后反馈：“H1验证了 没问题”。设备环境为既有 NDSL+iTouchDS。未提供时长及分项记录，不扩大为所有游戏或存档互通逐项通过。构建时 JSON 的 `hardware_tested:false` 保持原样；后续反馈单独存档。

## 修复方式

- 第 0 行绘制期过滤遗留 HBlank DMA，避免新帧源表多取一项。
- Slot-2 ROM 复制符合安全条件时，每 32 字节检查一次 HBlank 并维护既有 DMA0，避免长时间关中断造成请求合并、漏行。
- CPU IRQ 始终保持关闭，游戏回调不插入缓存加载，缓存仍在完整复制和处理后发布。只 ACK HBlank 并递延 GBA 中断投递。
- 仅支持唯一 HBlank 通道 DMA0、控制字 0xA260、count=1、WIN0H/WIN1H 目的、对齐且位于标准 GBA EWRAM/IWRAM 的当前源。其他配置、IRQ 模式、越界读取回原路径。

## 给 Wokann 的最小移植

已提交：[Wokann PR #9](https://github.com/Wokann/GBARunner3/pull/9)（Draft）；完整源码：[review/slot2patch-window-hdma-h1](https://github.com/chr5122/GBARunner3/tree/review/slot2patch-window-hdma-h1)。

目标：`cache-hicode/slot2patch` @ `f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9`，以前置对齐 PR #2 的提交 `f5efe7acd93dc7d8428fc9a8ceac3794188ce83e` 为父本。

`upstream-port/` 收录三文件差异、构建／独立核对结果、实际 helper C 宿主测试。完整可编译代码将通过上游 PR 的 fork 分支提供。此移植保留原 helper 与帧首过滤；额外将原 `dmaStartSound` 移至 EWRAM/noinline 腾出 ITCM，函数逻辑不变。没有捆绑声音回绕、B3、A2、SR2、R1、诊断或日志移除；保留上游日志行为，所以不等同于顺畅日常组合版。

初次移植 NDS：224,768 字节，SHA256：

`44ab8ffdecfb85080663c3d65453a5a5e9139dc094d7d007a83e9f7aa37bff77`

完整构建通过；69,673 条件、1,054 轮询、5 复制／回退用例通过；实际链接过滤指令通过 5,120 例。ARM7 与父本逐字节一致，头校验及完整 core 复制通过；ITCM 末尾 0x7FB0，VRAM BSS 末尾 0x0681FD50。无新增永久状态；既有部分 VRAM 数据地址因链接平移 16 字节，具体清单见 verification.json。

**新移植没有完整游戏重放或新实机验收，因此提交 Draft。** 不得将组合 H1 的硬件反馈套到新产物。宿主桩测试不模拟真实扫描线或烧录卡延迟。

`test_helpers.py` 可在完整移植源码 checkout 中直接运行：`python3 test_helpers.py`（放在 checkout 根目录，或传源码目录作为第一个参数）；需要 Python3 和 clang++。它只生成宿主测试程序和结果，不运行游戏、不访问卡带。

## 后续边界

- 独立 H1 的原始记录按历史保留。2026-11-02 用户要求与 SR2 合入社区 PATCH 主线，后续以 [H1＋SR2 整合记录](../h1_sr2_mainline/README.md) 为准；最终组合另含跨行一致采样加固，仍待实机复测，A2 未加入。
- save 模式不走 Slot-2 4KB ROM 复制，但与原 PATCH 共享帧首 HBlank 代码；同场景未验证，不能断言完全无问题，也不直接搬入卡带轮询路径。
- PRE/SD 的另外一轮读取、延迟及失败注入审计没有发现需要新增修改的证据；本修复不改 PRE 或保存路径。
- 多游戏、其他 DMA 模式、不同烧录卡和完整动态 JIT 仍待回归。

这里上传源码与文字证据，不包含游戏 ROM、BIOS、存档、PRE、汉化补丁或 NDS 二进制，未创建正式 Release。



## 后续一致采样加固

当前上游 PR #9 的 head 为 `adb4344d8d1535515fca7e2a044d279a8295a3de`，同样采用主线整合中发现的一致采样 guard，不含 SR2。完整独立构建通过，ARM7 不变，ITCM 末尾仍为 0x7FB0；guard 实际指令 10,240 例通过。新独立审阅 NDS SHA256 为 `a4eb80c810ff7dd0b031ba8b3026f48ce2f687cea54459c7750f98cedcf0786a`，仍未做该裸分支完整游戏或实机回归，保持 Draft。上文初次移植及原 H1 的历史指纹不改写；本次结果见 [guard-refinement](upstream-port/guard-refinement/)。

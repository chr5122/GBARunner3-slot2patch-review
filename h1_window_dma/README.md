# H1：窗口扫描线 DMA 时序修复

2026-11-02。基于 Gericom 与原项目贡献者的 GBARunner3、Wokann 的 Slot-2 分支。H1 修复绿宝石暗洞光圈暴露出的两项时序问题；不声称覆盖全部扫描线效果。

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

新移植 NDS：224,768 字节，SHA256：

`44ab8ffdecfb85080663c3d65453a5a5e9139dc094d7d007a83e9f7aa37bff77`

完整构建通过；69,673 条件、1,054 轮询、5 复制／回退用例通过；实际链接过滤指令通过 5,120 例。ARM7 与父本逐字节一致，头校验及完整 core 复制通过；ITCM 末尾 0x7FB0，VRAM BSS 末尾 0x0681FD50。无新增永久状态；既有部分 VRAM 数据地址因链接平移 16 字节，具体清单见 verification.json。

**新移植没有完整游戏重放或新实机验收，因此提交 Draft。** 不得将组合 H1 的硬件反馈套到新产物。宿主桩测试不模拟真实扫描线或烧录卡延迟。

`test_helpers.py` 可在完整移植源码 checkout 中直接运行：`python3 test_helpers.py`（放在 checkout 根目录，或传源码目录作为第一个参数）；需要 Python3 和 clang++。它只生成宿主测试程序和结果，不运行游戏、不访问卡带。

## 后续边界

- 用户已确认组合 H1 正常；尚未升级基线，没有与 A2/SR2 合并。
- save 模式不走 Slot-2 4KB ROM 复制，但与原 PATCH 共享帧首 HBlank 代码；同场景未验证，不能断言完全无问题，也不直接搬入卡带轮询路径。
- PRE/SD 的另外一轮读取、延迟及失败注入审计没有发现需要新增修改的证据；本修复不改 PRE 或保存路径。
- 多游戏、其他 DMA 模式、不同烧录卡和完整动态 JIT 仍待回归。

这里上传源码与文字证据，不包含游戏 ROM、BIOS、存档、PRE、汉化补丁或 NDS 二进制，未创建正式 Release。

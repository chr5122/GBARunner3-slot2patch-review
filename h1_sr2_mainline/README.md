# PATCH H1 + SR2 主线整合

用户于 2026-11-02 反馈“SR2验证成功 与h1一同并入主线”。H1 的先前反馈为“H1验证了 没问题”。据此整合社区 PATCH 代码线；这不代表 Wokann 或 Gericom 已合入，也不把两项分别通过写成新组合产物已实机通过。

## 来源与组成

- 冻结 PATCH B3：`f2d5f8bedf024a694b00ee3bcb1eaebdda2eb21644b20e06c063f5f499f5dbad`。
- 已实测 H1：`7e77a51d32f2e7d34ac865b462dec887eb8fb9c582cb2c116c3c28ae26de48f6`。
- iCloud SR2 实物与交接 SHA256 一致：`c4d6dc5b5efb4b967191a720dc76d1c78c070e148be13aea1416b88ccc17ff5b`。
- SR2 根因与短触发排查来自用户提供的 Grok 交接；本次从准确 H1 源码恢复其两条指令修改，独立比较实际链接解码器与上述 SR2 实物，唯一匹配。
- 保留 B3 继承的 D2、G1、R1、可选占位 ROM、2KiB 对齐与 BX 快捷路径；不包含 A2，也不包含失败的 SR1 拦截方案。

## 两项机制

H1 维护贯穿游戏运行的共享缓存加载／HBlank 时序；洞穴光圈只是量化观测现场。维护路径仍严格限制窗口 DMA0，其他效果未宣称全部修复。

SR2 修复 high-ROM SWI 从缓存整字中取错半字的问题。实例字节 `8D 46 01 DF 00 DF` 中，位于 `0x082959EE` 的 SWI1 曾误读为 0x8D 并进入存档 SWI 分发；现在先按 LR bit1 选择正确半字，再取低八位。LR 是指令后的返回地址，条件为 `tst lr,#2` / `moveq r13,r13,lsr #16`。

## 合并时发现并修正的边界

最初只叠加 SR2 的组合没有设为基线，也没有发布。它成功软重启，但大小光圈均在同一 446 帧回放中出现一帧少做一次 DMA，对应画面越界。现场没有卡带复制。

原 H1 先读 VCOUNT，再读 DISPSTAT；异常帧 HBlank 入口位于第 0 行末尾，两个采样跨到第 1 行，导致“旧行号 0 + 新状态 HDraw”误过滤。最终改为一条 32 位读取同时获取 DISPSTAT/VCOUNT，并只过滤快照本身确实为第 0 行 HDraw 的请求。新六指令 guard 在私有 ARM946 解释器中覆盖 10,240 例，包含跨行及初始 NZCV 组合，寄存器保持、无写内存／栈增长。

这个细化使最终组合不再是仅改 16 字节的初次实验。它只增加一条 ARM 指令，后续 534 个代码符号按链接重定位；全部 RAM/data 符号地址保持一致，ITCM 末尾仍为 0x7FF0。不能把第一次组合的哈希或布局结论套到最终产物。

## 构建和独立核验

最终文件：`GBARunner3_PATCH_H1_SR2.nds`，228864 字节。

SHA256：`1aa3ab06bd34c140c260bd833f3777714324ec1b50e24d8e0513628e16125199`。

相对准确 H1 源码只改 VMSwi.s 和 HBlankIrq.s。ARM7 逐字节相同；NDS 0x000–0x1FF 头部、CRC、既有 228 字节诊断尾部、bootstrap 消费长度、hicode 2KiB 对齐均核对。两段非执行打包元数据随重打包变化，共 40 字节，完整文件哈希因此也受工具链影响。编译使用的 libtwl 76 个跟踪 blob 与原 submodule 一致。

SR2 实际链接的 TST/MOVEQ/AND 指令通过 8,192 个 ARM946 执行用例，覆盖两个半字、全 256 个立即数及全部初始 NZCV 组合；CP15 缓存取数另以游戏重放观察，不把这项指令测试夸大为完整缓存测试。

组合游戏回放和核验结果保存在 `validation/`，由最终汇总脚本写入 `integration_results.json`。所有测试使用内存虚拟 SD/卡带及私有存档副本，不写实际卡带、固件或原输入文件；没有周期 SD 诊断写入。

## 证据边界与交付

用户已分别反馈 H1、SR2 实机通过，未提供各项时长及完整操作清单；最终组合及新增一致采样 guard 尚未实机复测。完整通关名单长跑没有在本次重新执行，软重启测试不冒充完整名单验收。save 线及 SR2S 实机范围本次不自行扩大。

历史 B3/H1/SR2 产物、构建记录和上游独立 PR 保留。新主线源码不代表已经创建 NDS Release。基础来自 Gericom 与原贡献者；Slot-2 分支来自 Wokann，SR2 调查来源保留上述署名。

## 最终组合回放结果

| 回放 | 结果 |
|---|---|
| 大光圈静止／走动／停下 | 446/446 画面与原 H1 字节一致；DMA0 每帧 160；越界 0 |
| 小光圈静止／走动／停下 | 446/446 画面与原 H1 字节一致；DMA0 每帧 160；越界 0 |
| 每组复制审计 | 205 次复制、27 次分段、86 次维护；错误／重入／未完成均 0 |
| H1 软重启阴性对照 | 误读 0x8D 一次，未到 BIOS SoftReset，最终 PC=4 |
| 最终组合软重启 | SWI1 两次、SWI0 一次、误读 0x8D 为 0；进入 BIOS 后两次观察到 ROM 入口，最终 PC 正常 |

所有回放输入哈希未变，虚拟 SD 写入、保存持久化请求、Flash 变化均为 0。这里没有新增真实卡带保存验收。

## 主线源码

[完整固定源码](https://github.com/chr5122/GBARunner3/tree/65866604e5fd4e90c51eb32e6ea34bb251d075c4)（分支 community/slot2patch）；上游 PR #9 是独立移植，不与整合版混用。

```sh
git clone --recursive --branch community/slot2patch https://github.com/chr5122/GBARunner3.git
cd GBARunner3
git checkout 65866604e5fd4e90c51eb32e6ea34bb251d075c4
git submodule update --init --recursive
make -C code
```

需按原项目准备 devkitARM/libnds；串行构建，更新 core 后确保 bootstrap main.o 重编以消费新长度。源代码可获取不表示已发布 NDS 二进制下载。

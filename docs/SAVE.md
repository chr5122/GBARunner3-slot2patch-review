# save 项目：slot2save

[返回首页](../README.md) · [patch 项目](PATCH.md) · [验证状态](STATUS.md) · [版本哈希](VERSIONS.md)

## 运行方式与父本

在这里的 save 测试方式中，游戏程序和中文内容来自 SD 上完整 ROM，存档使用 Slot-2 对应正版卡。它不是 slot2patch 的外挂补丁读取方式。

固定上游为 Wokann 的 `cache-hicode/slot2save`，提交 `1f9b601395c96b0b62a7e0cffd9b7711ce6283bc`。基础 GBARunner3 来自 Gericom 和原项目贡献者。

## G1S：音频 DMA 回绕移植

把 patch 线上 G1 的 m4a PCM DMA 回绕移植到 slot2save，源码差异仅 `DmaTransfer.c`。控制条件和声音修复详见原材料。

用户实机记录：NDSL、save 模式，切场景“咔”声消失。没有把这条反馈扩充为所有音频、保存往返或所有游戏都已测试。

- [PR #2](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/2)
- [中文 README](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/d76e6b0fb3590af0f45541909fa961dba8e5524b/g1s_dma_wrap/README.md)
- [源码差异：slot2save → G1S](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/d76e6b0fb3590af0f45541909fa961dba8e5524b/g1s_dma_wrap/g1s_vs_slot2save.diff)
- [冻结构建记录](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/d76e6b0fb3590af0f45541909fa961dba8e5524b/g1s_dma_wrap/BUILD_INFO.json)

## G1S+B3：短跳转优化移植

在 G1S 上移植与 patch B3 相同的 Thumb BX 快捷处理。它是独立的 save 构建，不能把 patch B3 的 NDS 或实测结论直接套过来。

已有电脑模型记录：

| 固定绿宝石 BPEJ v1.13 首次翻卡 | 八地址配置 | 关闭 JIT |
|---|---:|---:|
| G1S 控制包 | 63 帧 | 41 帧 |
| G1S+B3 | 41 帧 | 41 帧 |

模型中 SD 写入和存档变更为零；因此这里没有保存功能验收。第二/三次翻卡、完整动态 JIT、RTC、声音和其他游戏的范围，以各自产物记录为准。最新用户实机状态见 [统一状态页](STATUS.md)。

- [PR #3](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/3)
- [G1S+B3 中文 README](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/54dfec0f5b0c650e72c0383f486a97a1389f8827/g1s_b3_thumb_bx/README.md)
- [模型结果](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/54dfec0f5b0c650e72c0383f486a97a1389f8827/g1s_b3_thumb_bx/RESULT.md)
- [G1S → G1S+B3 源码差异](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/54dfec0f5b0c650e72c0383f486a97a1389f8827/g1s_b3_thumb_bx/G1S_B3_vs_G1S.patch)

## 审阅材料与运行包

PR #2、#3 当前均未合入 main；以上固定提交链接可直接阅读材料。这里没有提供 NDS 下载，构建产物通过 [版本表](VERSIONS.md) 的完整 SHA256 区分。

G1S 的实机成功不自动证明 G1S+B3 已实机成功；同样，patch B3 的翻卡数值不能写成 save 的实测值。

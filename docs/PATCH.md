# patch 项目：slot2patch

[返回首页](../README.md) · [save 项目](SAVE.md) · [验证状态](STATUS.md) · [版本哈希](VERSIONS.md)

## 运行方式

在本项目的测试方式中，原版程序和未修改数据来自 Slot-2 正版卡；汉化改动来自 SD 的外挂补丁，修改后的块由 PRE 缓存提供。存档仍使用对应卡带。

固定上游：Wokann 的 `cache-hicode/slot2patch`，提交 `f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9`。本页是材料导航，不替代具体版本的安装和配置说明。

<a id="d2-pre"></a>

## D2：运行期只读与自动 PRE

用户在 DS Lite + iTouchDS + TWiLight Menu++ 上反馈：运行期关闭日志与周期写盘后明显流畅；D2 进一步保留启动时自动生成 PRE。

已记录用户确认：首次生成、随后运行、再次启动和卡带存档互通。原白屏根因未被充分隔离，不能据此宣称对全部烧录卡都应无条件删除作者原有规避路径。

材料：
- [实现与检查](../IMPLEMENTATION.md)
- [实机历史记录](../FIELD_TESTS.md)
- [构建说明](../BUILD_REVIEW.md)
- [D1 → D2](../10_D2_vs_D1_review.patch)
- [固定上游 → D2 完整差异](../20_FULL_vs_f8ac25c_review.patch)

前两种补丁视图的父本不同。10_ 和 20_ 不是顺次叠加的两步。

## G1：切场景爆音

对识别为 m4a 双路声音 FIFO、缓冲间距 0x630 的情况，在缓冲末尾回绕 DMA 读取位置。用户反馈切场景爆音消失，长时间运行和存档写回正版卡正常；这不代表所有声音类型已经量化验证。

- [音频排查与实现](../G1_AUDIO_POP_FIX.md)
- [D2 → G1 差异](../30_G1_vs_D2_review.patch)
- [布局变化](../MAP_DIFF_SUMMARY.md)
- [PR #1（本材料仓库已合并）](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/1)

<a id="r1-read-guard"></a>

## R1：读取失败保护

R1 继承已记录的 D2/G1 功能和中间启动改动，新增读取结果向上传递、失败缓存禁止发布、嵌套临时缓冲保护。2026-10-29 用户反馈实机成功并指定它为本地后续开发基线。

R1 NDS：`46eda7a79321bb24213b8d39f4e77079e84bb0cc3436cc5964749aaeb134d808`，228352 字节。

**材料边界：** R1 的完整前置修改及完整可重建源码树尚未在本仓库收录。B3 的 `SOURCE.patch` 相对 R1，不是直接相对 Wokann 原分支。本仓库的 D2/G1 差异不能被当成已补齐 R1 的全部构建步骤。

## B3：hicode 短跳转优化

只处理实际缓存中字节为 Thumb `BX r0-r3` 的情况，目标限：
- EWRAM：0x02000000–0x0203FFFF
- IWRAM：0x03000000–0x03007FFF
- 低 2MB ROM：0x08000000–0x081FFFFF

其他编码、目标地址、缓存缺失等回到原处理。B3 未修改声音、SD、存档或 MSR/IRQ 处理器。

| 固定绿宝石八地址场景 | 首次 | 第二次 | 第三次 |
|---|---:|---:|---:|
| R1 | 60 | 81 | 127 |
| B3 | 38 | 37 | 37 |

单位为模型帧数。首次映射重建由 24219 次降至 1376 次。指令测试、画面对照和独立复核已记录；最新用户实机反馈单列在 [状态页](STATUS.md)。

审阅材料（PR #3，尚未合入 main）：
- [PR 主页面](https://github.com/chr5122/GBARunner3-slot2patch-review/pull/3)
- [B3 中文 README](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/54dfec0f5b0c650e72c0383f486a97a1389f8827/b3_thumb_bx_strict_ram/README.md)
- [完整报告](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/54dfec0f5b0c650e72c0383f486a97a1389f8827/b3_thumb_bx_strict_ram/REPORT.md)
- [R1 → B3 源码差异](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/54dfec0f5b0c650e72c0383f486a97a1389f8827/b3_thumb_bx_strict_ram/SOURCE.patch)
- [B2 → B3 范围收紧差异](https://github.com/chr5122/GBARunner3-slot2patch-review/blob/54dfec0f5b0c650e72c0383f486a97a1389f8827/b3_thumb_bx_strict_ram/B2_TO_B3.patch)

固定提交链接保留当时的证据；PR 页面显示后续更新。构建时写出的“未实机”是历史状态，后续反馈见统一状态页，不回写冻结的构建 JSON。

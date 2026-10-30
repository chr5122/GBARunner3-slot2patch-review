# 版本、父本与产物指纹

[返回首页](../README.md) · [patch](PATCH.md) · [save](SAVE.md) · [状态](STATUS.md)

这里的版本名用于区分社区实验产物，不代表 Wokann/Gericom 的官方版本号。以下 NDS 均未放入本仓库。

| 模式 | 产物 | 父本/关系 | 字节数 | SHA256 |
|---|---|---|---:|---|
| patch | D2_AUTO_PRE.nds | slot2patch 固定上游及 D1 实验之后 | 227328 | `7965f4b1a2381a7ad325b1c618cc3b3511fc1287489291243cc8e296ddf6f76b` |
| patch | G1_DMA_WRAP.nds | D2 + m4a DMA 回绕 | 227840 | `eefe98a0d2369d18a78e02450e56a50a45c79e20b8f4887e2d1adc1e4063502d` |
| patch | GBARunner3_R1_SD_READ_GUARD.nds | 继承 D2/G1 及中间启动改动；新增读取失败保护 | 228352 | `46eda7a79321bb24213b8d39f4e77079e84bb0cc3436cc5964749aaeb134d808` |
| patch | B3_THUMB_BX_STRICT_RAM_TEST.nds | R1 + B3 | 228352 | `f2d5f8bedf024a694b00ee3bcb1eaebdda2eb21644b20e06c063f5f499f5dbad` |
| save | G1S_DMA_WRAP.nds | slot2save 固定上游 + 音频回绕 | 211968 | `6c0420fda11c0668a558e89f2c56cecbddf5df26e8e066fcc91c50cdd9fbd154` |
| save | G1S_B3_TEST.nds | G1S + B3 移植 | 211968 | `74077023e82769f5a56fe8b091725d23042736d771b75df013d62aa196e30048` |

## 固定上游与 patch 基准

- patch 上游：`cache-hicode/slot2patch` @ `f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9`。
- save 上游：`cache-hicode/slot2save` @ `1f9b601395c96b0b62a7e0cffd9b7711ce6283bc`。
- `10_D2_vs_D1_review.patch`：D1 → D2。
- `20_FULL_vs_f8ac25c_review.patch`：固定 patch 上游 → D2；与 10_ 是不同父本的替代视图。
- `30_G1_vs_D2_review.patch`：D2 → G1。
- PR #2 的 `g1s_vs_slot2save.diff`：固定 save 上游 → G1S。
- PR #3 的 `b3_thumb_bx_strict_ram/SOURCE.patch`：R1 → patch B3。
- PR #3 的 `g1s_b3_thumb_bx/G1S_B3_vs_G1S.patch`：G1S → save G1S+B3。

R1 的完整前置材料尚未在本仓库收录；不能把“D2、G1、R1、B3 的功能演进关系”直接当成一套已验证可连续应用的公共构建脚本。

B1/B2 是 B3 之前的研究候选，不作为当前对照候选列出。B2 → B3 差异保留用于审查目标范围收紧。

## 证据与哈希

NDS 哈希标识具体二进制，不表示本仓库已经提供该二进制或完成跨设备认证。构建 JSON 的 `hardware_tested:false` 是写出时的状态，后续用户反馈记录在 [STATUS.md](STATUS.md)，不重写冻结证据。

原根目录 `SHA256.json` 保留 D2/G1 历史指纹；整理后的导航文档使用 [DOCS_SHA256.json](../DOCS_SHA256.json)。主分支和不同 PR 的文件清单各有适用范围。

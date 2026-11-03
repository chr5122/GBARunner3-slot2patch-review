# 版本、父本与产物指纹

**2026-11-04 更新：[A17 PATCH 音频测试版](../audio_a17/README.md)已提供 NDS、运行包和对应源码快照。它有用户实机试听反馈，尚未完成多游戏验收；未替换社区代码主线，SAVE 未改，也未创建正式 Release。下文保留较早候选的历史准备状态。**

**2026-11-02 社区 PATCH 主线已整合 H1＋SR2**（含跨行状态一致采样加固）。[整合记录](../h1_sr2_mainline/README.md) · [完整源码](https://github.com/chr5122/GBARunner3/tree/65866604e5fd4e90c51eb32e6ea34bb251d075c4)。H1/SR2 分别有用户实机成功反馈；最终组合通过电脑回归，仍待实机复测。A2 未加入，save 线本轮未改。

[返回首页](../README.md) · [patch](PATCH.md) · [save](SAVE.md) · [状态](STATUS.md)

这里的版本名用于区分社区实验产物，不代表 Wokann/Gericom 的官方版本号。下方历史 NDS 不因本次上传自动提供下载；新增的 A17 单独见下载入口。

| 模式 | 产物 | 父本/关系 | 字节数 | SHA256 |
|---|---|---|---:|---|
| patch | D2_AUTO_PRE.nds | slot2patch 固定上游及 D1 实验之后 | 227328 | `7965f4b1a2381a7ad325b1c618cc3b3511fc1287489291243cc8e296ddf6f76b` |
| patch | G1_DMA_WRAP.nds | D2 + m4a DMA 回绕 | 227840 | `eefe98a0d2369d18a78e02450e56a50a45c79e20b8f4887e2d1adc1e4063502d` |
| patch | GBARunner3_slot2patch_v1_romopt_trial.nds | G1 + 占位 ROM 可选（只改 `loadGbaCart`）；R1 记录中的前一二进制 `R0_UPLOADED_ROMOPT.nds` 与之同哈希 | 227840 | `592e01ae2feaa708b660cee1cb499890224861794093c62387af3d5a37766699` |
| patch | GBARunner3_R1_SD_READ_GUARD.nds | romopt 试验版 + 读取失败保护（继承 D2/G1 与占位 ROM 可选） | 228352 | `46eda7a79321bb24213b8d39f4e77079e84bb0cc3436cc5964749aaeb134d808` |
| patch | B3_THUMB_BX_STRICT_RAM_TEST.nds | R1 + B3 | 228352 | `f2d5f8bedf024a694b00ee3bcb1eaebdda2eb21644b20e06c063f5f499f5dbad` |
| save | G1S_DMA_WRAP.nds | slot2save 固定上游 + 音频回绕 | 211968 | `6c0420fda11c0668a558e89f2c56cecbddf5df26e8e066fcc91c50cdd9fbd154` |
| save | G1S_B3_TEST.nds | G1S + B3 移植 | 211968 | `74077023e82769f5a56fe8b091725d23042736d771b75df013d62aa196e30048` |

## 固定上游与 patch 基准

- patch 上游：`cache-hicode/slot2patch` @ `f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9`。
- save 上游：`cache-hicode/slot2save` @ `1f9b601395c96b0b62a7e0cffd9b7711ce6283bc`。
- `10_D2_vs_D1_review.patch`：D1 → D2。
- `20_FULL_vs_f8ac25c_review.patch`：固定 patch 上游 → D2；与 10_ 是不同父本的替代视图。
- `30_G1_vs_D2_review.patch`：D2 → G1。
- `rom_gba_optional/trial_vs_v1.diff`：G1 → 占位 ROM 可选试验版。
- PR #2 的 `g1s_vs_slot2save.diff`：固定 save 上游 → G1S。
- PR #3 的 `b3_thumb_bx_strict_ram/SOURCE.patch`：R1 → patch B3。
- PR #3 的 `g1s_b3_thumb_bx/G1S_B3_vs_G1S.patch`：G1S → save G1S+B3。

R1 的完整前置材料尚未在本仓库收录；不能把“D2、G1、R1、B3 的功能演进关系”直接当成一套已验证可连续应用的公共构建脚本。

B1/B2 是 B3 之前的研究候选，不作为当前对照候选列出。B2 → B3 差异保留用于审查目标范围收紧。

## 证据与哈希

NDS 哈希标识具体二进制，不表示本仓库已经提供该二进制或完成跨设备认证。构建 JSON 的 `hardware_tested:false` 是写出时的状态，后续用户反馈记录在 [STATUS.md](STATUS.md)，不重写冻结证据。

原根目录 `SHA256.json` 保留 D2/G1 历史指纹；整理后的导航文档使用 [DOCS_SHA256.json](../DOCS_SHA256.json)。主分支和不同 PR 的文件清单各有适用范围。


## H1／SR2 主线新增指纹

| 产物 | 关系 | 字节数 | SHA256 |
|---|---|---:|---|
| 已测 H1 | B3＋H1 | 228864 | `7e77a51d32f2e7d34ac865b462dec887eb8fb9c582cb2c116c3c28ae26de48f6` |
| 已测 SR2 | B3＋SR2；由 iCloud 实物核对 | 227840 | `c4d6dc5b5efb4b967191a720dc76d1c78c070e148be13aea1416b88ccc17ff5b` |
| 当前 H1＋SR2 | H1＋SR2＋跨行一致采样加固 | 228864 | `1aa3ab06bd34c140c260bd833f3777714324ec1b50e24d8e0513628e16125199` |

仅代码主线已整合；最终组合尚未实机测试。历史构建 JSON 保持原样，当前状态见整合记录。


## A17 音频测试下载

| 产物 | 关系 | 字节数 | SHA256 |
|---|---|---:|---|
| [GBARunner3_PATCH_A17.nds](../audio_a17/GBARunner3_PATCH_A17.nds?raw=true) | H1/SR2/A2 测试线＋A16 波形步进＋自适应 PCM v4 | 233472 | `6f00e104b1b52a56aa69b2af3d57d0283a692fdd9ef9002e41d3c3fe8249fffe` |

同此前 iCloud A17，原文件未重新编译。用户试听反馈与电脑证据的边界见 [A17 说明](../audio_a17/README.md)。未包含后续 M1/M2/M3 量化候选。

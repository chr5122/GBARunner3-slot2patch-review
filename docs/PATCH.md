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

<a id="rom-optional"></a>

## 占位 ROM 可选（romopt）：无 `rom.gba` 也能启动

日期：2026-10-28。父本是 G1（文件名 `GBARunner3_slot2patch_v1.nds`，SHA256 与 G1_DMA_WRAP 相同：`eefe98a0…502d`），即固定上游 + D2 + G1 DMA 回绕，bootstrap 拷贝长度写死 130660。

问题：从烧录卡菜单直接启动、没有传入 ROM 路径时，G1 去打开 SD 根目录 `/rom.gba`；patch 模式下这只是占位文件，ROM 字节来自 Slot-2 卡带。打不开就以停机码 12（`X1_NO_LAUNCH_FILE`）停在 GBR3 logo。

改动只在 `core/arm9/source/main.cpp` 的 `loadGbaCart()`：
- 打得开 `rom.gba`：与 G1 相同，仍做 sd2M / sd4M 两次诊断读取。
- 打不开：把 `gFile.obj.fs` 指到已挂载的 `gFatFs`，跳过这两次诊断读取，继续从卡带启动。
- 没有新增 SD 写入；存档格式、存档逻辑、bootstrap 拷贝长度、ITCM/高 ROM 代码均未改。
- 卡带 game code 不匹配时，原有 `handleSave` 仍在打开任何 SD 存档前以停机码 15 停下。这一点是对照源码得出，模拟器无法放入不匹配卡带。

试验 NDS：`GBARunner3_slot2patch_v1_romopt_trial.nds`，227840 字节，SHA256 `592e01ae2feaa708b660cee1cb499890224861794093c62387af3d5a37766699`。未放入本仓库。

**电脑核验（仅 melonDS）：** 无 `rom.gba` 时 G1 停在 logo；试验版进到训练家卡片，画面与 G1 有占位文件的基线逐像素相同；放回 `rom.gba` 时与 G1 相同；SD 写入为 0，卡带存档无变化。

**已知旧问题未动：** 试验核心 130888 B，bootstrap 只拷 130660 B，未拷 228 B（G1 时已有 172 B）。R1 记录把它列为保留的“228 字节诊断遗漏”。

**与后续版本的关系：** R1 基线记录中的前一个二进制 `R0_UPLOADED_ROMOPT.nds` 与本试验 NDS 哈希相同，R1 在它之上加读取失败保护，并列明保留“optional placeholder ROM”。B3 相对 R1，B3 发布包也写明“保留无占位 ROM 启动”（见[发布准备](RELEASE_PREPARATION.md)）。

**实机：** 这一版单独的用户实机反馈未记录。文件名 `R0_UPLOADED_ROMOPT` 表示它曾由用户回传作为 R1 的输入，但不能据此当作实机验收。之后 R1、B3 的用户实机反馈覆盖的是含此行为的后续版本，见[状态页](STATUS.md)。

材料（从未合并分支 `cursor/rom-gba-optional-96bc` 提交 `966066a` 合入）：
- [试验说明](../rom_gba_optional/README.md)
- [G1(v1) → 试验源码差异](../rom_gba_optional/trial_vs_v1.diff)
- [构建信息](../rom_gba_optional/BUILD_INFO.txt)
- [模拟器截图](../rom_gba_optional/screenshots/) 与 [SHA256SUMS](../rom_gba_optional/SHA256SUMS)

slot2patch 方案的作者是卧看微尘（Wokann）。本试验没有向 Wokann/GBARunner3 开合并请求。

<a id="r1-read-guard"></a>

## R1：读取失败保护

R1 继承已记录的 D2/G1 功能和中间启动改动（即上面的占位 ROM 可选），新增读取结果向上传递、失败缓存禁止发布、嵌套临时缓冲保护。2026-10-29 用户反馈实机成功并指定它为本地后续开发基线。

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

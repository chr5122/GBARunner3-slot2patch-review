# GBARunner3 卡带汉化与兼容性改进

基于 GBARunner3 的社区实验，为 NDS / NDS Lite 上的 GBA 卡带汉化、兼容性和声音表现提供改进与测试资料。

## 选择运行方式

| 模式 | 游戏从哪里运行 | 正版卡带的作用 | 详细说明 |
|---|---|---|---|
| **PATCH：外挂补丁** | 正版卡带游戏 + SD 卡上的汉化补丁 | 读取游戏数据并使用卡带存档 | [PATCH 模式](docs/PATCH.md) |
| **SAVE：完整 ROM** | SD 卡上的完整游戏 ROM | 使用对应卡带存档 | [SAVE 模式](docs/SAVE.md) |

两种模式需要使用各自对应的 GBARunner3 版本。本仓库不提供游戏 ROM、BIOS 或存档。

## 下载与工具

- **PATCH A20 音频测试版：** [下载 NDS](audio_a18_a20/GBARunner3_A20_wave_resume.nds?raw=true) · [版本说明和 A18、A19 对照](audio_a18_a20/README.md)。用户反馈 NDSL 实机听感非常接近原生卡带；多游戏验收尚未完成。
- **PATCH A17 对照版：** [下载 NDS](audio_a17/GBARunner3_PATCH_A17.nds?raw=true) · [下载 ZIP 与查看说明](audio_a17/README.md)。
- **SAVE 模式：** [功能和版本资料](docs/SAVE.md)。这里的资料页尚未提供 SAVE NDS 下载。
- **电脑补丁工具：** [工具说明和下载](docs/TOOLS.md)。仓库中的 Windows 旧包可能出现日志输出错误；[修复源码分支](https://github.com/chr5122/GBARunner3-slot2patch-review/tree/fix/windows-tool-stdio-20261108)已通过 Windows 自动冒烟测试，实际用户环境仍需验证。

## 改进概览

- **声音：** G1 修复声音 DMA 回绕相关爆音；A17–A20 是后续 PATCH 音频测试版本。
- **画面：** H1 改善游戏运行期间共享的 HBlank／窗口 DMA 时序，绿宝石洞穴光圈是便于观察的场景之一。
- **重启：** SR2 修复 high-ROM SWI 解码中的半字选择问题，针对已复现的软重启异常。
- **性能与稳定性：** 包括缓存跳转优化、SD 读取失败保护、自动生成 PRE 等工作。

H1、SR2 分别有用户实机成功反馈；[H1＋SR2 代码整合记录](h1_sr2_mainline/README.md)中的最终组合已通过电脑回放，不能将单项反馈直接当成该组合的完整实机验收。A20 的听感反馈属于实际试听，不代表所有游戏或设备已经验证。

## 开发与验证

- [PATCH 完整源码（固定版本）](https://github.com/chr5122/GBARunner3/tree/65866604e5fd4e90c51eb32e6ea34bb251d075c4) · [版本和校验值](docs/VERSIONS.md) · [版本沿革](docs/VERSION_HISTORY.md)
- [测试与验证状态](docs/STATUS.md) · [审阅材料](docs/REVIEW.md) · [文件整理说明](docs/FILE_ORGANIZATION.md)
- 向 Wokann 提交的 [H1 PR #9](https://github.com/Wokann/GBARunner3/pull/9) 和 [SR2 PR #10](https://github.com/Wokann/GBARunner3/pull/10) 均处于待审状态；[其他 PR 索引](docs/UPSTREAM_PRS.md)。社区整合不代表上游已合并。

GBARunner3 基础项目来自 [Gericom 及原项目贡献者](https://github.com/Gericom/GBARunner3)，Slot-2 分支来自 [Wokann（卧看微尘）](https://github.com/Wokann/GBARunner3)。感谢所有作者和测试者；相关来源见 [NOTICE](NOTICE.md)。

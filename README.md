# GBARunner3 slot2patch review — D2

供 **Wokann（卧看微尘）** 审阅的非官方缓存实验、源码差异和实测记录。这里不是完整的 GBARunner3 仓库，也不是正式发行版或已精简的合并请求。

感谢 Wokann 的 Slot-2/外挂补丁实现，以及 Gericom 和其他 GBARunner3 贡献者的基础工作。

## 本次想交流的结果

在一套 **DS Lite + iTouchDS + TWiLight Menu++** 上，用户确认关闭运行期日志和周期写盘心跳后，体感明显更流畅。

最终 D2 保留了启动阶段自动生成 `.pre`：

- 有有效缓存：直接只读使用。
- 无有效缓存：排他创建 `.tmp`，写入、同步并关闭，逐块读回校验，必要时保留旧缓存为 `.bak`，再启用新缓存。
- 进入游戏前关闭并封闭 SD 写入许可；游戏期间不写日志、不做写盘保活。
- 正版卡存档路径未改，卡带仍可写。

用户已确认 **首次生成缓存、生成后继续游戏、关机再次启动，以及正版卡原生 GBA 存档互通** 成功。这些属于用户实机反馈，不是独立硬件复现或全平台兼容认证。

**没有查明原白屏根因，也不建议由此直接删去其他设备可能需要的作者原有规避路径。** 希望先讨论是否值得引入显式可选的 boot-bake / read-only-runtime 模式。

## 先看哪些材料

| 材料 | 内容 |
|---|---|
| [FIELD_TESTS.md](FIELD_TESTS.md) | X1/D1/D2 实机反馈、诊断计数及尚未验证事项 |
| [MERGE_NOTES.md](MERGE_NOTES.md) | 作者审核边界、诊断遗留和后续最小 PR 建议 |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | 构建时实现、布局、栈、失败保护和检查说明 |
| [10_D2_vs_D1_review.patch](10_D2_vs_D1_review.patch) | D1 → D2 的 7 文件小差异；**不能直接套到卧看原分支** |
| [20_FULL_vs_f8ac25c_review.patch](20_FULL_vs_f8ac25c_review.patch) | 固定上游提交 → 实测 D2 的 15 文件完整源码差异，含诊断/布局遗留 |
| [PATCH_VERIFICATION.json](PATCH_VERIFICATION.json) | 两份 patch 的基准、逐文件哈希、实际 apply 后比对结果 |
| [BUILD_REVIEW.md](BUILD_REVIEW.md) | 源码差异复核与构建注意事项 |

**两份 patch 是不同基准的替代视图，不要一起套用。** 两份均已在独立临时目录实际 apply 后逐字节核对。

`source/` 仅包含相对上游新增/变更的源文件，便于网页阅读；不能单独编译它。点击 GitHub 的 **Code → Download ZIP** 可以一次下载全部审核材料。

## 固定版本

- 上游：[Wokann/GBARunner3](https://github.com/Wokann/GBARunner3)，`cache-hicode/slot2patch`。
- 提交：`f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9`。
- libtwl：`e069645bed14a93e149e873e9273f04851e3a04e`。
- 实测 D2 NDS：227328 B；SHA-256 `7965f4b1a2381a7ad325b1c618cc3b3511fc1287489291243cc8e296ddf6f76b`。
- 日期：2026-10-22（Asia/Shanghai）。

没有发布 NDS 二进制、游戏 ROM、BIOS、游戏汉化补丁/PRE、存档、SDK、原始照片、访问令牌或私人联系方式。
构建时文档的“未实机验证”属于历史状态；后续反馈单独记录于 FIELD_TESTS.md，没有篡改冻结的构建报告。

## 限制与安全

测试仅支持已记录设备和场景，未验证全部烧录卡、SD、游戏或卡带修订版；未提供 FPS/耗时或音频丢样量化。
保留作者原 PRE 格式。已有缓存仍使用原元数据校验，新生成缓存才逐块完整读回。
启动生成会真正写入 SD；两次 FAT rename **不是抗断电原子事务**，必须先备份，不能热插拔或在写入中关机。
阶段门禁不是按路径鉴权的文件系统沙箱；SD 运行期只读也不等于正版卡存档写保护。

源文件原有版权与许可证声明保留，见 [NOTICE.md](NOTICE.md)。本仓库未向 Wokann/Gericom 创建 PR，也不声称已获作者采纳。

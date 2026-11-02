# Wokann 上游 PR 审阅入口

2026-11-02：以下代码 PR 已直接提交到 **Wokann/GBARunner3**，均为 Draft（草稿）。本仓库原有 PR 是材料整合记录，两者编号属于不同仓库。

| 上游 PR | 内容 | 目标分支 | 前置 |
|---|---|---|---|
| [Wokann #2](https://github.com/Wokann/GBARunner3/pull/2) | patch：hicode 占位区 2KB 对齐 | `cache-hicode/slot2patch` | 无 |
| [Wokann #3](https://github.com/Wokann/GBARunner3/pull/3) | patch：m4a PCM 声音 DMA 回绕 | `cache-hicode/slot2patch` | #2，已包含在提交历史中 |
| [Wokann #4](https://github.com/Wokann/GBARunner3/pull/4) | save：m4a PCM 声音 DMA 回绕 | `cache-hicode/slot2save` | 无 |
| [Wokann #5](https://github.com/Wokann/GBARunner3/pull/5) | patch：B3 缓存 Thumb BX 快捷处理 | `cache-hicode/slot2patch` | #2，已包含在提交历史中 |
| [Wokann #6](https://github.com/Wokann/GBARunner3/pull/6) | save：B3 缓存 Thumb BX 快捷处理 | `cache-hicode/slot2save` | 无 |
| [Wokann #7](https://github.com/Wokann/GBARunner3/pull/7) | patch：移除运行期日志刷盘／允许无占位 ROM 启动 | `cache-hicode/slot2patch` | #2，已包含在提交历史中 |
| [Wokann #8](https://github.com/Wokann/GBARunner3/pull/8) | patch：SD 读取失败结果传播和缓存发布保护 | `cache-hicode/slot2patch` | #2，已包含在提交历史中 |
| [Wokann #9](https://github.com/Wokann/GBARunner3/pull/9) | patch：H1 共享 HBlank 时序／卡带复制期间窗口 DMA0 维护 | `cache-hicode/slot2patch` | #2；不捆绑其他功能 |

建议 patch 侧先看 #2，再独立看 #3、#5、#7、#8、#9；save 侧 #4、#6 可分别审阅。后续合并需重新核对组合后的构建、链接布局与实机行为。

## 代码与验证边界

这是从卧看准确父本重新拆出的独立审阅构建：patch 父本 `f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9`；save 父本 `1f9b601395c96b0b62a7e0cffd9b7711ce6283bc`。完整源码分支在 [chr5122/GBARunner3](https://github.com/chr5122/GBARunner3)，这里仍保留历史材料和证据。

七项 ARM9/ARM7/bootstrap 完整构建均通过；已核对远端完整源码树仅包含各自预期文件改动，并与本地构建源码的 Git blob 一致。两项 B3 分别通过实际编译指令测试：1,388 组等价、770 组回退。新的拆分构建没有重新做实机回归，不能把既有组合版的用户反馈直接当作这七份新构建的验收。Draft 需要后续验证并标为 Ready for review 后才能通过常规流程合并。

- 声音 PR 保留 G1/G1S 的 m4a 布局识别启发式，不宣称覆盖所有游戏或所有声音 DMA 配置。
- B3 为单独构建腾出 ITCM，还将原有 dmaStartSound 原样移到 EWRAM；未叠加声音回绕逻辑。
- #7 是日志和启动入口的最小拆分，保留上游 PRE 烘焙流程；不等同于整套 D2，也不保证所有设备运行期全局 SD 只读。去掉保活在不同烧录卡上的兼容性仍需验证。
- #8 处理驱动明确返回失败；不解决驱动永不返回，也不检测“成功但数据错误”。该独立拆分尚未重新做故障注入，ARM7/ARM9 必须配套编译。
- 本次没有上传 ROM、BIOS、存档或 NDS，也没有替换用户已验证的运行版本／基线。

## 提交与本地构建指纹

以下 SHA256 对应新拆分构建，仅用于标识，不是现有正式基线，也未提供二进制下载。

| PR | 源码 head | NDS SHA256 |
|---|---|---|
| #2 | `f5efe7acd93dc7d8428fc9a8ceac3794188ce83e` | `0c4fabac3301a806d408c532f42fae055e739bca0ef96f7226dfec5a4f1da7eb` |
| #3 | `2ee63327c926e6449296e151347c401b4210cadb` | `1e0bd77b3565561d82ea8991e4851bc0b50b8a112816023d7855ff50da5db2d1` |
| #4 | `54b4aebbb6da996e70538645c7c8bab02e016358` | `3000292a5e6065f474de55f208629e18e7f106d5b4b41821d576409b5fcf620f` |
| #5 | `b20db4c57044952a92f91e2993508d047a1e8a14` | `cfb7978f285d4509e9a85c773d3800778190b867ce0b93c45c364ae6e6cd0bbf` |
| #6 | `a42ce98ecaa79722fb93da04c06dec9479fd8d55` | `da3b706da1566c876910606c73ff07fedd09a3b038d33b1df06cb26af39a07bc` |
| #7 | `d4bfd37e2a74caae51a192af5ff7d0510a39d308` | `763ff09006dd38e4aacd2f413700bb76f89a400ddbbd681b424988e66e5f2d7e` |
| #8 | `25b377fa159ea0f7e8a5381ea7aa26a75d91a8a0` | `1580ce150ba537d2e65ac6aa5ff9e715036b73bf32e7c3039e6b9582ecedad91` |


## H1 追加记录（2026-11-02）

#9 已通过新分支完整构建、实际 helper C 宿主条件／轮询／复制测试，以及新链接帧首过滤指令检查；远端完整源码树已与本地预期逐项核对。包含 #2 后新增三个文件，其中 dmaStartSound 仅移至 EWRAM 腾出 ITCM。完整 H1 机制和证据见 [h1_window_dma](../h1_window_dma/README.md)。

已实测组合 H1 SHA256 为 `7e77a51d32f2e7d34ac865b462dec887eb8fb9c582cb2c116c3c28ae26de48f6`；用户反馈“H1验证了 没问题”，未提供测试时长及分项。它保留 B3 原声音修复，不含 A2、SR2。

上游新移植 head 为 `d92e1eace6cb41d2abf0f43197ebd091a4c77710`，新 NDS SHA256 为 `44ab8ffdecfb85080663c3d65453a5a5e9139dc094d7d007a83e9f7aa37bff77`。此独立构建没有完整游戏重放或新实机验收，保持 Draft；不得与组合 H1 混淆。没有发布 NDS 二进制、合并旧 PR 或升级基线。

### H1 范围澄清

问题位于游戏全程共用的 ROM 缓存加载和 HBlank 服务路径，不局限于洞穴地图；光圈只是异常更显眼的观测场景。其他阶段是否出现可见异常取决于缓存未命中、临界区与逐行任务的重叠。当前量化验证仍限大小光圈，H1 的维护也只接受已审计窗口 DMA0 配置，不能解释为其他效果或全部时序问题均已修复。见 [范围说明](../h1_window_dma/SCOPE.md)。


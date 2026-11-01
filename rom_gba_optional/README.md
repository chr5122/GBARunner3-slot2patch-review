# 补丁模式可不放根目录占位 `rom.gba`（试验）

供 **卧看（Wokann）** 审阅。slot2patch 方案的作者是卧看，上游仓库是 [Wokann/GBARunner3](https://github.com/Wokann/GBARunner3)，分支 `cache-hicode/slot2patch`。这里是试验记录，供合并前先看，不向该仓库开合并请求。

本目录没有 BIOS、游戏 ROM、游戏补丁或存档。

## 基底

v1 = 卧看提交 `f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9` + G1 DMA 回绕 + bootstrap 拷贝长度写死 `130660`。

试验记录里的对照 NDS 与本仓库已记录的 G1_DMA_WRAP 哈希相同：227840 B，SHA-256 `eefe98a0d2369d18a78e02450e56a50a45c79e20b8f4887e2d1adc1e4063502d`。记录称对照文件未改。

## 现象

从烧录卡菜单直接启动时通常没有传入 ROM 路径，于是打开 `/rom.gba`。补丁模式下这个文件只是占位，ROM 字节来自槽 2 卡带。v1 在 `loadGbaCart` 里打不开它就停机，停机码 12（`X1_NO_LAUNCH_FILE`），停在 GBR3 logo。

这次试验只想去掉这一条：补丁模式从菜单直接启动时，不再要求 SD 根目录放占位 `rom.gba`。改动只在 `loadGbaCart`。

## 改动

见 [trial_vs_v1.diff](trial_vs_v1.diff)。

- 打得开 `rom.gba`：仍做 sd2M / sd4M 两次诊断读取，路径与 v1 相同。
- 打不开：把 `gFile.obj.fs` 指到已经挂载的 `gFatFs`，并跳过这两次诊断读取。
- 没有新增 SD 写入。
- 卡带 game code 不匹配时，原有 `handleSave` 仍在打开任何 SD 存档之前以停机码 15（`X1_SD_SAVE_FALLBACK`）停下。这次 diff 没有改这段。默认路径下，文件名字符串会先变成 `/rom.sav`，但停机发生在打开它之前。模拟器跑不出不匹配卡带，这一点是对照源码，不是模拟结果。

## 模拟器记录

只在 melonDS 里跑过。尚未在真机上测试。

| 用例 | 结果 | 停机/运行标记 | SD 读 | SD 写 | 卡带存档 |
|---|---|---|---|---|---|
| a. v1，无 `rom.gba` | 停在 logo | `0xC`（停机码 12） | 80 | 0 | 无变化 |
| b. 试验版，无 `rom.gba` | 进到训练家卡片，与 c0 逐像素相同 | `0xD2B003` | 11260 | 0 | 无变化 |
| c. 试验版，有 `rom.gba` | 与 c0 相同 | `0xD2B003` | 11276 | 0 | 无变化 |
| c0. v1，有 `rom.gba`（基线） | 进到训练家卡片 | `0xD2B003` | 11276 | 0 | 无变化 |
| b2. 试验版，无 `rom.gba`，拷贝长度按写死的 130660 | 与 b 相同 | `0xD2B003` | 11260 | 0 | 无变化 |

b 比 c 少 16 次 SD 读。试验记录把这 16 次算作被跳过的两次 sd2M / sd4M 诊断读取。

截图在 [screenshots/](screenshots/)。`card0` 是训练家卡片，`frame_360` 是开机标志，`frame_1080` 是标题画面。`b`、`b2`、`c`、`c0` 的同名截图字节相同。`a_*` 三张也是同一张诊断计数画面。

## 这次没有动的旧问题

bootstrap 仍按写死的 130660 B 拷贝。试验版核心是 130888 B，有 228 B 没有拷到。v1 核心是 130832 B，当时已经有 172 B 没有拷到。b2 只说明在这个拷贝长度下，模拟器里仍能进到训练家卡片。实机还没有看。

构建环境、工具链和模拟器配置见 [BUILD_INFO.txt](BUILD_INFO.txt)。

## 试验 NDS

`GBARunner3_slot2patch_v1_romopt_trial.nds`：227840 B，SHA-256 `592e01ae2feaa708b660cee1cb499890224861794093c62387af3d5a37766699`。

沿本仓库惯例，NDS 不提交。需要这个文件时索取。

本目录其余文件的 SHA-256 在 [SHA256SUMS](SHA256SUMS)。在本目录执行 `sha256sum -c SHA256SUMS` 可以核对它们。该清单不含自身；自身哈希记在仓库根的 `SHA256.json`。

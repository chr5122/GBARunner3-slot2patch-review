# slot2patch 补丁打包工具 v2

基于卧看（Wokann）PatchTool 的 slot2patch 补丁打包工具 v2。差分格式与 PatchTool 作者为 **卧看微尘（Wokann）**，原仓库：[Wokann/PatchToolForGbaR3](https://github.com/Wokann/PatchToolForGbaR3)。打出的补丁供 [Wokann/GBARunner3](https://github.com/Wokann/GBARunner3) 的 slot2patch 使用。本目录在上述工具上做封装、LR 返回地址扫描与打包。

**本文件夹供卧看审核。** 放在本材料仓库中，供作者查看，不代表上游已经采纳。

## 功能

在界面点 **「生成」** 时，会先自动深度扫描 LR（返回地址）地址问题，并按 **高 / 中 / 低** 风险分级：

- 没有高风险或中风险：直接生成 slot2patch ZIP。
- 有高风险或中风险：弹出列表窗口，列出风险、地址和说明。可选择 **修复**、**不修复（直接生成）** 或 **取消**。
- 选择修复后，再生成 slot2patch ZIP。
- 可选同时导出 BPS 和报告（含修复后 ROM，仅本地自测；请分发 BPS / ZIP）。

更细的操作、命令行和已知限制见 [src/使用说明.md](src/使用说明.md)，打包参数见 [src/README.md](src/README.md)。

## 界面截图

有高 / 中风险时弹出的选择窗口：

![发现返回地址问题，可选择修复、不修复或取消](merge3_dialog.png)

不修复、直接生成后的主界面：

![已生成（未修复）](merge3_direct.png)

修复后生成的主界面：

![已生成（修复了 7 处）](merge3_fixdone.png)

## 目录

| 路径 | 内容 |
|---|---|
| `src/` | 源码、界面脚本、卧看 PatchTool 源码与 Windows 差分工具 `PatchToolForGbaR3.exe`、`_gba/configs/` |
| `release/slot2patch工具_mac_arm64.zip` | Mac arm64 独立 `.app`（`slot2patch工具.app`），压缩包原样存放，未再解压 |
| `merge3_*.png` | 上面三张界面截图 |
| `SHA256SUMS.txt` | Mac 压缩包的 SHA256 |

Mac 压缩包 SHA256（已核对，与 `SHA256SUMS.txt` 一致）：

```
95a54c53d2dabd43c977eb11bbb4a323f3158e35486ffcc69f3f133d68792978  slot2patch工具_mac_arm64.zip
```

## 使用与限制

- **Mac 版**内置 Python 3.12 和 Tk 9，不需要另行安装 Python。解压 ZIP 后打开 `slot2patch工具.app`。
- **Windows 图形界面 exe 尚未构建。** `src/build_windows.bat` 只是打包脚本。源码可在安装 Python 3（含 Tcl/Tk）后用 `src/打开界面.bat` 启动；目录中的 `PatchToolForGbaR3.exe` 是差分工具本体。
- **未经 Apple 公证。** 首次打开若被系统拦截，请在 Finder 中对 `slot2patch工具.app` 右键 → 打开。
- **未经充分实机验证。** 扫描和修复结果请先自行在 GBARunner3 实机上确认。
- **不提供 ROM、BIOS、NDS**，也不含完整 GBR3 教程。游戏 ROM 请自备。公开完整实机教程前请先征得卧看同意。

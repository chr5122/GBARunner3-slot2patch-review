# slot2patch 补丁打包工具 v2

本文件夹是基于卧看（Wokann）PatchTool 的 **slot2patch 补丁打包工具 v2**，供卧看审核。

差分格式与 PatchTool 作者是 **卧看微尘（Wokann）**。原仓库：[Wokann/PatchToolForGbaR3](https://github.com/Wokann/PatchToolForGbaR3)。GBARunner3 的 Slot-2 外挂补丁来自 [Wokann/GBARunner3](https://github.com/Wokann/GBARunner3)。本工具在卧看 PatchTool 上做调用封装、LR 地址扫描和打包，补丁格式本身来自卧看。

## 功能

在界面里点 **「生成」** 时，会先对汉化 ROM 做一次 **LR 地址问题深度扫描**，并按风险分级：

- **高**：在用，且 LR 未换算
- **中**：可疑，需要判断
- **低**：没找到调用者，或更像误报

没有高风险或中风险时，直接生成 slot2patch ZIP。有高风险或中风险时，弹出列表窗口，列出风险、地址和说明，可选择：

- **修复**
- **不修复**（直接生成）
- **取消**

选择修复后，再生成 slot2patch ZIP。界面上还可以勾选 **同时导出 BPS 和报告**。

界面截图：

| 文件 | 内容 |
|---|---|
| [merge3_dialog.png](merge3_dialog.png) | 高 / 中风险列表，以及修复、不修复、取消 |
| [merge3_direct.png](merge3_direct.png) | 无高 / 中风险时直接生成 |
| [merge3_fixdone.png](merge3_fixdone.png) | 修复后生成完成 |

更细的操作、命令行和修复方式见 [src/使用说明.md](src/使用说明.md) 与 [src/README.md](src/README.md)。

## 目录

| 路径 | 内容 |
|---|---|
| `src/` | 源码、界面脚本、卧看 `PatchToolForGbaR3.c`、Windows 用 `PatchToolForGbaR3.exe`，以及 `_gba/configs/` 下的游戏配置 JSON |
| `merge3_*.png` | 上面三张界面截图 |
| `SHA256SUMS.txt` | Mac 发布 zip 的 SHA256 |
| `release/slot2patch工具_mac_arm64.zip` | Mac arm64 独立 `.app`（未拆包） |

## 怎么用

**Mac（Apple 芯片 / arm64）**

1. 解压 `release/slot2patch工具_mac_arm64.zip`。
2. 打开里面的 `slot2patch工具.app`。
3. 应用内置 **Python 3.12** 和 **Tk 9**，不需要另行安装 Python。

这个 Mac 包 **没有做 Apple 公证**。第一次打开如果被系统拦住，在 Finder 里对该 `.app` **右键 → 打开**。

**Windows**

独立的 Windows 图形界面 exe **尚未构建**。`src/PatchToolForGbaR3.exe` 只是卧看差分工具的 Windows 可执行文件，不是本工具的完整安装包。当前可在已安装 Python 3 和 Tcl/Tk 的 Windows 上运行 `src/` 里的脚本；打包脚本是 `src/build_windows.bat`（需要 Python 3.12）。

## 范围

- 未经充分实机验证。生成或修复之后，请自行在实机上确认。
- 本文件夹不提供 ROM、BIOS 或 NDS，请自备合法的原版与目标 ROM。
- 不含完整 GBR3 教程。公开完整实机教程前，请先征得卧看同意。
- 放在本审核仓库，供卧看审阅；不代表上游已经采纳。

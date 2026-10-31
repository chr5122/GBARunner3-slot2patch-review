# GBA slot2patch 一键打包（自用）

把「原版 `.gba` + 汉化／目标 `.gba`」打成卧看微尘 GBARunner3 用的 `_gba/titles/<identity>.patch` 发布 ZIP。

适用于火红／叶绿／绿宝石等；**不宣称** GBR3 已正式支持任意 ROM。差分过大或实机未验证时仍可能失败。

## 署名

- 差分格式与 [PatchToolForGbaR3](https://github.com/Wokann/PatchToolForGbaR3) 作者：**卧看微尘（Wokann）**
- 本目录脚本只封装调用、校验与打包，**不是**自研补丁格式
- 完整 GBARunner3 实机教程请先征得卧看同意再公开

## identity 规则

```
identity = GameCode(ROM 偏移 0xAC 起 4 字节 ASCII) + Rev(ROM 偏移 0xBC，两位大写十六进制)
```

例：`BPRJ00`（火红日版 Rev0）、`BPGJ00`（叶绿）、`BPEJ00`（绿宝石）。SD 路径：`_gba/titles/<identity>.patch`。不要把 `.patch.json` 拷进 SD／ZIP。

## 硬限制

1. **原版与汉化 GameCode 必须相同**（脚本会拦）。
2. **差分块数 ≥ 4096** 时脚本中止：PatchTool／GBR3 有块数上限（经验约 4096）。全量错位类差分（例如部分红宝石日美）不适合 slot2patch，可考虑 **slot2save**。
3. 不保证任意 ROM 实机能跑；本包不是完整 GBR3 教程。

## 文件一览

| 文件 | 作用 |
|------|------|
| `slot2patch_core.py` | 跨平台打包核心（Windows／macOS／Linux） |
| `gui_slot2patch.py` | 图形界面（优先调 core） |
| `打开界面.bat` / `Open GUI.bat` | **Windows** 双击启动界面 |
| `打开界面.command` | **macOS** 双击启动界面 |
| `make_slot2patch.sh` | 命令行入口（有 core 时转发到 Python） |
| `make_frlg_slot2patch.sh` | 火红／叶绿兼容入口 |
| `PatchToolForGbaR3.exe` | Windows 差分工具（已交叉编译时可直接用） |
| `PatchToolForGbaR3` | macOS／Linux 可执行文件（或符号链接） |
| `PatchToolForGbaR3.c` | 源码；缺 exe 时自行编译 |

## Windows 用法（图形界面）

1. 安装 [Python 3](https://www.python.org/downloads/)，勾选 **Add python.exe to PATH** 和 **tcl/tk and IDLE**。
2. 确认本目录有 `PatchToolForGbaR3.exe`（本包若已附带可跳过）。没有就编译（见下）。
3. 双击 **`打开界面.bat`**（或英文名 **`Open GUI.bat`**）。若被拦截：右键 → 属性 → 解除锁定，或「仍要运行」。
4. 在窗口里选「原版 .gba」「汉化 .gba」，填版本号，点 **生成**。
5. 成功后点「打开所在文件夹」，把 ZIP 里的 `_gba` 合并到 SD 根目录。

命令行（不强制 Git Bash）：

```bat
py -3 slot2patch_core.py --orig 原版.gba --cn 汉化.gba --version "v1.13" --name Emerald
```

### 编译 PatchTool（Windows，仅缺 .exe 时）

安装 [MinGW-w64](https://www.mingw-w64.org/) 或 MSYS2 后，在本目录执行：

```bat
gcc PatchToolForGbaR3.c -o PatchToolForGbaR3.exe -O2 -std=c99 -Wall
```

MSVC 也可用，保持 C99 即可。把得到的 `PatchToolForGbaR3.exe` 放在本目录。

## macOS／Linux 用法

双击 **`打开界面.command`**（macOS；若提示无法打开：右键 → 打开），或：

```bash
cd /path/to/frlg_slot2patch_tool
python3 gui_slot2patch.py
# 或命令行：
./make_slot2patch.sh --orig 原版.gba --cn 汉化.gba --version "v1.13" --name Emerald
python3 slot2patch_core.py --orig 原版.gba --cn 汉化.gba --version "v1.13"
```

编译原生工具：

```bash
gcc PatchToolForGbaR3.c -o PatchToolForGbaR3 -O2 -std=c99 -Wall
```

## 参数

| 参数 | 作用 |
|------|------|
| `--name NAME` | ZIP／说明里的友好名（默认：已知码表 FireRed／LeafGreen／Emerald／Ruby／Sapphire，否则用 GameCode） |
| `--out DIR` | 输出目录 |
| `--tool PATH` | PatchTool 可执行文件 |
| `--force-orig` | 原版 SHA 与内置 No-Intro Rev0 表不符时仍继续（仅 BPRJ／BPGJ／BPEJ 会硬拦；其它码只警告） |
| `--skip-verify` | 跳过 apply 还原核对（不推荐） |
| `--game firered\|leafgreen\|emerald` | 可选提示，校验与 GameCode 一致 |

## 产出

ZIP 内含：

- `_gba/titles/<identity>.patch`
- `PATCH_INFO.json`（原版／目标／补丁 SHA、块数）
- `SHA256.txt`
- `使用说明.md`（短说明，不是完整 GBR3 教程）

ZIP 文件名：日版（GameCode 第 4 位为 `J`）→ `{Name}_JP_CN_{ver}_slot2patch.zip`；其它区 → `{Name}_{identity}_{ver}_slot2patch.zip`。

## 自测记录

- 2026-10-26：日版火红 Rev0 + 由旧包还原的 2.2.1／BUILD0105 重打，补丁 SHA 与参考包一致：`7855575875417ec88d362d5402e135a2271ec6c843e4305ed6d0be01db419f39`。
- 2026-10-26：绿宝石日版 + jp_chs v1.13 → `BPEJ00.patch` SHA：`5f2b37897367e9bdc78c8a460053a10b518d647c6ec464378fa89dcb2b0bd3bb`。
- 2026-10-26：跨平台核心 `slot2patch_core.py` 重打，上述两 SHA 对齐；附 Windows `PatchToolForGbaR3.exe`（mingw-w64 交叉编译）与 `打开界面.bat`。

## v2 新增：LR 深度扫描

见 `使用说明.md`。界面点“生成”时会先自动深度扫描，有高／中风险会弹出问题列表窗口（勾选后 修复／不修复／取消），结果显示在主界面；也可用 `lr_scan.py` 命令行可扫描并按 高／中／低／已修 分级，勾选后修复并生成 BPS、报告和 slot2patch 包。

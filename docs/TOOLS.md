# 电脑端 slot2patch 工具

[返回首页](../README.md) · [patch 模式](PATCH.md) · [作者审阅](REVIEW.md)

这是生成专用 `.patch` 的电脑工具，不是 NDSL 上运行的 `.nds`，也不是完整游戏 ROM。差分格式和 PatchToolForGbaR3 来自 Wokann（卧看微尘），这里增加界面、打包、返回地址风险扫描和可选修复。

## 当前版本与获取入口

采用已合入 main 的 PR #5。旧 PR #4 已关闭，由 #5 替代；原提交及旧包仍可通过历史记录查找。

- [工具说明与截图](../slot2patch_tool_v2/README.md)
- [源代码](../slot2patch_tool_v2/src/)
- [Mac Apple 芯片工具 ZIP](../slot2patch_tool_v2/release/slot2patch工具_mac_arm64.zip)
- [Windows x64 工具 ZIP](../slot2patch_tool_v2/release/slot2patch工具_windows_x64.zip)
- [两个 ZIP 的校验值](../slot2patch_tool_v2/SHA256SUMS.txt)
- [操作与已知限制](../slot2patch_tool_v2/src/使用说明.md)

这是仓库中已有的工具包，本轮未重新打包，也没有建立正式 Release。下载单个 ZIP 时使用 GitHub 文件页的下载按钮；它们不是缺失的 GBR3 NDS 下载入口。

## 配置要另外准备

PR #5 默认生成的补丁 ZIP **不再附带 `_gba/configs/`**，只有显式使用 `--configs DIR` 才加入。已有源码目录保留的 301 个配置，不代表每一款汉化 ROM 都已验证；不要用旧包覆盖自己已测试的游戏配置。

## 验证范围

本轮核对了 #4/#5 的逐文件差异：原有 301 个配置相同，旧版遗漏项只有三个 Python 字节码缓存；新版另有 Windows 包及构建流程。Python 源码语法、两个后端的帮助和缺参数检查通过。

现有 Windows 包的构建冒烟记录见原工具说明。本轮没有重新下载校验两个二进制 ZIP，也没有对自动修复器做完整独立代码审计或新增实机回归，不据此扩充原验证结论。

风险分级是候选提示，可能误报、漏报；可选修复也仅覆盖工具能处理的部分模式。优先使用汉化作者已验证的成品，修改代码后应另行回归。生成／还原检查通过与实机兼容是两回事。

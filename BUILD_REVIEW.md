# 如何核对这份源码差异

本仓库不是可独立构建的完整 checkout。先从 Wokann/GBARunner3 获取固定提交和子模块，再应用 **20_FULL_vs_f8ac25c_review.patch**。

```sh
git clone https://github.com/Wokann/GBARunner3.git
cd GBARunner3
git checkout f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9
git submodule update --init --recursive
git apply --check /path/to/20_FULL_vs_f8ac25c_review.patch
git apply /path/to/20_FULL_vs_f8ac25c_review.patch
```

libtwl 固定提交应为 e069645bed14a93e149e873e9273f04851e3a04e。
完整差异含所有新增源文件、font include 和 linker 修改；没有游戏 ROM、PRE、BIOS 或存档。
不要再应用 D1 → D2 的 10_ patch，两个是不同基准的替代视图。

沿用上游 Makefile 和 devkitARM/libnds/libtwl 构建方式（code/ 下 make）。
实测候选使用本地 devkitARM r65/GCC 14.2、libnds 1.8.3、ndstool 2.3.1；原上游 CI 镜像为 devkitpro/devkitarm:20241104。
本仓库不安装/分发 SDK。不同工具链输出和菜单 banner 不保证二进制同哈希；实测 NDS 的菜单标题在链接后另行定制。

重编译不是自动继承实测结论：本构建 VRAM 尾部余量仅 268 B，EWRAM 代码距原 BSS 起点仅 56 B。
必须核对 ELF/map 段界限、2 KiB hicode 对齐、关键 EWRAM BSS 地址、1 MiB cache、20 KiB heap 和栈使用，再做独立实机短测。
本包的 PATCH_VERIFICATION.json 证明差异 apply 后内容正确，不是新工具链构建/运行已经成功的保证。

source/ 目录只是变更文件的网页阅读副本，非完整构建树。
构建/主机/布局检查的说明见 IMPLEMENTATION.md；907 条检查多数是逐文件校验，不是 907 个实机场景。

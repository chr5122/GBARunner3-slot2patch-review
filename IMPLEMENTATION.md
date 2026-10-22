> Historical build-time document. Later user field feedback is recorded in FIELD_TESTS.md; do not mistake the pre-test status below for the current feedback.

# D2 AUTO PRE — 启动自动缓存实验候选，尚未实机验证

## 交付与父本

文件：d2_output/D2_AUTO_PRE.nds，227328 B。

SHA-256：7965f4b1a2381a7ad325b1c618cc3b3511fc1287489291243cc8e296ddf6f76b。

直接父本 D1_SLOT2PATCH.nds：cb0ef2f1b393ed368abc2838dfdbda1873bb57b07c05628d172773ab8b475749。
上游 Wokann cache-hicode/slot2patch：f8ac25cc8c79ec5a4c624cbd94eeed9e2d1842c9。
本版不含 X2/FatFs 替代热读取、X3/扩大簇表或 X4/单次日志实验。
不是作者的正式发行版，不能将 D1 的实机结果自动算作 D2 已通过。

用户已经确认 D1 运行约 20 分钟正常、保存测试成功。X1 约 40 分钟运行及保存/重启/原生 GBA 模式读档曾通过。
D1 原生 GBA 模式读回未在本轮单独确认。D2 尚无实机结果。

## 行为

1. 已有 .pre 通过继承的头部、补丁哈希、ROM 抽样哈希、长度、索引及簇表校验：直接只读打开，完全不调用生成器、mkdir、rename 或写盘许可。
2. 缺失或失效：检查同名 .tmp 是否存在；若需替换旧 .pre，再检查 .bak 是否存在。出现残留/冲突就停止，不覆盖它们。
3. 唯一一次启动写入窗口打开后，以 FA_CREATE_NEW 新建临时 .tmp，绝不截断正式 .pre。
4. 生成各个 4 KiB 补丁块：正版卡原始块（越界为 FF）加原有 IPS 解析。先写 valid=0；完整 payload f_sync 成功后才提交临时头部 valid=1，再 sync、close。
5. 临时文件以只读方式重开，继承元数据和簇表校验；逐块从正版卡＋补丁重新计算预期内容，通过实际运行期 raw-sector lookup/read 路径读回全部块，比对完整 4096 B。
6. 读回缓冲先填入预期数据的逐字节反码，flush/drain 后才调用读路径，避免“驱动没读、旧缓存恰好相同”冒充成功。
7. 关闭只读临时句柄、取消有效映射；若有旧 .pre，先重命名为 .bak，再将 .tmp 重命名为正式 .pre。两次返回值逐项检查，旧文件不删除。
8. drain 所有已发 I/O 并永久关闭写入窗口；只读重开正式 .pre 并再次验证。没有 on-demand patch 回退。
9. main 在 handleSave 和 VirtualMachine.Run 之前 seal 写入状态，之后不能再次开启。

运行期继续禁止 SD 日志、写盘心跳及 SD 存档回退。正版卡存档代码保持原样，卡带仍可写。
生成的新缓存沿用原 PRE 格式版本 2（实际头部 20 B，不采纳旧注释的 16 B），没有新文件格式或文本修改。
已有缓存的 warm 路径仍是原元数据校验，不新增全 payload 检查；全量读回比较只用于本次新生成的临时文件。

## 写入范围与失败保护

源码实际新增的文件变更操作仅在 /_gba/prepatch/：mkdir、排他创建对应 .tmp、写入该 .tmp、必要时 .pre → .bak、.tmp → .pre。
不会删除旧缓存，不写游戏 ROM、BIOS、配置、日志、SD .sav 或固件。未新增驱动复位、时钟、电压、硬件计时器和固件操作。
disk_write 仅在 boot-open 状态允许 DEV_FAT/DEV_SD；DEV_PC 始终拦截。FS IPC 的两个写扇区命令在发送前再次检查相同状态。
状态借用原有自有诊断 reserved[2]，没有新永久 RAM：0(closed) → OPEN → CLOSED → SEALED；warm 为 0 → SEALED。
错误停止会把该字改成错误码，使许可立即失效。begin 只接受 0，一次运行不能重开。

限制：这是启动阶段的阶段门禁，不是按文件路径鉴权的通用文件系统沙箱。
阶段中已有 IRQ 及非重入 FatFs 环境未改变，但日志/心跳禁用；测试不能证明任何任意新增调用都不会写其他文件。
TWiLight、注入 DLDI 的 startup 内部、底层驱动未知副作用不在“运行器源码范围零写”的证明内。
ARM7 仍继承忽略 DLDI bool 返回值的问题；全量读回可以发现很多写入错误，不等于硬件持久化保证。

**FAT 两次重命名不是抗断电的原子事务。** 若中途断电，可能剩 .tmp/.bak 或发生文件系统损坏，不能保证自动恢复。
失效缓存重建会改变 SD 内容，必须先备份；生成时保持电量充足，不热插拔、不在写入过程中关机。
如果 .tmp 已存在、需要保留旧 .pre 而 .bak 已存在，主动停止，请用户先在电脑检查/备份，不自动清理。

## 布局与栈

仅 7 个源文件不同：main.cpp、PerfScreen.cpp、X1Readonly.h、Fat/diskio.cpp、Fat/FsIpc.cpp、Patches/ExternalPatch.cpp/.h。
原解析器、原 ROM/source hash、runtime raw-sector lookup、保存/FLASH/EEPROM/SRAM、Game Code 门禁、ARM7 和 bootstrap 保持。
validator 除可选临时文件路径及临时变量存储位置外，可独立还原到 D1 的相同校验逻辑。

启动首次缓存读取之前，复用已分配但未发生 cache fetch 的 SD-cache blocks：

- 0：源块、补丁计算、hash scratch（继承）
- 1：逐块 raw-sector 读回比较缓冲
- 2：生成器文件名、FILINFO、临时头部
- 3：validator 的临时路径、头部、索引 entry

blocks 2/3 的结构均 static_assert 不超过一个块；不新增 4/8 KiB BSS 或 heap 分配。
缓存初始化先于生成，后续实际 cache load 会覆盖 scratch；原映射有效信息保存在既有 BSS 簇表而不是这些 scratch。

D1 的所有 EWRAM BSS 对象地址/大小保持一致；gGbaSaveShared 0x0204E780、gJitState 0x02056CCC、
诊断状态 0x02044000 / 1244 B、hicode buffer 0x020F9000 / 2 KiB 对齐、1 MiB cache 0x020FB000、
heap 0x021FB000..0x02200000 / 20 KiB，IRQ/DTCM 栈布局不变。
普通 VRAM BSS 因新增 FatFs 函数链接发生重新定位，由链接器解析引用，不能声称所有地址都未变。
最终普通 VRAM 尾部余量 268 B，EWRAM 代码距原 BSS 起点余量 56 B，空间非常紧，重编译必须重跑布局验证，不允许盲加代码。

中间草稿被检查挡下：普通 VRAM 越界、EWRAM 代码跨对齐边界、生成器局部 FILINFO 导致 600 B 栈帧。均未上传。
现版将临时对象放入既有 cache scratch；最终编译器栈报告需以 stack_audit/results.json 的 d2 为准。
Boot main 224 B、TryLoad 120 B、BakePrepatch 88 B、TryLoadPrepatch 48 B；f_rename 168 B（不含其调用者和下游）。
这些是静态单函数帧，不是完整启动/IRQ 最大用栈或实机 watermark 的证明。

## 验证与复现资料

64 个生成/故障/阶段主机场景＋26 个 IPC/disk 写门禁场景，ASan/UBSan 通过。
覆盖成功后 warm 零写、保留旧文件、每个主机 API 失败位置、短写、raw 错误/无读取、簇表失败、残留 tmp/bak、设备/簇尺寸、块数等。
主机运行实际生成器、validator、raw-sector mapping 和写 gate 的源码，底层文件系统为内存 API doubles，不是真实 FatFs/DLDI/DS 仿真，也没有断电仿真。

907 项独立检查通过，大部分为逐个父源文件校验，并非 907 个运行场景。
检查器不导入 builder：固定 D1 源码包与 NDS 哈希，独立逆向还原差异、检查 permission 顺序、实际 ELF、内存/对齐/堆/段边界、禁用 VBlank 入口、ARM7 字节、NDS CRC/菜单。
所有结论绑定最终 NDS SHA，任何构建改动都需重新验证。

脚本：prepare_d2.py（独立导出）、build_d2.py、test_d2.py、verify_d2.py、audit_stack.py d2。
模板：D2Bake.inc、D2Gate.inc；主机 harness：d2_bake_host.cpp；结果：d2_build.json、d2_host_results.json、d2_verification.json、stack_audit/results.json。
沿用此前 SDK，没有全局安装，历史工具链镜像来源限制未改变。

## 实机判据

先测已有有效缓存启动：显示/流畅度/基本操作不得退步。
备份 SD、卡带存档和已有 PRE 后，再在电脑将对应 .pre 改为 .old（不可覆盖原有 .old），测试 cold 自动生成。
第一轮不保存；生成完后静置、走动、图鉴和菜单，关注恢复读 SD 是否白屏。
关机后检查新 .pre，第二次启动不应重建；验证 warm 行为与流畅度。
新的 SD 启动写入可能重现作者原有白屏规避问题，D2 主机通过不能推翻这一风险。
若异常，保留画面/阶段/文件列表，退回 D1，不反复删除文件强试。
最后有备份再单独测保存互通。不做强制断电测试、不写固件、不上传游戏/存档。

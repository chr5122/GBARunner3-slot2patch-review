# G1S+B3 测试包（未实机）
- 控制包 G1S_CTRL_REPRO.nds 逐字节复现 G1S_DMA_WRAP.nds（6c0420fd…d154，211968 B）
- 候选 G1S_B3_TEST.nds 74077023e82769f5a56fe8b091725d23042736d771b75df013d62aa196e30048，211968 B
- 源码差异 G1S_B3_vs_G1S.patch = B3 SOURCE.patch 内容一致
## melonDS（slot2save：CN v1.13 32MB ROM 在 SD，槽2 虚拟 JP 卡+128K flash 存档；观测只读）
| 配置 | 首翻帧数 | 窗口300帧 prefetch abort | hic_mapRomBlock 调用 | MSR/帧 |
|---|---|---|---|---|
| G1S 8地址 | 63 | 114851 | 46855 | 642 |
| G1S+B3 8地址 | 41 | 95666 | 21374 | 660 |
| G1S JIT关 | 41 | 82307 | 30983 | 3 |
| G1S+B3 JIT关 | 41 | 81186 | 21374 | 3 |
mapNewBlock 被内联，不能单独计数；用 hic_mapRomBlock 调用数代替。SD 写 0，存档变更 0。

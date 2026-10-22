> 随 G1 构建留下的 ARM9 链接 map 对比。下面各段的地址和长度已与当时的 arm9 map 段行核对。全文 map 含本机构建路径，未放入本仓库。
>
> `dmaStartSound` 没有出现在 map 的全局符号里。G1 的 `DmaTransfer.o` `.ewram` 位于 `0x02043c58`。摘要里的 `__dmaStartSound_veneer`（`0x00007f60`）来自当时的 nm 记录；map 中 `.itcm.__stub` 从 `0x00007f48` 起、长度 `0x88`，该地址落在这段里。

# Linker map summary: D2 vs G1 (arm9.map)
## D2
  .text           0x06800198     0xeaf8
  .itcm           0x00000000     0x7ff8 load address 0x06813ea4
  .ewram          0x02040000     0x3fc8 load address 0x0681be9c
  0x02043fc8                        __ewram_end = ABSOLUTE (.)
  .ewram.bss      0x02044000   0x1b7000 load address 0x0681fe64
  0x021fb000                        __ewram_bss_end = .
  0x021fb000                        __heap_start = .
## G1
  .text           0x06800198     0xeaf8
  .itcm           0x00000000     0x7fd0 load address 0x06813ea4
  .ewram          0x02040000     0x409c load address 0x0681be74
  0x0204409c                        __ewram_end = ABSOLUTE (.)
  .ewram.bss      0x02045000   0x1b7000 load address 0x0681ff10
  0x021fc000                        __ewram_bss_end = .
  0x021fc000                        __heap_start = .

## Notes
- ITCM: 0x7ff8 -> 0x7fd0 (region 32 KiB = 0x8000; D2 had 8 bytes free, G1 has 48).
- .ewram: 0x3fc8 -> 0x409c (+212 B; crosses 16 KiB), so .ewram.bss start (4 KiB aligned) moves 0x02044000 -> 0x02045000.
- .ewram.bss size unchanged (0x1b7000); end/heap start 0x021fb000 -> 0x021fc000; heap end fixed at 0x02200000
  (gbarunner9.ld:28) => heap ~20 KiB -> ~16 KiB.
- `dmaStartSound` (static, not listed in map) now in .ewram at 0x02043c58 (nm), called from ITCM via
  linker veneer `__dmaStartSound_veneer` at 0x00007f60.
- No hard-coded 0x02044000 found in sources/linker scripts/asm/ARM7; crt0.s and heap_init use linker symbols.

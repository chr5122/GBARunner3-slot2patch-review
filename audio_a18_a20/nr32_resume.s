.syntax unified
.cpu arm7tdmi
.arm

/* 03805eb4. r2 is previous NR32, r1 is new nonzero selector.
 * Active status and PCM encoding selector are 0x558 bytes apart.
 * Preserve the original refresh rule for previous nonzero NR32.
 */
    ldr     r0, [pc, #0x1bc]      @ 03806078 -> 03809b4c (channel status)
    cmp     r2, #0
    ldreq   r2, [r0]
    tsteq   r2, #4
    ldrne   r2, [r0, #-0x558]     @ 038095f4 (encoding currently in PCM)
    cmpne   r2, r1
    strne   r1, [r0, #-0x558]
    movne   r0, r1
    blne    . - 0x1180           @ 03804d54 (reencode existing buffers)
    b       . - 0x13c            @ 03805d9c (apply gain and return)

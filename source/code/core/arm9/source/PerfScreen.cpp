// Frozen readout experiment. Gameplay keeps the original capture/display path.
// No FPS, milliseconds, driver-error or complete cache-hit-ratio claims.
#include "PerfScreen.h"
#ifndef PERF_HOST_TEST
#include "X1Readonly.h"
#endif
#ifndef PERF_HOST_TEST
#include "common.h"
#include "Fat/FsIpc.h"
#include "Slot2Diag.h"
#include "SystemIpc.h"
#include "Save/Save.h"
#include "Application/Settings/AppSettingsService.h"
#include "cp15.h"
#define CODE __attribute__((section(".ewram"), noinline))
#define STATE __attribute__((section(".ewram.bss")))
#define CONST __attribute__((section(".perf.rodata")))
#define CONFIG __attribute__((used, section(".perf.data")))
#else
#define CODE
#define STATE
#define CONST
#define CONFIG
extern "C" void slot2DiagVblankHook(void);
#endif

struct PerfConfig { uint32_t magic[3]; volatile uint32_t enabled; uint32_t end; };
extern "C" {
CONFIG PerfConfig gPerfConfig={{0x33524650,0x30313230,0x32445253},0,0x21444e45};
}
struct LoadEvent { uint32_t block,source,state; };
struct PerfState {
    uint32_t active,ticks,uiFlags;
    uint32_t starts[4],done[4],slowHits,evictions,unique,reloads;
    uint32_t waitCalls,busyCalls,polls,maxPolls;
    uint32_t requests[5],sectorsRead,sectorsWritten,lastCmd,lastSector;
    uint32_t logCalls,syncCalls,eventHead;
    uint8_t seen[1024];
    LoadEvent events[4];
    uint32_t scope,scopePolls[3],scopeBusy[3],waitDepth,reserved[4];
};
static STATE PerfState s;
static_assert(sizeof(PerfState)==1244);
static_assert(__builtin_offsetof(PerfState,reserved)+16==sizeof(PerfState));
enum { ALLOWED=1,ARMED=2,FROZEN=4,SAMPLING=8,COMBO=(1u<<2)|(1u<<8)|(1u<<9),NO_BANK=4 };
static CODE bool enabled() { return s.active && (s.uiFlags&SAMPLING) && gPerfConfig.enabled==1; }
extern "C" CODE void perfScreenLoad(uint32_t block,uint32_t source,uint32_t state)
{
    if (!enabled() || source>=4 || state>1) return;
    if (!state) {
        ++s.starts[source];
        if (block<8192) {
            uint8_t mask=uint8_t(1u<<(block&7));
            if (s.seen[block>>3]&mask) ++s.reloads;
            else { s.seen[block>>3]|=mask; ++s.unique; }
        }
    } else ++s.done[source];
    s.events[s.eventHead&3]={block,source,state};
    ++s.eventHead;
}
extern "C" CODE void perfScreenSlowHit(void) { if (enabled()) ++s.slowHits; }
extern "C" CODE void perfScreenVictim(uint32_t block,uint32_t oldBlock)
{ (void)block; if (enabled() && oldBlock!=0xffff) ++s.evictions; }
extern "C" CODE void perfScreenWaitBegin(void) { ++s.waitDepth; }
extern "C" CODE void perfScreenWait(uint32_t polls)
{
    if (s.waitDepth) --s.waitDepth;
    if (!enabled()) return;
    ++s.waitCalls;
    unsigned scope=s.scope<3?s.scope:0;
    s.scopePolls[scope]+=polls;
    if (polls) ++s.scopeBusy[scope];
    if (polls) ++s.busyCalls;
    s.polls+=polls;
    if (polls>s.maxPolls) s.maxPolls=polls;
}
extern "C" CODE void perfScreenRequest(uint32_t cmd,uint32_t sector,uint32_t count)
{
    if (!enabled()) return;
    if (cmd<5) ++s.requests[cmd];
    if (cmd==1 || cmd==3) s.sectorsRead+=count;
    if (cmd==2 || cmd==4) s.sectorsWritten+=count;
    s.lastCmd=cmd;s.lastSector=sector;
}
extern "C" CODE void perfScreenLog(void) { if (enabled()) ++s.logCalls; }
extern "C" CODE void perfScreenSync(void) { if (enabled()) ++s.syncCalls; }

// Scope attribution counts ONLY software poll iterations, never elapsed time.
extern "C" CODE uint32_t perfScreenEnterScope(uint32_t scope)
{
    uint32_t old=s.scope;
    if (s.active && gPerfConfig.enabled==1) s.scope=scope<3?scope:0;
    return old;
}
extern "C" CODE void perfScreenLeaveScope(uint32_t old)
{
    if (s.active && gPerfConfig.enabled==1) s.scope=old<3?old:0;
}
static CODE void beginSample()
{
    // Owned diagnostic object only; volatile byte loop avoids libc/FS imports.
    volatile uint8_t* bytes=reinterpret_cast<volatile uint8_t*>(&s);
    for (unsigned i=0;i<__builtin_offsetof(PerfState,reserved);++i) bytes[i]=0;
    s.active=1;s.uiFlags=ALLOWED|SAMPLING; // must release keys before stop
}

// This generated include reuses the previously tested original 5x7 patterns.
#include "freeze_font.inc"
static CODE unsigned glyph(char c)
{
    if (c>='0' && c<='9') return c-'0'+1;
    if (c>='A' && c<='Z') return c-'A'+11;
    return 0;
}
static CODE void character(volatile uint16_t* fb,unsigned row,unsigned col,char c)
{
    unsigned g=glyph(c);
    for (unsigned y=0;y<7;++y) for (unsigned x=0;x<5;++x)
        if (font[g][y]&(1u<<(4-x))) fb[(row*8+y)*256+col*8+x]=0xffff;
}
static CODE void label(volatile uint16_t* fb,unsigned row,const char* text)
{
    for (unsigned col=0;col<32 && text[col];++col) character(fb,row,col,text[col]);
}
static CODE void number(volatile uint16_t* fb,unsigned row,unsigned col,uint32_t value)
{
    for (int x=7;x>=0;--x) { character(fb,row,col+x,char('0'+value%10));value/=10; }
}
static CONST const char rowText[]=
 "D2 SD PRE BAKE\0"
 "FROZEN POWER OFF\0"
 "CART LOAD\0"
 "PRE LOAD\0"
 "SD LOAD\0"
 "OOB FILL\0"
 "UNIQUE          RLOAD\0"
 "EVICT           SLOW\0"
 "WAIT CALLS\0"
 "BUSY CALLS\0"
 "POLL SUM\0"
 "POLL MAX\0"
 "SD READS\0"
 "SD WRITES\0"
 "SECTORS R\0"
 "SECTORS W\0"
 "BOOT SD READS\0"
 "WRITE ATTEMPTS\0"
 "STOP CODE\0"
 "PRE VERIFIED\0"
 "LOG POLLS\0"
 "PRE POLLS\0"
 "OTHER POLLS\0"
 "VBLANKS\0"
;
static CONST const uint16_t rowOffsets[]={0,15,32,42,51,59,68,90,111,122,133,142,151,160,170,180,190,204,219,229,242,252,262,274};
static CODE void draw(volatile uint16_t* fb)
{
    for (unsigned i=0;i<256*192;++i) fb[i]=0x8000;
    for (unsigned r=0;r<24;++r) label(fb,r,rowText+rowOffsets[r]);
    number(fb,2,23,s.starts[0]);number(fb,3,23,s.starts[1]);
    number(fb,4,23,s.starts[3]);number(fb,5,23,s.starts[2]);
    number(fb,6,7,s.unique);number(fb,6,24,s.reloads);
    number(fb,7,7,s.evictions);number(fb,7,24,s.slowHits);
    number(fb,8,23,s.waitCalls);number(fb,9,23,s.busyCalls);
    number(fb,10,23,s.polls);number(fb,11,23,s.maxPolls);
    number(fb,12,23,s.requests[1]+s.requests[3]);
    number(fb,13,23,s.requests[2]+s.requests[4]);
    number(fb,14,23,s.sectorsRead);number(fb,15,23,s.sectorsWritten);
    for (unsigned i=0;i<4;++i) number(fb,16+i,23,s.reserved[i]);
    number(fb,20,23,s.scopePolls[1]);number(fb,21,23,s.scopePolls[2]);
    number(fb,22,23,s.scopePolls[0]);number(fb,23,23,s.ticks);
}
// Pure predicate: use ONLY the free LCDC capture bank, not the displayed bank.
static CODE unsigned chooseBank(uint32_t c,uint32_t d,uint32_t capture,uint32_t ipc,uint32_t saveState)
{
    if ((capture&0x80000000) || saveState || (((ipc>>8)^ipc)&15)) return NO_BANK;
    if (c==0x80 && d==0x84) return 2;
    if (c==0x84 && d==0x80) return 3;
    return NO_BANK;
}
static CODE bool wantsSnapshot(uint32_t keys)
{
    if ((keys&COMBO)!=0) { s.uiFlags|=ARMED;return false; }
    return (s.uiFlags&(ALLOWED|ARMED))==(ALLOWED|ARMED);
}

#ifndef PERF_HOST_TEST
[[noreturn]] static CODE void freeze(unsigned bank)
{
    // Called in VBlank IRQ only after eligibility checks, never resume the VM.
    *(volatile uint32_t*)0x04000208=0; // ARM9 IME only
    *(volatile uint32_t*)0x04000064=0; // completed capture stays stopped
    s.active=0;s.uiFlags|=FROZEN;
    auto fb=(volatile uint16_t*)(0x06800000+bank*0x20000);
    draw(fb);
    // LCDC is cached by this runner's MPU. Commit ONLY this free bank's pixels.
    dc_flushRange((void*)fb,256*192*2);
    dc_drainWriteBuffer();
    *(volatile uint32_t*)0x04000000=0x20000|(bank<<18); // main LCD framebuffer
    *(volatile uint16_t*)0x0400006C=0; // reveal the previously dimmed other LCD
    for (;;) asm volatile("nop");
}
#endif

extern "C" CODE void perfScreenInit(void)
{
    // D1: no sampling and no diagnostic backlight/display IPC at startup.
    // Keep the owned state allocation to preserve X1's live memory layout.
    s.active=0;s.uiFlags=0;
}
extern "C" CODE void perfScreenVblankHook(void)
{
    // D1: no key reads, sampling, heartbeat, or gameplay freeze entry point.
    return;
}

// Persistent boot audit words: reads, rejected writes, stop reason, validated pre.
extern "C" void x1CountRead(void) { ++s.reserved[0]; }
extern "C" void x1PreVerified(void) { s.reserved[3]=1; }
extern "C" bool x1HeartbeatEnabled(void) { return false; }
#ifndef PERF_HOST_TEST
extern "C" __attribute__((noreturn)) void x1Stop(uint32_t code)
{
    s.reserved[2]=code;
    unsigned bank=(*(volatile uint8_t*)0x04000242==0x80)?2:
                  (*(volatile uint8_t*)0x04000243==0x80)?3:NO_BANK;
    if (bank!=NO_BANK) freeze(bank);
    // Never reconfigure an unknown VRAM mapping to force an error display.
    *(volatile uint32_t*)0x04000208=0;
    for (;;) asm volatile("nop");
}
extern "C" __attribute__((noreturn)) void x1BlockedWrite(void)
{
    ++s.reserved[1];x1Stop(X1_WRITE_ATTEMPT);
}
#endif

// Four-state one-way boot write gate, using an existing owned diagnostic word.
// 0(initial, closed) -> OPEN -> CLOSED -> SEALED; warm boot goes 0 -> SEALED.
// No additional globals, game RAM, timers, clock or firmware operations.
extern "C" bool d2BootWritesAllowed(void) { return s.reserved[2]==0xD2B001u; }
extern "C" CODE void d2BeginBootWrites(void)
{
    if (s.reserved[2]!=0) x1Stop(48);
    s.reserved[2]=0xD2B001u;
}
extern "C" void d2EndBootWrites(void)
{
    if (!d2BootWritesAllowed()) x1Stop(48);
#ifndef PERF_HOST_TEST
    fs_waitForCompletionOfCurrentTransaction(false);
#endif
    s.reserved[2]=0xD2B002u;
}
extern "C" void d2SealRuntime(void)
{
    if (s.reserved[2]!=0 && s.reserved[2]!=0xD2B002u) x1Stop(48);
#ifndef PERF_HOST_TEST
    fs_waitForCompletionOfCurrentTransaction(false);
#endif
    s.reserved[2]=0xD2B003u;
}

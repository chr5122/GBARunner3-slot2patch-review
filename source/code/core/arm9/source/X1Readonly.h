#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
enum { X1_BAD_PRE=10,X1_NO_CART=11,X1_NO_LAUNCH_FILE=12,X1_BAD_PATCH=13,
       X1_APPLY_FAILED=14,X1_SD_SAVE_FALLBACK=15,X1_WRITE_ATTEMPT=20 };
void x1CountRead(void);
void x1PreVerified(void);
void x1BlockedWrite(void) __attribute__((noreturn));
void x1Stop(uint32_t code) __attribute__((noreturn));
bool x1HeartbeatEnabled(void);
bool d2BootWritesAllowed(void);
void d2BeginBootWrites(void);
void d2EndBootWrites(void);
void d2SealRuntime(void);
#ifdef __cplusplus
}
#endif

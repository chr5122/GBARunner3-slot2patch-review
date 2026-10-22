#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void perfScreenInit(void);
void perfScreenVblankHook(void);
void perfScreenLoad(uint32_t block, uint32_t source, uint32_t state);
void perfScreenSlowHit(void);
void perfScreenVictim(uint32_t block, uint32_t oldBlock);
void perfScreenWait(uint32_t polls);
void perfScreenRequest(uint32_t cmd, uint32_t sector, uint32_t count);
void perfScreenLog(void);
void perfScreenSync(void);
void perfScreenWaitBegin(void);
uint32_t perfScreenEnterScope(uint32_t scope);
void perfScreenLeaveScope(uint32_t old);
#ifdef __cplusplus
}
#endif

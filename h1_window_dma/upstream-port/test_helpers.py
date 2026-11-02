"""Compile the actual candidate helper logic with host MMIO/memcpy stubs."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,tempfile
R=Path(__file__).resolve().parent;S=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R
if not (S/'code').is_dir():
 raise SystemExit('Usage: python3 test_helpers.py /path/to/full/source/checkout')
O=Path(tempfile.mkdtemp(prefix='gbr3-h1-host-'))
text=(S/'code/core/arm9/source/SdCache/SdCache.c').read_text()
start=text.index('// H1: bounded maintenance');end=text.index('/// @brief Loads a rom block',start)
helper=text[start:end]
host=helper.replace('[[gnu::section(".ewram"), gnu::noinline]]','')
assert host.count('*(vu32*)0x04000214')==2 and host.count('*(vu32*)0x04000004')==1
host=host.replace('*(vu32*)0x04000214','fakeIf').replace('*(vu32*)0x04000004','fakeScan')
headers='''#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
using u32=uint32_t;using u16=uint16_t;using u8=uint8_t;
#include "GbaDma.h"
#include "Peripherals/DmaTransfer.h"
static constexpr u32 SDC_BLOCK_SIZE=4096;
alignas(4) u8 emu_ioRegisters[0x20c];
dma_state_t dma_state{};
u32 vm_emulatedIfImeIe=0,vm_hwIrqMask=0,fakeScan=0,cpsr=0xd1;
unsigned transfers=0,acks=0,copies=0,bytes=0;
struct FakeIf {u32 value=0;operator u32()const{return value;}
 void operator=(u32 x){if(x!=2)throw std::runtime_error("ack other interrupt");value&=~x;++acks;}} fakeIf;
u32 arm_getCpsr(){return cpsr;}
void dma_dmaTransfer(int c){if(c!=0)throw std::runtime_error("wrong channel");++transfers;dma_state.channels[0].curSrc+=2;}
void mem_copy32(const void*s,void*d,u32 n){if(n!=32&&n!=4096)throw std::runtime_error("copy size");
 ++copies;bytes+=n;std::memcpy(d,s,n);}
'''
tests='''
static void need(bool ok){if(!ok)throw std::runtime_error("test failed");}
static GbaDmaChannel& io(){return *reinterpret_cast<GbaDmaChannel*>(emu_ioRegisters+0xb0);}
static void reset(){std::memset(emu_ioRegisters,0,sizeof emu_ioRegisters);dma_state={};
 io().src=0x02001000;io().dst=0x04000040;io().count=1;io().control=0xa260;
 dma_state.dmaFlags=1;dma_state.channels[0]={io().src,io().dst};
 vm_emulatedIfImeIe=0xa5a50000;vm_hwIrqMask=2;fakeIf.value=0x10003;fakeScan=(40<<16)|2;
 transfers=acks=copies=bytes=0;cpsr=0xd1;}
int main(){unsigned gates=0,polls=0,copyTests=0;
 reset();for(u32 control=0;control<65536;control++){io().control=control;
 need(h1WindowDmaSafe(1,&io(),0x02001000,io().dst)==(control==0xa260));++gates;}
 for(u32 flags=0;flags<4096;flags++){reset();
 need(h1WindowDmaSafe(flags,&io(),0x02001000,io().dst)==((flags&15)==1));++gates;}
 for(u32 src:{0u,1u,0x01fffffeu,0x02000000u,0x02000001u,0x0203fffcu,0x0203fffeu,0x0203ffffu,
   0x02040000u,0x020fc000u,0x02200000u,0x02fffffeu,0x03000000u,0x03000001u,0x03007ffeu,
   0x03007fffu,0x03008000u,0x03fffffeu,0x08000000u,0xffffffffu}){
  reset();bool expected=src%2==0&&((src>=0x02000000&&src<0x02040000)||(src>=0x03000000&&src<0x03008000));
  need(h1WindowDmaSafe(1,&io(),src,io().dst)==expected);++gates;}
 for(u32 dst:{0x04000040u,0x04000042u,0x04000041u,0x04000044u,0x04000048u,0x040000a0u,0x02001000u,0x08000000u}){
  reset();io().dst=dst;need(h1WindowDmaSafe(1,&io(),io().src,dst)==(dst==0x04000040||dst==0x04000042));++gates;
  need(!h1WindowDmaSafe(1,&io(),io().src,dst+2));++gates;}
 for(u32 count:{0u,1u,2u,160u,65535u}){reset();io().count=count;
  need(h1WindowDmaSafe(1,&io(),io().src,io().dst)==(count==1));++gates;}
 for(u32 line=0;line<263;line++)for(unsigned hb=0;hb<2;hb++)for(unsigned mask=0;mask<2;mask++){
  reset();fakeScan=line<<16|(hb?2:0);vm_hwIrqMask=mask?2:0;h1PollWindowDma();
  bool xfer=line<160&&(line!=0||hb),forward=line<160||(line>=192&&line<260);
  need(acks==1&&fakeIf.value==0x10001&&transfers==unsigned(xfer));
  need(dma_state.channels[0].curSrc==io().src+(xfer?2:0));
  need(vm_emulatedIfImeIe==(0xa5a50000|(forward&&mask?2:0)));need(cpsr==0xd1);++polls;}
 reset();fakeIf.value=0x10001;h1PollWindowDma();need(!acks&&!transfers&&fakeIf.value==0x10001);++polls;
 reset();io().control^=0x4000;h1PollWindowDma();need(!acks&&!transfers&&fakeIf.value==0x10003);++polls;
 u8 src[4096],dst[4096];for(unsigned i=0;i<4096;i++)src[i]=u8((i*13)^0xa5);
 for(unsigned variant=0;variant<5;variant++){reset();fakeIf.value=0;std::memset(dst,0,sizeof dst);bool inBounds=true;
  if(variant==1)inBounds=false;if(variant==2)cpsr=0x92;if(variant==3)cpsr=0x11;if(variant==4)io().control=0;
  auto old=cpsr;h1CopyCartBlock(src,dst,inBounds);need(std::memcmp(src,dst,4096)==0&&bytes==4096&&cpsr==old);
  need(copies==(variant==0?128u:1u));++copyTests;}
 std::cout<<"{\\"pass\\":true,\\"gate_cases\\":"<<gates<<",\\"poll_cases\\":"<<polls
 <<",\\"copy_cases\\":"<<copyTests<<",\\"cpu_irq_unmasking\\":false,\\"scope\\":\\"actual helper C logic with host MMIO/memcpy stubs\\"}\\n";
}
'''
(O/'host_helpers.cpp').write_text(headers+host+tests)
cmd=['clang++','-std=c++17','-O2','-I'+str(S/'code/core/common'),'-I'+str(S/'code/core/arm9/source'),
 str(O/'host_helpers.cpp'),'-o',str(O/'host_helpers')]
p=subprocess.run(cmd,text=True,capture_output=True);(O/'host_build.log').write_text(p.stdout+p.stderr)
assert p.returncode==0,p.stderr[-2500:]
p=subprocess.run([str(O/'host_helpers')],text=True,capture_output=True);(O/'host_stderr.log').write_text(p.stderr)
assert p.returncode==0,p.stderr
j=json.loads(p.stdout);j['tested_helper_sha256']=hashlib.sha256(helper.encode()).hexdigest()
(O/'host_tests.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j,indent=2))

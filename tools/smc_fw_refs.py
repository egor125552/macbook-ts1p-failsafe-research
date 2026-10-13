from pathlib import Path
import sys, struct
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_REG, ARM64_OP_MEM
b=Path(__import__('os').environ.get('SMC_FW','smc-firmware.bin')).read_bytes()
m=Cs(CS_ARCH_ARM64, CS_MODE_ARM);m.detail=True;m.skipdata=True
lo,hi=map(lambda s:int(s,0),sys.argv[1:3]);regs={}
for i in m.disasm(b[:0x69000],0):
 if i.id==0: continue
 o=i.operands;v=None
 if i.mnemonic in ('adr','adrp'):v=o[1].imm
 elif i.mnemonic=='add' and len(o)==3 and o[2].type==ARM64_OP_IMM:
  if o[1].reg in regs:v=regs[o[1].reg]+(o[2].imm<<o[2].shift.value)
 elif i.mnemonic=='mov' and len(o)==2:
  if o[1].type==ARM64_OP_REG:v=regs.get(o[1].reg)
  elif o[1].type==ARM64_OP_IMM:v=o[1].imm
 if v is not None:
  regs[o[0].reg]=v
  if lo<=v<hi:print(f'{i.address:#08x} {i.mnemonic} {i.op_str} => {v:#x}')
 elif i.mnemonic.startswith(('ldr','ldur','str','stur','ldp','stp')):
  mem=o[-1]
  if mem.type==ARM64_OP_MEM and mem.mem.base in regs and not mem.mem.index:
   a=regs[mem.mem.base]+mem.mem.disp
   if lo<=a<hi:print(f'{i.address:#08x} {i.mnemonic} {i.op_str} @ {a:#x}')
  if i.mnemonic.startswith(('ldr','ldur','ldp')):
   for z in o[:-1]:regs.pop(z.reg,None)
 elif i.mnemonic=='bl':
  for n in range(19):regs.pop(m.reg_name(0),None) if False else None
  # Do not infer unknown effects of outlined helpers. Keep only register constants.
 elif o and o[0].type==ARM64_OP_REG and i.mnemonic not in ('cmp','tst','fcmp'):
  regs.pop(o[0].reg,None)
for p in range(0x69000,len(b)-7,4):
 v=struct.unpack_from('<Q',b,p)[0]
 if lo<=v<hi:print(f'DATA {p:#x} => {v:#x}')

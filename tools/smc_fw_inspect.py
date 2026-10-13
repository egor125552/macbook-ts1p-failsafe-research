from pathlib import Path
import struct,sys
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM,ARM64_OP_REG,ARM64_OP_MEM

B=Path(__import__('os').environ.get('SMC_FW','smc-firmware.bin')).read_bytes()
MD=Cs(CS_ARCH_ARM64,CS_MODE_ARM);MD.detail=True;MD.skipdata=True
INS=list(MD.disasm(B[:0x69000],0))
BY={x.address:x for x in INS}

def show(a,e):
    for x in INS:
        if a<=x.address<e:print(f'{x.address:#08x} {x.mnemonic:8} {x.op_str}')

mode=sys.argv[1]
if mode=='range':show(int(sys.argv[2],0),int(sys.argv[3],0))
elif mode=='imm':
    targets={int(v,0) for v in sys.argv[2:]}
    for i,x in enumerate(INS):
        if x.mnemonic.startswith('mov') and any(o.type==ARM64_OP_IMM and o.imm in targets for o in x.operands):
            show(max(0,x.address-12),x.address+20)
elif mode=='calls':
    targets={int(v,0) for v in sys.argv[2:]}
    for i,x in enumerate(INS):
        if x.mnemonic in ('bl','b') and any(o.type==ARM64_OP_IMM and o.imm in targets for o in x.operands):
            show(max(0,x.address-28),x.address+8)
elif mode=='strings':
    for query in sys.argv[2:]:
        q=query.encode();p=0
        while True:
            p=B.find(q,p)
            if p<0:break
            e=B.find(b'\0',p);print(hex(p),B[p:e].decode(errors='replace'));p+=len(q)
elif mode=='stores':
    targets={int(v,0) for v in sys.argv[2:]};regs={}
    for x in INS:
        if x.id==0:continue
        ops=x.operands
        if x.mnemonic in ('adrp','adr') and len(ops)==2:
            regs[ops[0].reg]=ops[1].imm
        elif x.mnemonic=='add' and len(ops)==3 and ops[2].type==ARM64_OP_IMM:
            a=regs.get(ops[1].reg)
            if a is not None:regs[ops[0].reg]=a+(ops[2].imm << ops[2].shift.value)
            else:regs.pop(ops[0].reg,None)
        elif x.mnemonic.startswith('str') and len(ops)==2 and ops[1].type==ARM64_OP_MEM:
            a=regs.get(ops[1].mem.base)
            if a is not None and a+ops[1].mem.disp in targets:
                print('STORE TO',hex(a+ops[1].mem.disp));show(max(0,x.address-32),x.address+12)
        elif x.mnemonic=='mov' and len(ops)==2:
            if ops[1].type==ARM64_OP_IMM:regs[ops[0].reg]=ops[1].imm
            elif ops[1].reg in regs:regs[ops[0].reg]=regs[ops[1].reg]
            else:regs.pop(ops[0].reg,None)
        elif x.mnemonic.startswith('ldr') and len(ops)>=2:
            regs.pop(ops[0].reg,None)
elif mode=='dump':show(0,0x69000)

import os, re, struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

B = Path(os.environ.get('THERMALMONITORD','thermalmonitord')).read_bytes()
BASE = 0x100000000
SECS = []
pos = 32
for _ in range(struct.unpack_from('<I', B, 16)[0]):
    cmd, size = struct.unpack_from('<II', B, pos)
    if cmd == 0x19:
        for j in range(struct.unpack_from('<I', B, pos+64)[0]):
            q = pos+72+j*80
            name = B[q:q+16].split(b'\0')[0].decode()
            addr, length, off = struct.unpack_from('<QQI', B, q+32)
            SECS.append((addr, length, off, name))
    pos += size

def off(addr):
    for a, n, f, name in SECS:
        if a <= addr < a+n: return f+addr-a
    raise ValueError(hex(addr))

def u64(addr): return struct.unpack_from('<Q', B, off(addr))[0]
def ptr(addr): return BASE+(u64(addr)&0xffffffff)
def cs(addr):
    o = off(addr)
    return B[o:B.find(b'\0', o)].decode('utf8', 'replace')
def cf(addr): return cs(ptr(addr+16))

MD = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
MD.skipdata = True
textsec = next(x for x in SECS if x[3]=='__text')
INS = list(MD.disasm(B[textsec[2]:textsec[2]+textsec[1]], textsec[0]))
BY = {x.address:x for x in INS}
STUBS = {}
ss = next(x for x in SECS if x[3]=='__objc_stubs')
for a in range(ss[0], ss[0]+ss[1], 32):
    ins = list(MD.disasm(B[off(a):off(a)+8], a))
    try:
        page = int(ins[0].op_str.split('#')[1], 0)
        delta = int(ins[1].op_str.split('#')[1].rstrip(']'), 0)
        STUBS[a] = cs(ptr(page+delta))
    except (ValueError, IndexError): pass

METHODS = {}
cache = Path(os.environ.get('THERMAL_OBJC','thermal_objc.txt')).read_text()
for m in re.finditer(r'name\s+0x[0-9a-f]+ \((0x[0-9a-f]+)\)\s+types[^\n]*\n\s+imp\s+0x[0-9a-f]+ \((0x[0-9a-f]+)\)', cache):
    try: METHODS[int(m[2],16)] = cs(ptr(int(m[1],16)))
    except ValueError: pass

def show(start, end):
    for x in INS:
        if start <= x.address < end:
            note=''
            if x.mnemonic in ('bl','b'):
                dest=int(x.op_str.lstrip('#'),16)
                note=STUBS.get(dest, METHODS.get(dest,''))
            print(f'{x.address:#x} {x.mnemonic:8} {x.op_str:42} {note}')

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='range': show(int(sys.argv[2],0), int(sys.argv[3],0))
    elif mode=='xref':
        wanted=set(sys.argv[2:])
        for i,x in enumerate(INS):
            if x.mnemonic not in ('bl','b'): continue
            name=STUBS.get(int(x.op_str.lstrip('#'),16),'')
            if name in wanted:
                owners=[a for a in METHODS if a<=x.address]
                owner=max(owners) if owners else 0
                print('OWNER',hex(owner),METHODS.get(owner,''),'CALL',hex(x.address),name)
                show(max(textsec[0],x.address-32), x.address+12)
    elif mode=='data':
        for arg in sys.argv[2:]:
            a=int(arg,0)
            try: print(arg, 'ptr',hex(ptr(a)),cs(ptr(a)))
            except ValueError:
                try: print(arg, 'cf',cf(a))
                except ValueError: print(arg, 'raw',B[off(a):off(a)+32].hex())
    elif mode=='methods':
        for a,n in sorted(METHODS.items()):
            if any(s.lower() in n.lower() for s in sys.argv[2:]): print(hex(a),n)

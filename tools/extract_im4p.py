import ctypes, struct, sys
from pathlib import Path

def tlv(b,p):
    tag=b[p];v=b[p+1];p+=2
    if v&128:
        n=v&127;v=int.from_bytes(b[p:p+n],'big');p+=n
    if p+v>len(b):raise ValueError('truncated DER')
    return tag,p,p+v

def extract(path, dest):
    b=Path(path).read_bytes();tag,start,end=tlv(b,0);fields=[];p=start
    while p<end:
        tag,s,e=tlv(b,p);fields.append((tag,b[s:e]));p=e
    print('fields',[(hex(t),len(v),v[:32]) for t,v in fields])
    payload=next(v for t,v in fields if t==4)
    if payload.startswith((b'bvx2',b'bvxn')):
        lib=ctypes.CDLL('/usr/lib/libcompression.dylib')
        lib.compression_decode_buffer.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_int]
        lib.compression_decode_buffer.restype=ctypes.c_size_t
        size=32*1024*1024;out=ctypes.create_string_buffer(size)
        n=lib.compression_decode_buffer(out,size,payload,len(payload),None,0x801)
        if not n:raise ValueError('LZFSE decode failed')
        payload=out.raw[:n]
    Path(dest).write_bytes(payload)
    print('saved',dest,len(payload),'magic',payload[:32].hex())

if __name__=='__main__':extract(sys.argv[1],sys.argv[2])

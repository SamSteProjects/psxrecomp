"""Isolated instruction oracle for two immutable retail ME routines only.

No BIOS, overlays, devices, game loop, process attachment or native compilation.
All code/memory access and instruction steps are bounded and fail closed.
"""
import struct
from hashlib import sha256
from importer.actor_runtime_capacity import EXECUTABLE_SHA256

SPANS = ((0x8002A9CC, 2240, '4846568647c9d13fdf55938ca4832679c2674dc611898267ccac55fe8da42acd'),
         (0x8002B28C, 328, '708ff5d29efa7afa0ae55a29ee44cda7c07e9842aa881b46e3c13b4ee69130ef'))
MASK = 0xffffffff
signed = lambda n: n - 0x100000000 if n & 0x80000000 else n


def qualified_code(executable):
    if executable[:8] != b'PS-X EXE' or sha256(executable).hexdigest() != EXECUTABLE_SHA256:
        raise ValueError('Consumer oracle requires the exact retail executable')
    base, size = struct.unpack_from('<II', executable, 0x18)
    result = {}
    for address, length, digest in SPANS:
        offset = address - base
        if not 0 <= offset <= size - length: raise ValueError('Consumer span exceeds load image')
        raw = executable[2048+offset:2048+offset+length]
        if sha256(raw).hexdigest() != digest: raise ValueError('Consumer instruction witness changed')
        result.update((address+i*4, word) for i, (word,) in enumerate(struct.iter_unpack('<I', raw)))
    return result


class Machine:
    def __init__(self, code, regions):
        self.code = code; self.regions = regions; self.r = [0]*32
        self.pc = 0; self.next = 0; self.load = None; self.steps = 0
        self.hi = self.lo = 0
        self.writes = {}; self.reads = {}; self.visited = set(); self.operations = set()

    def memory(self, address, size, write=None):
        if size not in (1,2,4) or address % size: raise ValueError('Unaligned or unsupported consumer memory access')
        for start, data, writable, label in self.regions:
            if start <= address and address+size <= start+len(data):
                at = address-start
                if write is None:
                    for i in range(size): self.reads.setdefault(label,set()).add(at+i)
                    return int.from_bytes(data[at:at+size], 'little')
                if not writable: raise ValueError('Consumer tried to write immutable source')
                data[at:at+size] = (write & ((1 << (size*8))-1)).to_bytes(size, 'little')
                for i in range(size): self.writes.setdefault(label,set()).add(at+i)
                return
        raise ValueError(f'Consumer access escapes isolated buffers: {address:08X}/{size}')

    def step(self):
        word = self.code.get(self.pc)
        if word is None: raise ValueError(f'Consumer execution escapes qualified instructions: {self.pc:08X}')
        self.visited.add(self.pc);self.steps += 1
        op, rs, rt, rd, sa, fn = word>>26, (word>>21)&31, (word>>16)&31, (word>>11)&31, (word>>6)&31, word&63
        imm = word & 65535; si = imm-65536 if imm&32768 else imm
        a,b = self.r[rs],self.r[rt]; pending=self.load; self.load=None
        sequential=self.next; target=(self.next+4)&MASK; assigned=set()
        def put(reg,value):
            if reg: self.r[reg]=value&MASK;assigned.add(reg)
        def branch(take):
            nonlocal target
            if take: target=(self.pc+4+si*4)&MASK
        self.operations.add((op,fn if op==0 else None))
        if op==0:
            if fn==0: put(rd,b<<sa)
            elif fn==2: put(rd,b>>sa)
            elif fn==3: put(rd,signed(b)>>sa)
            elif fn==4: put(rd,b<<(a&31))
            elif fn==6: put(rd,b>>(a&31))
            elif fn==7: put(rd,signed(b)>>(a&31))
            elif fn==8: target=a
            elif fn==9: put(rd,self.pc+8);target=a
            elif fn==0x10: put(rd,self.hi)
            elif fn==0x12: put(rd,self.lo)
            elif fn in (0x18,0x19):
                product=(signed(a)*signed(b) if fn==0x18 else a*b)&0xffffffffffffffff
                self.hi=product>>32;self.lo=product&MASK
            elif fn in (0x20,0x21): put(rd,a+b)
            elif fn in (0x22,0x23): put(rd,a-b)
            elif fn==0x24: put(rd,a&b)
            elif fn==0x25: put(rd,a|b)
            elif fn==0x26: put(rd,a^b)
            elif fn==0x27: put(rd,~(a|b))
            elif fn==0x2a: put(rd,int(signed(a)<signed(b)))
            elif fn==0x2b: put(rd,int(a<b))
            else: raise ValueError(f'Unsupported consumer SPECIAL: {fn:X}')
        elif op in (2,3):
            target=((self.pc+4)&0xf0000000)|((word&0x3ffffff)<<2)
            if op==3: put(31,self.pc+8)
        elif op==4: branch(a==b)
        elif op==5: branch(a!=b)
        elif op==6: branch(signed(a)<=0)
        elif op==7: branch(signed(a)>0)
        elif op in (8,9): put(rt,a+si)
        elif op==10: put(rt,int(signed(a)<si))
        elif op==11: put(rt,int(a<(si&MASK)))
        elif op==12: put(rt,a&imm)
        elif op==13: put(rt,a|imm)
        elif op==14: put(rt,a^imm)
        elif op==15: put(rt,imm<<16)
        elif op in (0x20,0x21,0x23,0x24,0x25):
            size={0x20:1,0x21:2,0x23:4,0x24:1,0x25:2}[op];value=self.memory((a+si)&MASK,size)
            if op in (0x20,0x21) and value&(1<<(size*8-1)):value-=1<<(size*8)
            self.load=(rt,value&MASK)
        elif op in (0x28,0x29,0x2b): self.memory((a+si)&MASK,{0x28:1,0x29:2,0x2b:4}[op],b)
        else: raise ValueError(f'Unsupported consumer opcode: {op:X}')
        if pending and pending[0] and pending[0] not in assigned:self.r[pending[0]]=pending[1]
        self.r[0]=0;self.pc=sequential;self.next=target

    def run(self,entry,stop,limit=2000000):
        self.pc=entry;self.next=entry+4
        while self.pc!=stop:
            if self.steps>=limit: raise ValueError('Consumer instruction step budget exceeded')
            self.step()
        return self.r[2]


def consume(code, source, decoded_size, index=None, scratch_seed=0):
    src,dst,stack,stop=0x10000000,0x10020000,0x10090000,0x7fffff00
    if not isinstance(source,bytes) or not 1<=len(source)<=0x10800 or type(decoded_size) is not int or not 2<=decoded_size<=146882 or type(scratch_seed) is not int or not 0<=scratch_seed<=255:
        raise ValueError('Consumer input/output budget or scratch seed is invalid')
    output=bytearray([0xcd])*decoded_size;scratch=bytearray([scratch_seed])*1024;stack_bytes=bytearray(4096)
    m=Machine(code,[(src,bytearray(source),False,'source'),(dst,output,True,'output'),(0x1f800000,scratch,True,'scratch'),(stack-4096,stack_bytes,True,'stack')])
    m.r[29]=stack;m.r[31]=stop
    if index is None:m.r[4]=dst;m.r[5]=src;entry=0x8002a9cc
    else:m.r[4]=src;m.r[5]=dst;m.r[6]=index;entry=0x8002b28c
    returned=m.run(entry,stop,decoded_size*256+20000)
    return bytes(output),dict(returned=returned,steps=m.steps,output_written=len(m.writes.get('output',())),source_reads=sorted(m.reads.get('source',())),scratch_highest=max(m.writes.get('scratch',[-1])),visited=sorted(m.visited))

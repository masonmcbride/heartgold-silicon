"""Finite, source-checked MI ARM instruction translation for guest RAM. MIT.

This is a build adaptation of one fixed input, not a runtime ARM interpreter.
Unknown instructions fail. Registers remain uint32_t; memory uses checked spans.
"""
import hashlib
import re

FUNCTIONS={
    'MIi_CpuClear16':['uint16_t','uint32_t','uint32_t'],
    'MIi_CpuClear32':['uint32_t']*3,
    'MIi_CpuClearFast':['uint32_t']*3,
    'MIi_CpuCopy16':['uint32_t']*3,
    'MIi_CpuCopy32':['uint32_t']*3,
    'MI_CpuFill8':['uint32_t','uint8_t','uint32_t'],
    'MI_CpuCopy8':['uint32_t']*3,
}


def translate(text,source):
    if source.name!='mi_memory.c' or hashlib.sha256(text.encode()).hexdigest()!='7bfc34240ca43ec5c45773a7dad14547b0bb38fe7638c055a0f735e0aa0eb592':
        raise ValueError('original MI source changed')
    output=['/* Direct original MI instruction translation. Generated; MIT. */', '#include "guest32_mi.h"']
    for name,types in FUNCTIONS.items():
        body=re.search(r'asm void '+name+r'\([^\n]*\) \{\n(.*?)\n\}',text,re.S)
        if not body:raise ValueError('original MI function missing: '+name)
        output.append('void guest32_'+name+'(void *ram,'+','.join(t+' a'+str(i) for i,t in enumerate(types))+'){')
        output.append('uint32_t '+','.join('r'+str(i)+'='+('a'+str(i) if i<3 else '0') for i in range(13))+';')
        output.append('int zero=0,carry=0,less=0; (void)zero;(void)carry;(void)less;')
        def value(s):
            s=s.strip()
            if re.fullmatch(r'r(?:[0-9]|1[0-2])',s):return s
            if re.fullmatch(r'#(?:0x[0-9a-f]+|[0-9]+)',s):return s[1:]+'u'
            raise ValueError('unsupported MI operand: '+s)
        def operand(parts):
            if len(parts)==1:return value(parts[0])
            if len(parts)!=2:raise ValueError('MI shifted operand')
            m=re.fullmatch(r'(lsl|lsr) #(0x[0-9a-f]+|[0-9]+)',parts[1])
            if not m or not 0<int(m[2],0)<32:raise ValueError('MI shift')
            return '('+value(parts[0])+(' << ' if m[1]=='lsl' else ' >> ')+m[2]+')'
        for raw in body[1].splitlines():
            line=raw.strip()
            if not line:continue
            if line.startswith('@') and line.endswith(':'):
                output.append(line[1:]);continue
            op,_,args=line.partition(' ')
            if op in ('b','beq','bne','bcc','bcs','blt'):
                if not re.fullmatch(r'@L[0-9A-F]+',args):raise ValueError('MI branch target')
                condition={'b':'1','beq':'zero','bne':'!zero','bcc':'!carry','bcs':'carry','blt':'less'}[op]
                statement='if('+condition+')goto '+args[1:]+';'
            elif op=='bx' and args=='lr':statement='return;'
            elif (op,args) in [('stmdb','sp!, {r4, r5, r6, r7, r8, r9}'),('ldmia','sp!, {r4, r5, r6, r7, r8, r9}')]:
                statement='/* Native C ABI preserves the original callee-saved registers. */'
            elif op in ('ldmia','stmia'):
                m=re.fullmatch(r'(r\d+)!, \{(r\d+(?:, r\d+)*)\}',args)
                if not m:raise ValueError('MI multiple transfer')
                base,registers=m[1],m[2].split(', ')
                if base in registers:raise ValueError('MI transfer base in list')
                statements=[]
                for i,reg in enumerate(registers):
                    address=base+'+'+str(4*i)+'u'
                    statements.append(reg+'=g32_mi_read(ram,'+address+',4);' if op=='ldmia' else 'g32_mi_write(ram,'+address+','+reg+',4);')
                statement=''.join(statements)+base+'+='+str(4*len(registers))+'u;'
            elif op in ('ldr','ldrh','str','strh'):
                m=re.fullmatch(r'(r\d+), \[(r\d+)(?:, (#[^-\]]+|#-\d+|r\d+))?\](?:, #(\d+))?',args)
                if not m:raise ValueError('MI memory operand: '+line)
                reg,base,offset,post=m.groups();address=base
                if offset:address+='-'+offset[2:]+'u' if offset.startswith('#-') else '+'+value(offset)
                width=2 if op.endswith('h') else 4
                statement=reg+'=g32_mi_read(ram,'+address+','+str(width)+');' if op.startswith('ldr') else 'g32_mi_write(ram,'+address+','+reg+','+str(width)+');'
                if post:statement+=base+'+='+post+'u;'
            else:
                parts=args.split(', ')
                if op=='cmp':
                    if len(parts)!=2:raise ValueError('MI compare')
                    x,y=map(value,parts)
                    statement='zero=('+x+'=='+y+');carry=('+x+'>='+y+');less=((int32_t)'+x+'<(int32_t)'+y+');'
                elif op=='tst':statement='zero=(('+value(parts[0])+'&'+operand(parts[1:])+')==0);'
                elif op=='mov':statement=value(parts[0])+'='+operand(parts[1:])+';'
                elif op in ('add','sub','subs','and','orr','eor','bic','bics'):
                    dest,x=value(parts[0]),value(parts[1]);y=operand(parts[2:])
                    symbol={'add':'+','sub':'-','subs':'-','and':'&','orr':'|','eor':'^','bic':'&~','bics':'&~'}[op]
                    statement=('carry=('+x+'>=('+y+'));' if op=='subs' else '')+dest+'='+x+symbol+'('+y+');'
                    if op in ('subs','bics'):statement+='zero=('+dest+'==0);'
                else:raise ValueError('unsupported original MI instruction: '+line)
            output.append(statement+' /* '+line.replace('*/','')+' */')
        output.append('}')
    return '\n'.join(output)+'\n'


def main():
    import argparse
    import json
    from pathlib import Path
    from native_overlay_link import symbols
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--nm',required=True)
    a=p.parse_args();original=a.source.read_text();translate(original,a.source)
    archive=a.archive.resolve();actual=symbols(archive,nm=a.nm)
    identities={'_guest32_'+n:n for n in FUNCTIONS}
    if actual!=identities.keys():raise ValueError('MI emitted provider inventory changed')
    member='lib/NitroSDK/src/mi/mi_memory.o'
    family=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        original_members={member:hashlib.sha256(original.encode()).hexdigest()},symbols={s:member for s in actual},
        original_identities=identities,abi_representation='guest32',
        signature_validation='original register widths; checked instruction memory spans',
        scope='seven original ARM routines translated instruction by instruction; not a complete replacement SDK object')
    a.out.write_text(json.dumps(dict(schema=1,families={'MI_memory':family}),indent=2)+'\n')

if __name__=='__main__':main()

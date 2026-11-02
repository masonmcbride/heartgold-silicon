"""Read actual Mach-O fixups and generate checks of dyld's resolved pointer slots."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import struct


def bindings(path, providers):
    data=path.read_bytes()
    header=struct.unpack_from('<8I',data)
    if header[:2]!=(0xfeedfacf,0x0100000c) or header[3]!=6:
        raise ValueError('Expected actual ARM64 dylib')
    if not header[6] & 0x80 or header[6] & 0x100:
        raise ValueError('Image does not use two-level namespace')
    cursor=32; ranges=[]; preferred=None
    dependencies=[]; identity=None
    for _ in range(header[4]):
        command,size=struct.unpack_from('<II',data,cursor)
        if command==0x19:
            name,address,length=struct.unpack_from('<16sQQ',data,cursor+8)
            if name.rstrip(b'\0')==b'__TEXT': preferred=address
            ranges.append((address,length))
        if command in (0xc,0xd,0x80000018,0x8000001f,0x80000023):
            offset=struct.unpack_from('<I',data,cursor+8)[0]
            name=data[cursor+offset:cursor+size].split(b'\0',1)[0].decode()
            if command==0xd: identity=name
            else: dependencies.append(name)
        cursor+=size
    expected_identity='@rpath/'+path.name
    if identity != expected_identity:
        raise ValueError('Incorrect native install name: '+str(identity))
    allowed={'@executable_path/heartgold','/usr/lib/libSystem.B.dylib'}
    allowed.update(f'@rpath/libheartgold_image_{i}.dylib' for i in providers.values() if i>=0)
    if set(dependencies)-allowed:
        raise ValueError('Unverified runtime dependencies: '+str(set(dependencies)-allowed))
    if preferred!=0: raise ValueError('Binding checks require zero preferred TEXT address')
    report = subprocess.run(['xcrun','dyld_info','-fixups',str(path)],
                            text=True,capture_output=True,check=True).stdout
    rows=[]
    for line in report.splitlines():
        if not re.search(r'\sbind\s',line): continue
        match=re.fullmatch(r'\s*\S+\s+\S+\s+(0x[0-9A-Fa-f]+)\s+bind\s+(\S+?)/(_\S+?)(?:\s*\+\s*(0x[0-9A-Fa-f]+|\d+))?\s*',line)
        if not match: raise ValueError('Unreviewed Mach-O binding: '+line)
        address,library,symbol,addend=match.groups()
        if not any(base<=int(address,16) and int(address,16)+8<=base+length for base,length in ranges):
            raise ValueError('Binding slot outside mapped image: '+line)
        if library=='libSystem': provider=-2
        elif symbol in providers:
            provider=providers[symbol]
            expected='heartgold' if provider == -1 else f'libheartgold_image_{provider}'
            if library != expected:
                raise ValueError('Incorrect two-level provider (expected '+expected+'): '+line)
        else: raise ValueError('No unique emitted owner for actual binding: '+line)
        rows.append(dict(offset=int(address,16),symbol=symbol,provider=provider,addend=int(addend or '0',0)))
    from native_overlay_link import symbols
    if symbols(path,undefined=True) != {row['symbol'] for row in rows}:
        raise ValueError('Imports without verified binding slots: '+str(path))
    return rows


def generate(images, providers, output, report):
    result={ident:bindings(path,providers) for ident,path in images.items()}
    text='/* Generated from actual ARM64 Mach-O fixups; checked after dyld binding, before FS activation. */\n'
    for ident,rows in sorted(result.items()):
        for row in rows:
            text += 'HG_NATIVE_BINDING(%d, 0x%x, %s, %d, 0x%x)\n' % (ident,row['offset'],json.dumps(row['symbol'][1:]),row['provider'],row['addend'])
    if not output.exists() or output.read_text()!=text: output.write_text(text)
    report.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contracts',type=Path,required=True)
    p.add_argument('--image',action='append',required=True,help='Original numeric ID=actual dylib path')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    images={}
    for item in a.image:
        ident,path=item.split('=',1)
        if int(ident) in images: raise ValueError('Duplicate image ID')
        images[int(ident)]=Path(path)
    generate(images,json.loads(a.contracts.read_text()),a.output,a.report)

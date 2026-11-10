"""Read actual Mach-O fixups and generate checks of dyld's resolved pointer slots."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import struct



NATIVE_SUPPORT_PROVIDERS = {
    "libheartgold_dwc_status": -3,
    "libheartgold_wm_arm9": -4,
    "libheartgold_ovy0_wifi_subset": -5,
    "libc++": -6,
}

_native_support_exports = {}

def verified_native_support(path, library, symbol):
    import subprocess

    if library not in NATIVE_SUPPORT_PROVIDERS:
        raise ValueError("Unknown support provider: " + library)

    if library == "libc++":
        import ctypes
        dylib = ctypes.CDLL("/usr/lib/libc++.1.dylib")
        try:
            getattr(dylib, symbol[1:])
        except AttributeError:
            raise ValueError("libc++ does not export " + symbol)
        return NATIVE_SUPPORT_PROVIDERS[library]

    dylib = path.parent / (library + ".dylib")
    if not dylib.is_file():
        raise ValueError("Missing support dylib: " + str(dylib))

    if dylib not in _native_support_exports:
        result = subprocess.run(
            ["nm", "-gU", str(dylib)],
            text=True, capture_output=True, check=True
        )
        _native_support_exports[dylib] = {
            fields[-1]
            for line in result.stdout.splitlines()
            if (fields := line.split())
            and len(fields) >= 3
            and fields[-2] != "U"
        }

    if symbol not in _native_support_exports[dylib]:
        raise ValueError(
            "Support library does not export " + symbol
            + ": " + str(dylib)
        )

    return NATIVE_SUPPORT_PROVIDERS[library]



_weak_definition_cache = {}

def weak_overlay_owners(directory):
    """Actual exported definitions in the completed native images."""
    directory = directory.resolve()
    if directory not in _weak_definition_cache:
        from collections import defaultdict
        import subprocess

        owners = defaultdict(set)
        for image in sorted(directory.glob("libheartgold_image_*.dylib")):
            result = subprocess.run(
                ["nm", "-g", "-P", str(image)],
                text=True, capture_output=True, check=True
            )
            for line in result.stdout.splitlines():
                fields = line.split()
                if len(fields) >= 2 and fields[1].upper() != "U":
                    owners[fields[0]].add(image.name)
        _weak_definition_cache[directory] = owners

    return _weak_definition_cache[directory]


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
    if set(dependencies) - (allowed | {'@rpath/libheartgold_dwc_status.dylib', '@rpath/libheartgold_wm_arm9.dylib', '@rpath/libheartgold_ovy0_wifi_subset.dylib', '/usr/lib/libc++.1.dylib'}):
        raise ValueError('Unverified runtime dependencies: '+str(set(dependencies)-allowed))
    if preferred!=0: raise ValueError('Binding checks require zero preferred TEXT address')
    report = subprocess.run(['xcrun','dyld_info','-fixups',str(path)],
                            text=True,capture_output=True,check=True).stdout
    rows=[]
    local_weak_symbols=set()
    for line in report.splitlines():
        if not re.search(r'\sbind\s',line): continue
        match=re.fullmatch(r'\s*\S+\s+\S+\s+(0x[0-9A-Fa-f]+)\s+bind\s+(\S+?)/(_\S+?)(?:\s*\+\s*(0x[0-9A-Fa-f]+|\d+))?\s*',line)
        if not match: raise ValueError('Unreviewed Mach-O binding: '+line)
        address,library,symbol,addend=match.groups()
        if not any(base<=int(address,16) and int(address,16)+8<=base+length for base,length in ranges):
            raise ValueError('Binding slot outside mapped image: '+line)
        if library=='libSystem': provider=-2
        elif library in NATIVE_SUPPORT_PROVIDERS:
            provider=verified_native_support(path,library,symbol)
        elif library=='<weak-def-coalesce>':
            match_id = re.fullmatch(
                r'libheartgold_image_([0-9]+)\.dylib', path.name
            )
            if not match_id:
                raise ValueError("Unknown weak-binding importer: "+str(path))

            owners = weak_overlay_owners(path.parent).get(symbol,set())

            if owners == {path.name}:
                # Mach-O emitted a weak-coalescing fixup for a
                # genuine definition in this original overlay image.
                provider=int(match_id.group(1))
                local_weak_symbols.add(symbol)
            elif not owners:
                # An external C++ weak import must resolve to the
                # verified Apple C++ runtime, never an invented owner.
                provider=verified_native_support(path,"libc++",symbol)
            else:
                raise ValueError(
                    "Ambiguous weak binding owner for "+symbol+
                    ": "+str(sorted(owners))
                )
        elif symbol in providers:
            provider=providers[symbol]
            expected='heartgold' if provider == -1 else f'libheartgold_image_{provider}'
            if library != expected:
                raise ValueError('Incorrect two-level provider (expected '+expected+'): '+line)
        else: raise ValueError('No unique emitted owner for actual binding: '+line)
        rows.append(dict(offset=int(address,16),symbol=symbol,provider=provider,addend=int(addend or '0',0)))
    from native_overlay_link import symbols
    # Local weak definitions may have dyld binding slots without
    # being Mach-O undefined symbols. All actual undefined imports
    # must still correspond exactly to verified binding slots.
    verified_imports = {row['symbol'] for row in rows}
    if symbols(path,undefined=True) != verified_imports - local_weak_symbols:
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

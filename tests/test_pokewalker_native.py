"""Compile real generated consumers and validate native storage/hardware contracts."""
import argparse
import json
from pathlib import Path
import shlex
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def compiler_flags(entries, suffix):
    entry = next(e for e in entries if e['file'].endswith(suffix))
    args = shlex.split(entry['command'])[1:]
    result = []
    i = 0
    while i < len(args):
        if args[i] == '-o': i += 2; continue
        if args[i] in ('-c', entry['file']): i += 1; continue
        result.append(args[i]); i += 1
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--compiler',default='clang')
    args = parser.parse_args()
    build = args.build.resolve()
    work = build/'pokewalker-native-test'
    work.mkdir(parents=True,exist_ok=True)
    entries = json.loads((build/'compile_commands.json').read_text())
    flags = ['-UNDEBUG','-O1','-g','-fsanitize=address,undefined',
             '-Werror=pointer-to-int-cast','-Werror=int-to-pointer-cast','-Werror=void-pointer-to-int-cast',
             '-Werror=incompatible-pointer-types']
    # Include the actual generated storage owner and the exact adapted original
    # BeginTransfer body. Other IR functions require real OS/hardware subsystems
    # and are exercised by the image link, not replaced in this test executable.
    source = (build/'native/src/application/pokewalker/pokewalker_ir.c').read_text()
    subprocess.run([args.compiler]+compiler_flags(entries,'/pokewalker_ir.c')+flags+
                   ['-fsyntax-only',str(build/'native/src/application/pokewalker/pokewalker_ir.c')],
                   check=True,capture_output=True,text=True)
    start = source.index('void PokewalkerIr_BeginTransfer(')
    end = source.index('\n}',start) + 2
    harness = work/'storage.c'
    owner = build/'native/src/application/pokewalker/pokewalker_ir_requests.c'
    harness.write_text('#include "'+str(owner)+'"\n'+source[start:end]+'\n#include "'+str(ROOT/'tests/pokewalker_native_abi.c')+'"\n')
    executable = work/'storage'
    subprocess.run([args.compiler]+compiler_flags(entries,'/pokewalker_ir_requests.c')+
                   flags+[str(harness),'-o',str(executable)],check=True,capture_output=True,text=True)
    subprocess.run([str(executable)],check=True)
    card_sources = [build/'native/lib/NitroSDK/src/card'/f'{name}.c'
                    for name in ('card_spi_wait','card_spi_wait_cycles','card_spi_wait_init')]
    card_sources += [build/'native/lib/asm/card_spi_storage.c',
                     ROOT/'hardware_drivers/os/card_spi_host.c',ROOT/'tests/card_spi_native_contract.c']
    executable = work/'card-contract'
    subprocess.run([args.compiler]+compiler_flags(entries,'/card_spi_wait.c')+
                   flags+list(map(str,card_sources))+['-o',str(executable)],check=True,capture_output=True,text=True)
    subprocess.run([str(executable)],check=True)
    for operation in ('status','read','write'):
        result = subprocess.run([str(executable),operation],capture_output=True,text=True)
        assert result.returncode == -signal.SIGABRT, (operation,result.returncode,result.stderr)
        assert 'Unsupported physical DS cartridge SPI register 0x040001a0' in result.stderr
    registry = json.loads((build/'native-overlays/provider-registry.json').read_text())
    local = ['gPokewalkerIrImageSizes','gPokewalkerIrMessageQueue','gPokewalkerIrSendBuffer',
             'gPokewalkerIrStrollSizes','gPokewalkerIrTransfer']
    shared = ['CARD_SetSpiReadWaitCycles','CARD_SetSpiWriteWaitCycles','CARD_SpiWaitGetStatus',
              'CARD_SpiWaitInit','CARD_SpiWaitReadRange','CARD_SpiWaitWriteRange',
              '_f_ulltof','_fdiv','_ll_udiv']
    image = build/'native-overlays/libheartgold_image_112.dylib'
    exports = {line.split()[-1] for line in subprocess.run(['nm','-g','-U',str(image)],check=True,capture_output=True,text=True).stdout.splitlines() if line.split()}
    imports = {line.split()[-1] for line in subprocess.run(['nm','-u',str(image)],check=True,capture_output=True,text=True).stdout.splitlines() if line.split()}
    for name in local + shared:
        symbol = '_'+name
        providers = [p for p in registry['definitions'] if p['native_exported_identity']==symbol and p['abi_representation']=='native-arm64']
        assert len(providers)==1,(name,providers)
        assert providers[0]['image_owner']==('OVY_112' if name in local else 'main')
        assert symbol in (exports if name in local else imports), name
    subprocess.run([sys.executable,'-B',str(ROOT/'cmake/native_overlay_preflight.py'),
                    '--otool','otool',str(image)],check=True)
    print('All 14 native providers have unique ownership and the expected image exports/imports.')
    print('Native storage identity, >32-bit destinations, original requests, CARD initialization/waits, and three fatal hardware boundaries passed.')


if __name__ == '__main__':
    try: main()
    except subprocess.CalledProcessError as error:
        print(error.stderr,file=sys.stderr)
        raise

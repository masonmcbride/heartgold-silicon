"""Shared original ARM32 frontend contract (not native LP64 compilation)."""
from pathlib import Path
import fnmatch
import json
import re


def cxx_flags(game, member):
    """Honor the original build's exception policy, including per-member rules."""
    common=(game/'common.mk').read_text()
    if not re.search(r'(?m)^EXCCFLAGS\s*:=\s*-Cpp_exceptions off\s*$',common):
        raise ValueError('unproved original default C++ exception policy')
    enabled=False;matches=[]
    for line in (game/'Makefile').read_text().splitlines():
        line=line.split('#',1)[0].strip()
        if not re.search(r'EXCCFLAGS\s*[:+?]?=',line):continue
        rule=re.fullmatch(r'(.+?):\s*(?:private\s+)?EXCCFLAGS\s*:?=\s*-Cpp_exceptions\s+(on|off)',line)
        if not rule:raise ValueError('unsupported original per-member exception rule: '+line)
        for pattern in rule[1].split():
            if not pattern.startswith('$(BUILD_DIR)/'):raise ValueError('unknown original target pattern')
            if fnmatch.fnmatchcase(member,pattern.removeprefix('$(BUILD_DIR)/')):matches.append(rule[2])
    if len(set(matches))>1:raise ValueError('conflicting original C++ exception policies')
    if matches:enabled=matches[-1]=='on'
    return ['-std=gnu++98','-fexceptions' if enabled else '-fno-exceptions']


def private_overlay(game, out, records):
    """Reuse approved declaration-only adaptations without native layouts."""
    from native_sources import PRIVATE_FUNCTIONS,guest32_frontend,write_if_changed
    paths=set()
    for record in records:
        if record['source'] in PRIVATE_FUNCTIONS:
            paths.update((record['source'],PRIVATE_FUNCTIONS[record['source']][0]))
    approved={
        'lib/NitroSDK/src/mic.c',
        'lib/NitroSDK/src/rtc/rtc_api.c',
        'lib/src/nitrocrypto_rc4_fast.c',
        'src/comm_state.c',
        'src/comm_state_private.h',
        'lib/include/nitro/os/thread.h',
    }
    selected={r['source'] for r in records}
    paths.update(selected & approved)
    if 'src/comm_state.c' in selected:
        paths.add('src/comm_state_private.h')
    if 'lib/NitroSDK/src/os/os_thread.c' in selected:
        paths.add('lib/include/nitro/os/thread.h')
    roots=[]
    for relative in sorted(paths):
        source=game/relative;target=out/'frontend'/relative
        write_if_changed(target,guest32_frontend(relative,source.read_text(),game))
        roots.append({'type':'file','name':str(source),'external-contents':str(target),'use-external-name':False})
    if not roots:return [],{}
    overlay=out/'frontend.json';write_if_changed(overlay,json.dumps(dict(version=0,roots=roots)))
    return ['-ivfsoverlay',str(overlay)],{r['name']:r['external-contents'] for r in roots}


def flags(game, build):
    # The original sources use block-scoped for declarations. GNU89 accepts the
    # syntax but puts repeated loop variables in one scope. Preserve the existing
    # header inline definition convention independently of C99 loop scoping.
    return ['-target','armv5-apple-darwin','-ffreestanding','-fno-builtin',
            '-fsigned-char','-fno-short-enums','-std=gnu99','-fgnu89-inline',
            '-Wno-error=implicit-function-declaration','-Wno-error=implicit-int',
            '-Wno-error=incompatible-pointer-types','-DSDK_ARM9','-DSDK_CODE_ARM',
            '-DSDK_FINALROM','-DHEARTGOLD','-DENGLISH',
            *['-I'+str(d) for d in (build/'include',game/'include',game/'include/library',
                                  game/'lib/include',game/'lib/NitroSDK/include',game/'files',build/'generated/files')],
            '-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes']

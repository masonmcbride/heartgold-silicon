"""Shared original ARM32 frontend contract (not native LP64 compilation)."""
from pathlib import Path


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
                                  game/'lib/include',game/'lib/NitroSDK/include',build/'generated/files')],
            '-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes']

"""Source-validated lifecycle contracts for compiled original OS code."""
import hashlib
from pathlib import Path

def apply(codes, game):
    source=Path(game)/'lib/NitroSDK/src/os/os_thread.c'
    expected='eb91f80067f2aa05ef0e17d31c3c5c77aec256e7ce1e4e3e2211da1572723ed5'
    for f in codes:
        if f['name']!='OS_CreateThread' or not f['definition']:continue
        if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:raise ValueError('OS_CreateThread original source changed')
        if Path(f['origin']).resolve()!=source.resolve() or f['return']!='void' or f['params']!=['ptr','ptr','ptr','ptr','i32','i32']:raise ValueError('OS_CreateThread lifecycle ABI changed')
        for relative,digest in {'lib/include/nitro/os/common/thread_shared.h':'c5912e365f7a55ab466f1c4db082a5fa9ca1222d69b1709b16bac256369123e2','lib/include/nitro/os/context.h':'15cb1600a66fecc17c1a0501539e778eb4a58a5fa5e224dd28c072367904a337'}.items():
            if hashlib.sha256((Path(game)/relative).read_bytes()).hexdigest()!=digest:raise ValueError('original context/thread layout changed: '+relative)
        f.update(return_hook='g32_bind_thread_context',return_arguments=[0,3,4])


def dispatcher(codes, admitted):
    """Only resident main definitions are callable from bootstrap.

    Overlay entries deliberately fail closed: this project has no production
    guest overlay residency loader yet. Source-local identities stay distinct.
    """
    entries=[f for f in codes if f['key'] in admitted and f['definition'] and f.get('executable',True) and f['address_taken'] and f['return']=='void' and f['params'] in ([],['ptr'],['i32']) and not f.get('varargs')]
    text=['#include "guest32.h"']
    for f in entries:text.append('extern void '+f['native']+'(void*'+(',unsigned' if f['params'] else '')+');')
    text.append('void guest32_thread_entry(void *ram,unsigned code,unsigned arg){switch(code){')
    for f in sorted(entries,key=lambda f:f['address']):text.append('case '+str(f['address'])+':'+f['native']+'(ram'+(',arg' if f['params'] else '')+');return;')
    text.append('default:g32_bad_code(ram,code);}}')
    return '\n'.join(text)+'\n',entries

"""Stable synthetic 32-bit guest function handles, not original Nintendo PCs."""
import hashlib

START = 0x20000000
END = 0x80000000
SLOTS = (END - START) // 4


def candidate(key):
    if not isinstance(key, str) or not key:
        raise ValueError('empty guest code key')
    key = key.split('/upstream/pokeheartgold/', 1)[-1]
    n = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big') % SLOTS
    return START + 4 * n


def allocate(functions, previous=()):
    """Pin past addresses; reject signature changes and hash collisions."""
    prior, occupied = {}, {}
    for f in previous:
        k, addr = f['key'], f['address']
        if k in prior or not isinstance(addr, int) or not (0 < addr < END) or addr % 4:
            raise ValueError('invalid previous guest identity: ' + k)
        if addr in occupied and occupied[addr] != k:
            raise ValueError('previous code identity collision: ' + k)
        prior[k], occupied[addr] = f, k

    result = {}
    for k in sorted(functions):
        f = functions[k]
        if k in prior:
            old = prior[k]
            if any(old.get(field) != f.get(field)
                   for field in ('params', 'return', 'local', 'varargs')):
                raise ValueError('changed guest code ABI for pinned identity: ' + k)
            addr = old['address']
        else:
            addr = candidate(k)

        if addr in occupied and occupied[addr] != k:
            raise ValueError(
                f'guest code address collision 0x{addr:08x}: '
                f'{k} / {occupied[addr]}'
            )
        occupied[addr] = k
        result[k] = addr
    return result

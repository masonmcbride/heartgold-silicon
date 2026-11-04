import copy, pathlib, sys, unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'cmake'), str(ROOT/'compiler/guest32')]
from code_ids import candidate, allocate
from shared import plan


def fn(owner, name):
    key=f'/tmp/p/upstream/pokeheartgold/src/{owner}.c|{name}'
    return dict(key=key, name=name, local=False, definition=True,
                params=['ptr'], **{'return':'void'}, origin=key.split('|')[0],
                origin_line=1, body_hash='abc', address_taken=True, coalesce=False)


def image(owner, address):
    glob={'tag_'+owner: dict(offset=address, size=16)}
    return dict(register_edges=[], original_assembly_globals=glob,
                assembly_globals=glob,
                c_globals={'value_'+owner:dict(offset=0,size=16)},
                codes=[fn(owner,'a'),fn(owner,'b')])


class StableIDs(unittest.TestCase):
    def setUp(self):
        self.catalogs={
            'OVY_0':image('a',0x02001000),
            'OVY_38':image('b',0x02002000)
        }
        self.old=plan(self.catalogs)

    def test_third_image_preserves_existing_code_and_storage(self):
        extended=plan({
            **self.catalogs, 'OVY_44':image('c',0x02003000)
        },self.old)
        old={f['key']:f['address'] for f in self.old['codes']}
        new={f['key']:f['address'] for f in extended['codes']}
        self.assertEqual({k:new[k] for k in old},old)
        for name in self.catalogs:
            self.assertEqual(
                self.old['images'][name]['c_globals'],
                extended['images'][name]['c_globals']
            )

    def test_independent_clean_plans_stable(self):
        third={'OVY_44':image('c',0x02003000),**self.catalogs}
        a=plan(third)
        b=plan({**self.catalogs,'OVY_44':third['OVY_44']})
        self.assertEqual(a['codes'],b['codes'])

    def test_preexisting_legacy_id_pinned(self):
        legacy=copy.deepcopy(self.old)
        for i,f in enumerate(legacy['codes']):
            f['address']=0x10000000+i*4
        updated=plan({
            **self.catalogs,'OVY_44':image('c',0x02003000)
        },legacy)
        d={f['key']:f['address'] for f in updated['codes']}
        for f in legacy['codes']:
            self.assertEqual(d[f['key']],f['address'])


    def test_duplicate_registration_edges_are_idempotent(self):
        edge = dict(
            source='original.c', function='Register',
            target='Callback', previous='', mode='direct',
            line=12, argument=0, offset=0
        )
        catalogs = copy.deepcopy(self.catalogs)
        catalogs['OVY_0']['register_edges'] = [edge]
        catalogs['OVY_38']['register_edges'] = [dict(edge)]

        third = image('c', 0x02003000)
        third['register_edges'] = [dict(edge)]
        catalogs['OVY_44'] = third

        result = plan(catalogs)
        self.assertEqual(result['register_edges'], [edge])

    def test_distinct_registration_edges_are_preserved(self):
        edge = dict(
            source='original.c', function='Register',
            target='Callback', previous='', mode='direct',
            line=12, argument=0, offset=0
        )
        catalogs = copy.deepcopy(self.catalogs)
        catalogs['OVY_0']['register_edges'] = [edge]
        catalogs['OVY_38']['register_edges'] = [
            dict(edge, target='DifferentCallback')
        ]

        result = plan(catalogs)
        self.assertEqual(len(result['register_edges']), 2)

    def test_changed_abi_rejected(self):
        changed=copy.deepcopy(self.catalogs)
        changed['OVY_0']['codes'][0]['params']=['i64']
        with self.assertRaisesRegex(ValueError,'changed guest code ABI'):
            plan(changed,self.old)

    def test_colliding_new_ids_rejected(self):
        functions={
            f['key']:f for f in self.catalogs['OVY_0']['codes']
        }
        with patch('code_ids.candidate',return_value=0x21111110):
            with self.assertRaisesRegex(ValueError,'collision'):
                allocate(functions)

    def test_checkout_independent_address(self):
        self.assertEqual(
            candidate(fn('x','z')['key']),
            candidate('/other/upstream/pokeheartgold/src/x.c|z')
        )


if __name__=='__main__':
    unittest.main()

"""Global projection must preserve unknown edges and original overlap evidence."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'compiler/guest32'))
from whole_program import components, memory_constraints, project


class WholeProgram(unittest.TestCase):
    def test_large_scc(self):
        graph = {str(i): {str((i+1) % 5000)} for i in range(5000)}
        self.assertEqual(components(graph), [sorted(graph)])

    def test_direction_and_determinism(self):
        graph = {'c': set(), 'b': {'a', 'c'}, 'a': {'b'}}
        self.assertEqual(components(graph), [['a', 'b'], ['c']])
        self.assertEqual(components(dict(reversed(list(graph.items())))), components(graph))

    def test_aliases_and_overlay_reuse(self):
        catalog = dict(images={
            'A': dict(assembly_globals={'base': dict(offset=32, size=16), 'interior': dict(offset=36, size=12)}),
            'B': dict(c_globals={'other': dict(offset=40, size=16)})})
        result = memory_constraints(catalog)
        self.assertEqual(len(result['intervals']), 2)
        self.assertEqual(result['overlap_constraints'][0]['start'], 40)
        self.assertEqual(result['overlap_constraints'][0]['end'], 48)
        catalog['images']['B']['c_globals']['other']['offset'] = 2**32 - 1
        with self.assertRaises(ValueError):
            memory_constraints(catalog)

    def test_unknown_edges_and_storage_owners(self):
        manifest = {'main': dict(name='main', objects=['a.o', 'b.o', 'missing.o'])}
        def desc(name):
            return dict(functions=[dict(key=name, name=name, definition=True, local=False)],
                        globals=[dict(key='shared', definition=True)],
                        calls=[dict(target=None), dict(target='unavailable')])
        result = project(manifest, [('a#', 'a.o', desc('a')), ('b#', 'b.o', desc('b'))], dict(codes=[]))
        kinds = [r['kind'] for r in result['obligations']]
        self.assertIn('storage-ownership', kinds)
        self.assertIn('missing-original-description', kinds)
        self.assertEqual(kinds.count('dynamic-call'), 2)
        self.assertEqual(kinds.count('unresolved-call'), 2)
        self.assertFalse(result['admitted'])


if __name__ == '__main__':
    unittest.main()

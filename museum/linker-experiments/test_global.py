import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
"""Global selection must include complete zero-demand SCCs and isolate blockers."""
import unittest
import overlay_graph


class GlobalClosure(unittest.TestCase):
    def test_all_roots_includes_zero_demand_cycle(self):
        candidates=[dict(name='A', id=1, definitions=['_a'],imports=['_b'],satisfies=[]),
                    dict(name='B', id=2, definitions=['_b'],imports=['_a'],satisfies=[]),
                    dict(name='C', id=3, definitions=['_c'],imports=['_absent'],satisfies=['_c'])]
        selected, rejected=overlay_graph.choose(candidates,set(),129,all_roots=True)
        self.assertEqual(selected,['A','B'])
        self.assertIn('_absent',rejected['C'])

    def test_global_rejects_competing_provider_even_in_zero_demand_image(self):
        candidates=[dict(name='A',id=1,definitions=['_a'],imports=['_b'],satisfies=['_a']),
                    dict(name='B',id=2,definitions=['_b'],imports=[],satisfies=[]),
                    dict(name='C',id=3,definitions=['_b'],imports=[],satisfies=[])]
        selected, rejected=overlay_graph.choose(candidates,set(),129,all_roots=True)
        # The membership selector rejects duplicate exports before this graph.
        # The graph itself must still refuse an ambiguous importing consumer.
        self.assertNotIn('A',selected)
        self.assertIn('Ambiguous providers',rejected['A'])


if __name__=='__main__': unittest.main()

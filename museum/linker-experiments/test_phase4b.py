import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
from pathlib import Path
import subprocess
import tempfile
import unittest
import overlay_graph
import phase3
from phase2 import ROOT
import native_assembly_data as assembly


class GraphTests(unittest.TestCase):
    def test_zero_demand_provider_and_scc_dependency(self):
        rows = [dict(name='field',id=1,definitions=['_f'],imports=['_o'],satisfies=['_f']),
                dict(name='OVY_2',id=2,definitions=['_o'],imports=['_f','_p'],satisfies=[]),
                dict(name='provider',id=3,definitions=['_p'],imports=[],satisfies=[])]
        graph = overlay_graph.analyze(rows,set())
        self.assertIn(['OVY_2','field'],graph['components'])
        self.assertEqual(graph['edges']['OVY_2'],['field','provider'])
        self.assertEqual(phase3.choose_batch(rows,set(),3)[0],['field','OVY_2','provider'])
        self.assertEqual(phase3.choose_batch(rows,set(),2)[0],[])
        group = graph['components'].index(['OVY_2','field'])
        self.assertEqual(graph['component_dependencies'][group], [graph['components'].index(['provider'])])

    def test_after_is_not_a_provider_or_load_edge(self):
        rows=[dict(name='a',id=1,after=['b'],definitions=['_a'],imports=['_unknown'],satisfies=['_a']),
              dict(name='b',id=2,definitions=['_b'],imports=[],satisfies=[])]
        graph=overlay_graph.analyze(rows,set())
        self.assertEqual(graph['edges']['a'],[])
        self.assertIn('source ownership/ABI',graph['blockers']['a']['_unknown'])
        self.assertFalse(phase3.choose_batch(rows,set(),10)[0])

    def test_selected_provider_collision_is_blocked(self):
        rows=[dict(name='a',id=1,definitions=['_a'],imports=['_b']),
              dict(name='b',id=2,definitions=['_b'],imports=[])]
        self.assertIn('_b',overlay_graph.analyze(rows,{'_b'})['blockers']['a'])


if __name__=='__main__': unittest.main()

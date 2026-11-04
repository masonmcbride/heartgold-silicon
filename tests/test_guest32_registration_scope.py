import pathlib
import sys
import unittest

sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parents[1]
           / "compiler/guest32")
)
from registration_scope import scoped_spec


class RegistrationOwnership(unittest.TestCase):
    def setUp(self):
        self.spec = {
            "edges": [{"source": "OVY_0", "target": "callback"}],
            "nested": {"callbacks": [1, 2, 3]},
        }

    def test_original_zero_owner(self):
        self.assertIs(scoped_spec("OVY_0", self.spec), self.spec)

    def test_original_38_owner(self):
        self.assertIs(scoped_spec("OVY_38", self.spec), self.spec)

    def test_overlay_42_has_no_borrowed_edges(self):
        result = scoped_spec("OVY_42", self.spec)
        self.assertEqual(result["edges"], [])
        self.assertEqual(result["nested"]["callbacks"], [])
        self.assertEqual(len(self.spec["edges"]), 1)

    def test_overlay_44_has_no_borrowed_edges(self):
        self.assertEqual(
            scoped_spec("OVY_44", self.spec)["edges"], []
        )


if __name__ == "__main__":
    unittest.main()

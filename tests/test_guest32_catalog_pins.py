import pathlib
import sys
import unittest

sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parents[1]
           / "compiler/guest32")
)
from closure import merge_main_overlay_pins


class CatalogPins(unittest.TestCase):
    def record(self, definition, params, address=0x10004e94):
        return dict(
            key="example", address=address,
            definition=definition, params=params,
            local=False, varargs=False, **{"return": "i32"}
        )

    def test_main_definition_survives_overlay_declaration(self):
        definition = self.record(True, ["i32"])
        declaration = self.record(False, ["i16"])
        result = merge_main_overlay_pins(
            [definition], [declaration]
        )
        self.assertEqual(result["example"], definition)

    def test_overlay_definition_replaces_main_declaration(self):
        declaration = self.record(False, ["i16"])
        definition = self.record(True, ["i32"])
        result = merge_main_overlay_pins(
            [declaration], [definition]
        )
        self.assertEqual(result["example"], definition)

    def test_address_conflict_rejected(self):
        with self.assertRaises(ValueError):
            merge_main_overlay_pins(
                [self.record(True, ["i32"])],
                [self.record(False, ["i16"], 0x10004e98)]
            )

    def test_conflicting_definitions_rejected(self):
        with self.assertRaises(ValueError):
            merge_main_overlay_pins(
                [self.record(True, ["i32"])],
                [self.record(True, ["i16"])]
            )

    def test_conflicting_declarations_rejected(self):
        with self.assertRaises(ValueError):
            merge_main_overlay_pins(
                [self.record(False, ["i32"])],
                [self.record(False, ["i16"])]
            )

    def test_new_identity_admitted(self):
        record = self.record(True, ["i32"])
        self.assertEqual(
            merge_main_overlay_pins([], [record])["example"],
            record
        )

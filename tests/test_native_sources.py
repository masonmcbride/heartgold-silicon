"""Focused regressions for source-validated native representation changes."""
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "upstream/pokeheartgold"
spec = importlib.util.spec_from_file_location("native_sources", ROOT / "cmake/native_sources.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class NativeSourceAdaptations(unittest.TestCase):
    def test_every_party_action_and_cancel_value(self):
        original = (GAME / "src/party_menu_list_items.c").read_text()
        result = native.adapt("src/party_menu_list_items.c", original, GAME)
        entries, expected = native.party_actions(original)
        self.assertEqual(len(entries), 30)
        actual = native.span(result, "static const u32 _02101CB8[] = {", "\n};")
        self.assertEqual(actual, expected)
        self.assertEqual(actual.count("= LIST_CANCEL,"), 3)
        # Take and TakeMail must remain distinct identifiers and callbacks.
        self.assertIn("[PARTY_MON_CONTEXT_MENU_TAKE_MAIL] = PARTY_MON_CONTEXT_MENU_TAKE_MAIL,", actual)
        self.assertNotIn("PARTY_MON_CONTEXT_MENU_TAKEMail", result)
        for action, callback in entries:
            self.assertIn(f"[{action}] = {callback},", result)
        # Every original callback body and the original getter are untouched.
        first, last = original.index("static const u32 _02101CB8[]"), original.index("u32 GetPartyMenuContextMenuActionFunc")
        native_first, native_last = result.index("static const u32 _02101CB8[]"), result.index("u32 GetPartyMenuContextMenuActionFunc")
        self.assertEqual(result[:native_first], original[:first])
        self.assertEqual(result[native_last:result.index("\nvoid HG_PartyMenu_InvokeAction")], original[last:])

    def test_party_source_has_only_verified_dispatch_changes(self):
        original = (GAME / "src/party_menu.c").read_text()
        result = native.adapt("src/party_menu.c", original, GAME)
        self.assertEqual(result.count("HG_PartyMenu_InvokeAction(func, partyMenu,"), 2)
        self.assertNotIn("((PartyMonContextMenuActionFunc)func)", result)

    def test_private_comm_state_helpers_stay_private(self):
        source = (GAME / "src/comm_state.c").read_text()
        original = (GAME / "src/comm_state_private.h").read_text()
        result = native.adapt("src/comm_state_private.h", original, GAME)
        private = set(re.findall(r"^static\s+(?:void|BOOL|s32|int)\s+(CommState_\w+)\(", source, re.M))
        self.assertEqual(len(private), 77)
        for name in private:
            self.assertNotRegex(result, rf"\b{name}\s*\(")
        self.assertIn("int DWC_Init(void *work);", result)
        adapted = native.adapt("src/comm_state.c", source, GAME)
        for name in private:
            self.assertRegex(adapted, rf"static\s+(?:void|BOOL|s32|int)\s+{name}\(")
        self.assertIn("((uintptr_t)work + 31) & ~(uintptr_t)31", adapted)

    def test_changed_source_is_rejected(self):
        text = (GAME / "lib/NitroSystem/src/g2d_char_canvas.c").read_text()
        with self.assertRaises(ValueError):
            native.adapt("lib/NitroSystem/src/g2d_char_canvas.c", text.replace("asm { clz x, x }", "unknown"), GAME)
        with self.assertRaises(ValueError):
            native.adapt("not-a-registered-file.c", "", GAME)

    def test_unchanged_outputs_are_not_rewritten(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "build") as directory:
            path = Path(directory) / "native.c"
            native.write_if_changed(path, "same\n")
            stamp = path.stat().st_mtime_ns
            native.write_if_changed(path, "same\n")
            self.assertEqual(path.stat().st_mtime_ns, stamp)


if __name__ == "__main__":
    unittest.main()

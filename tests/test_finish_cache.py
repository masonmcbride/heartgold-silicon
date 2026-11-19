"""Provider-generation reuse must invalidate on dependencies and output damage."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'compiler/guest32'))
from finish_cache import FinishCache
from publication import publish


class FinishCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.args = argparse.Namespace(
            game=self.root/'game', build=self.root/'build', out=self.root/'out',
            llvm_bin=self.root/'llvm', lowerer=self.root/'lowerer',
            codegen=self.root/'codegen', image_root=self.root/'shared',
            compiler=str(self.root/'clang'), provider_plan=self.root/'plan.json',
            root_symbol=['NitroMain'])
        self.args.game.mkdir()
        self.source = self.args.game/'source.c'
        self.source.write_text('old')
        self.args.out.mkdir()
        (self.args.out/'complete.stamp').write_text('passed')
        self.output = self.args.out/'native.o'
        self.output.write_bytes(b'object')
        self.environment = patch.dict(os.environ, {k: '' for k in (
            'CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH',
            'DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH')})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.cache = self.new_cache()
        self.assertFalse(self.cache.reuse(self.args.out))
        self.cache.record()

    def new_cache(self):
        return FinishCache(self.args, self.root)

    def hit(self):
        return self.new_cache().reuse(self.args.out)

    def test_unchanged_skips_worker_and_publication(self):
        before = self.output.stat()
        publish(self.args.out, lambda _: self.fail('worker ran'), reuse=self.new_cache().reuse)
        self.assertEqual(before, self.output.stat())

    def test_edit_with_restored_mtime_invalidates(self):
        before = self.source.stat()
        self.source.write_text('new')
        os.utime(self.source, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertFalse(self.hit())

    def test_added_source_invalidates(self):
        (self.args.game/'new.h').write_text('new declaration')
        self.assertFalse(self.hit())

    def test_deleted_source_invalidates(self):
        self.source.unlink()
        self.assertFalse(self.hit())

    def test_output_damage_invalidates(self):
        self.output.write_bytes(b'broken')
        self.assertFalse(self.hit())

    def test_missing_output_invalidates(self):
        self.output.unlink()
        self.assertFalse(self.hit())

    def test_environment_invalidates(self):
        with patch.dict(os.environ, {'SDKROOT': '/different-sdk'}):
            self.assertFalse(self.hit())

    def test_external_search_paths_disable_reuse(self):
        with patch.dict(os.environ, {'CPATH': '/external/headers'}):
            cache = self.new_cache()
            self.assertFalse(cache.reuse(self.args.out))
            cache.record()
            self.assertFalse(self.hit())

    def test_changed_during_build_does_not_earn_receipt(self):
        cache = self.new_cache()
        cache.path.unlink()
        self.assertFalse(cache.reuse(self.args.out))
        self.source.write_text('changed during build')
        cache.record()
        self.assertFalse(cache.path.exists())

    def test_corrupt_receipt_is_a_miss(self):
        self.cache.path.write_text('not JSON')
        self.assertFalse(self.hit())


if __name__ == '__main__':
    unittest.main()

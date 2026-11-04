import pathlib
import sys
import unittest

sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parents[1]
           / 'compiler/guest32')
)
from closure import original_root_owners


class RootOwnership(unittest.TestCase):
    def setUp(self):
        self.defn = dict(name='Wanted', definition=True, local=False)
        self.descriptions = {
            'src/provider.o': {'functions': [self.defn]},
            'src/consumer.o': {
                'functions': [
                    dict(name='Wanted', definition=False, local=False)
                ]
            },
        }

    def test_unique_original_owner(self):
        self.assertEqual(
            original_root_owners(self.descriptions, ['Wanted']),
            {'Wanted': 'src/provider.o'}
        )

    def test_missing_owner_rejected(self):
        with self.assertRaises(ValueError):
            original_root_owners(self.descriptions, ['Missing'])

    def test_duplicate_owners_rejected(self):
        self.descriptions['src/duplicate.o'] = {
            'functions': [self.defn]
        }
        with self.assertRaises(ValueError):
            original_root_owners(self.descriptions, ['Wanted'])

    def test_declaration_not_a_provider(self):
        del self.descriptions['src/provider.o']
        with self.assertRaises(ValueError):
            original_root_owners(self.descriptions, ['Wanted'])


if __name__ == '__main__':
    unittest.main()

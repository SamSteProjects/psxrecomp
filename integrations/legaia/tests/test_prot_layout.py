"""Physical ownership must not follow overlapping decoder read windows."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError
from importer.prot_layout import locate_physical_span


def archive(starts):
    return SimpleNamespace(
        SECTOR=2048, node=SimpleNamespace(size=400*2048),
        entries=[SimpleNamespace(index=i, start_lba=start, size_sectors=118)
                 for i, start in starts])


class PhysicalSpanTests(unittest.TestCase):
    def test_boundary_uses_consecutive_starts_not_read_window(self):
        source = archive([(2, 239), (3, 240), (4, 243), (5, 354)])
        before = locate_physical_span(source, 243*2048-1)
        at = locate_physical_span(source, 243*2048)
        self.assertEqual(before['entry_index'], 3)
        self.assertEqual(at['entry_index'], 4)
        self.assertEqual(at['offset_within_span'], 0)
        self.assertEqual(at['byte_length'], 111*2048)
        self.assertFalse(at['relocation_verified'])

    def test_unknown_tail_missing_row_and_ambiguous_ownership_rejected(self):
        for source, offset in [
            (archive([(4, 243), (5, 354)]), 354*2048),
            (archive([(4, 243), (6, 354)]), 243*2048),
            (archive([(0, 200), (1, 300), (2, 220), (3, 320)]), 250*2048),
        ]:
            with self.subTest(offset=offset, entries=source.entries):
                with self.assertRaises(ImportError):
                    locate_physical_span(source, offset)
        for offset in [True, -1, 400*2048]:
            with self.assertRaises(ImportError):
                locate_physical_span(archive([(0, 0), (1, 400)]), offset)


if __name__ == '__main__':
    unittest.main()

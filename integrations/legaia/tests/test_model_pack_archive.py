from hashlib import sha256
import struct
import unittest

from importer.core import ImportError
from importer.model_face_ledger import create_face_ledger
from importer.model_pack_archive import rebuild_model_pack_entry
from test_model_pack_growth import pack_source, ledger_for, container_for


def archive_source(container, header_offset=0):
    sectors = (len(container)+2047)//2048
    container = container.ljust(sectors*2048, b'\0')
    header = bytearray(header_offset+2048)
    first = header_offset//2048+1
    starts = [first, first+1, first+1+sectors, first+2+sectors, 0]
    struct.pack_into('<ii', header, header_offset+4, 5, 1)
    struct.pack_into('<5I', header, header_offset+16, *starts)
    return bytes(header)+b'A'*2048+container+b'B'*2048+b'Z'*(8*2048), starts


class ModelPackArchiveTests(unittest.TestCase):
    def test_growth_updates_later_starts_and_preserves_every_neighbor(self):
        pack, models = pack_source();_, ledger = ledger_for(models[2], 32, varied=True)
        for header_offset in (0, 2048):
            source, starts = archive_source(container_for(pack), header_offset)
            result, audit = rebuild_model_pack_entry(source, sha256(source).hexdigest(), 1, 1,
                sha256(pack).hexdigest(), [dict(slot_index=2, ledger=ledger)], header_offset=header_offset)
            growth = audit['archive']['growth_sectors'];self.assertGreater(growth, 0)
            self.assertEqual(len(result)-len(source), growth*2048)
            expected = [value+(growth if index>1 and value else 0) for index,value in enumerate(starts)]
            self.assertEqual(list(struct.unpack_from('<5I', result, header_offset+16)), expected)
            start, end = starts[1]*2048, starts[2]*2048
            self.assertEqual(result[header_offset+2048:start], source[header_offset+2048:start])
            self.assertEqual(result[end+growth*2048:], source[end:])
            self.assertEqual(result[:header_offset], source[:header_offset])
            self.assertTrue(audit['reopened_pack_verified']);self.assertTrue(audit['physical_neighbors_preserved'])
            self.assertTrue(audit['disc_relocation_required']);self.assertFalse(audit['build_ready'])

    def test_noop_preserves_complete_archive_and_toc(self):
        pack, models = pack_source();source, _ = archive_source(container_for(pack, 37))
        result, audit = rebuild_model_pack_entry(source, sha256(source).hexdigest(), 1, 1,
            sha256(pack).hexdigest(), [dict(slot_index=0, ledger=create_face_ledger(models[0]))])
        self.assertEqual(result, source)
        self.assertEqual(audit['archive']['growth_sectors'], 0)
        self.assertFalse(audit['disc_relocation_required'])

    def test_overlapping_read_window_cannot_lend_capacity_to_physical_owner(self):
        pack, models = pack_source();_, ledger = ledger_for(models[0])
        source, starts = archive_source(container_for(pack))
        damaged = bytearray(source)
        # The third descriptor points into entry 2, inside entry 1's legacy
        # read window but outside its consecutive-start physical ownership.
        struct.pack_into('<I', damaged, starts[1]*2048+28, 2052)
        damaged = bytes(damaged)
        with self.assertRaises(ImportError):
            rebuild_model_pack_entry(damaged, sha256(damaged).hexdigest(), 1, 1,
                sha256(pack).hexdigest(), [dict(slot_index=0, ledger=ledger)])

    def test_source_header_entry_descriptor_and_model_binding_reject(self):
        pack, models = pack_source();_, ledger = ledger_for(models[0]);source, _ = archive_source(container_for(pack))
        records = [dict(slot_index=0, ledger=ledger)]
        for entry, descriptor, digest in ((True, 1, sha256(pack).hexdigest()),
                                          (-1, 1, sha256(pack).hexdigest()),
                                          (99, 1, sha256(pack).hexdigest()),
                                          (1, True, sha256(pack).hexdigest()), (1, 0, sha256(pack).hexdigest()), (1, 1, 'stale')):
            with self.assertRaises(ImportError):
                rebuild_model_pack_entry(source, sha256(source).hexdigest(), entry, descriptor, digest, records)
        for raw, digest, header in ((source, 'stale', 0), (source[:-1], sha256(source[:-1]).hexdigest(), 0),
                                    (source, sha256(source).hexdigest(), True), (source, sha256(source).hexdigest(), 2048)):
            with self.assertRaises(ImportError):
                rebuild_model_pack_entry(raw, digest, 1, 1, sha256(pack).hexdigest(), records, header_offset=header)
        bad = [dict(slot_index=1, ledger=ledger)]
        with self.assertRaises(ImportError):
            rebuild_model_pack_entry(source, sha256(source).hexdigest(), 1, 1, sha256(pack).hexdigest(), bad)


if __name__ == '__main__':
    unittest.main()

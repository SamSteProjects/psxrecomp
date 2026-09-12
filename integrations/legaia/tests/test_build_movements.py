import unittest
from sdk.build import _merge_movement_patch, _hash, BuildError

class MovementMerge(unittest.TestCase):
    def test_exact_span_overlap_and_unaudited_rejection(self):
        source = bytes(8); changed = source[:3] + b"\x05" + source[4:]
        entry = dict(decoded_byte_offset=3, owner_id="owner", source_record_sha256="record", requested_values={"x":704})
        audit = dict(movement_id="id", field="x", decoded_byte_offset=3,
                     owner_id="owner", source_record_sha256="record",
                     source_decoded_man_sha256=_hash(source), before_byte=0, after_byte=5)
        self.assertEqual(_merge_movement_patch(source, source, changed, [audit], {"id":entry}, []), changed)
        for previous in ([dict(decoded_byte_offset=2, byte_length=3)], [dict(decoded_byte_offset=3)]):
            with self.assertRaises(BuildError):
                _merge_movement_patch(source, source, changed, [audit], {"id":entry}, previous)
        with self.assertRaises(BuildError):
            _merge_movement_patch(source, source, changed[:-1]+b"x", [audit], {"id":entry}, [])
        with self.assertRaises(BuildError):
            _merge_movement_patch(source, source, changed, [dict(audit, owner_id="other")], {"id":entry}, [])

        with self.assertRaisesRegex(BuildError, 'requested coordinates'):
            _merge_movement_patch(source,source,changed,[audit],{'id':dict(entry,requested_values={'x':128})},[])

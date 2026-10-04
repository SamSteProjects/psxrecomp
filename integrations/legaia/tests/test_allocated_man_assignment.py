from hashlib import sha256
import unittest
from uuid import uuid4

from importer.animation import animation_record_ranges
from importer.animation_allocation import append_animation_records
from importer.core import ImportError,parse_man
from test_importer_man_assignments import fixture
from test_animation_allocation import bank


def allocated(context,frames=None):
    return append_animation_records(context._anm,sha256(context._anm).hexdigest(),[
        dict(record_id=str(uuid4()),donor_record_index=1,source_frame_indices=frames or [1,0,1],edits=[])])[0]


class AllocatedManAssignment(unittest.TestCase):
    def test_explicit_appended_ordinal_changes_only_verified_header_bytes(self):
        context,original=fixture();expanded=allocated(context)
        a,b=animation_record_ranges(expanded)[2];record_hash=sha256(expanded[a:b]).hexdigest()
        request={1:dict(donor_record_index=2,allocated_record_index=2,record_sha256=record_hash)}
        candidate,audit=context.patch_allocated(expanded,sha256(expanded).hexdigest(),request,original=original)
        self.assertEqual(len(candidate),len(original))
        self.assertEqual({i for i,(a,b) in enumerate(zip(original,candidate)) if a!=b},
                         {row['decoded_byte_offset'] for row in audit})
        before=parse_man(original).actors[0];after=parse_man(candidate).actors[0]
        self.assertEqual((after.model_index,after.animation_id),(5,3))
        self.assertEqual((before.world_x,before.world_z),(after.world_x,after.world_z))
        self.assertEqual(context._man,original)
        self.assertTrue(all(row['record_sha256']==record_hash for row in audit))

    def test_stale_hashes_retail_ordinals_aliases_mismatched_layout_and_byte_overflow_reject(self):
        context,original=fixture();expanded=allocated(context)
        a,b=animation_record_ranges(expanded)[2]
        value=dict(donor_record_index=2,allocated_record_index=2,record_sha256=sha256(expanded[a:b]).hexdigest())
        for bad in (dict(value,allocated_record_index=1),dict(value,allocated_record_index=True),
                    dict(value,record_sha256='0'*64),dict(value,donor_record_index=True),dict(value,extra=1)):
            with self.assertRaises(ImportError):context.patch_allocated(expanded,sha256(expanded).hexdigest(),{1:bad})
        with self.assertRaises(ImportError):context.patch_allocated(expanded,'0'*64,{1:value})
        with self.assertRaises(ImportError):context.patch_allocated(expanded,sha256(expanded).hexdigest(),{1:value},original=original+b'x')
        aliased,_=fixture(alias=True)
        with self.assertRaises(ImportError):aliased.patch_allocated(expanded,sha256(expanded).hexdigest(),{1:value})
        mismatched,_=fixture(bones=(2,3),model_counts={4:2,5:3});expanded2=allocated(mismatched)
        a,b=animation_record_ranges(expanded2)[2]
        with self.assertRaises(ImportError):mismatched.patch_allocated(expanded2,sha256(expanded2).hexdigest(),{
            1:dict(value,record_sha256=sha256(expanded2[a:b]).hexdigest())})
        source=bank([context._anm[x:y] for x,y in animation_record_ranges(context._anm)]+[b'opaque']*253)
        from importer.man_assignments import ManAssignmentContext
        many=ManAssignmentContext('synthetic',original,context._stream,context._models,source,{})
        donor=context._anm[animation_record_ranges(context._anm)[1][0]:]
        from importer.animation_allocation import append_animation_record_payloads
        expanded3,_=append_animation_record_payloads(source,sha256(source).hexdigest(),[dict(record_id=str(uuid4()),record=donor)])
        with self.assertRaisesRegex(ImportError,'byte selector'):many.patch_allocated(expanded3,sha256(expanded3).hexdigest(),{
            1:dict(value,allocated_record_index=255,record_sha256=sha256(donor).hexdigest())})


if __name__=='__main__':unittest.main()

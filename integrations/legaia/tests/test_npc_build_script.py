from io import BytesIO
from hashlib import sha256
import unittest,zipfile
from sdk.project import ProjectError
from sdk.npc_build_script import emitted_prot,actor_allocations
class SavedNpcScriptTests(unittest.TestCase):
    def package(self,payload):
        stream=BytesIO()
        with zipfile.ZipFile(stream,'w') as z:z.writestr('assets/edit.bin',payload)
        stream.seek(0);return zipfile.ZipFile(stream)
    def test_verified_overlay_spans_source_hash_and_bounded_payload(self):
        source=b'abcdefgh';payload=b'XY';row=dict(offset=2050,size=2,file='assets/edit.bin',sha256=sha256(payload).hexdigest(),expected_sha256=sha256(b'cd').hexdigest());audit=dict(overlays=[row])
        with self.package(payload) as z:self.assertEqual(emitted_prot(source,2048,z,audit),(b'abXYefgh','fixed_span_PROT_overlays'))
        for change in [dict(expected_sha256='0'*64),dict(sha256='0'*64),dict(offset=2047),dict(size=3)]:
            with self.package(payload) as z:
                with self.assertRaises(ProjectError):emitted_prot(source,2048,z,dict(overlays=[{**row,**change}]))
        with self.package(payload) as z:
            with self.assertRaises(ProjectError):emitted_prot(source,2048,z,dict(overlays=[row,row]))
        # An unrelated disc region cannot be mistaken for a PROT edit.
        with self.package(payload) as z:self.assertEqual(emitted_prot(source,2048,z,dict(overlays=[{**row,'offset':0}])),(source,'fixed_span_PROT_overlays'))
    def test_saved_allocations_bind_the_carrier_schema_and_reject_ambiguous_families(self):
        for schema,key in [('legaia.npc-fixed-span-build.v1','actor'),('legaia.npc-compressed-growth-build.v1','actor'),('legaia.npc-streaming-growth-build.v1','actor_changes')]:
            rows=[dict(draft_id='npc',record_index=73)]
            metadata=dict(schema_version=schema,draft_audit={key:dict(drafts=rows)})
            self.assertEqual(actor_allocations(metadata),rows);detached=actor_allocations(metadata);detached[0]['record_index']=0;self.assertEqual(rows[0]['record_index'],73)
            for audit in ({},{key:None},{key:dict(drafts=[])},{key:dict(drafts=[None])},{key:dict(drafts=rows*129)},{key:dict(drafts=rows),('actor' if key=='actor_changes' else 'actor_changes'):dict(drafts=rows)}):
                with self.assertRaises(ProjectError):actor_allocations(dict(schema_version=schema,draft_audit=audit))
            with self.assertRaises(ProjectError):actor_allocations(dict(metadata,schema_version='unknown'))

if __name__=='__main__':unittest.main()

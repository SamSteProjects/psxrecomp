"""Exact facing-byte Build composition and real retail package readback."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from importer.core import decompress_lzs
from importer.pipeline import import_scene
from sdk.project import ProjectService
from sdk.build import _merge_facing_patch, _hash, BuildError, build_project, package_change_kinds

class FacingMergeTests(unittest.TestCase):
    def test_source_ownership_upper_bits_overlaps_and_unaudited_bytes_reject(self):
        source=b'abc\x81def';changed=b'abc\x85def'
        target=dict(pc=2,before_raw=0x81,decoded_byte_offset=3,owner_id='owner',source_record_sha256='record',requested_values={'sector':5},mnemonic='CAM_CFG',target_context=None)
        audit=dict(pc=2,facing_id='id',field='sector',decoded_byte_offset=3,owner_id='owner',source_record_sha256='record',source_decoded_man_sha256=_hash(source),before_byte=0x81,after_byte=0x85,before_sector=1,after_sector=5,mnemonic='CAM_CFG',target_context=None)
        self.assertEqual(_merge_facing_patch(source,source,changed,[audit],{'id':target},[]),changed)
        for bad in (dict(audit,pc=3),dict(audit,owner_id='other'),dict(audit,source_record_sha256='stale'),dict(audit,target_context=1),dict(audit,before_sector=2),dict(audit,after_sector=4),dict(audit,decoded_byte_offset=2)):
            with self.assertRaises(BuildError):_merge_facing_patch(source,source,changed,[bad],{'id':target},[])
        for previous in ([dict(decoded_byte_offset=2,byte_length=3)],[dict(decoded_byte_offset=3)]):
            with self.assertRaises(BuildError):_merge_facing_patch(source,source,changed,[audit],{'id':target},previous)
        with self.assertRaises(BuildError):_merge_facing_patch(source,source,changed[:-1]+b'X',[audit],{'id':target},[])
        with self.assertRaises(BuildError):_merge_facing_patch(source,source,b'abc\x05def',[dict(audit,after_byte=5)],{'id':target},[])
        with self.assertRaises(BuildError):_merge_facing_patch(source,source,changed,[audit],{'id':dict(target,requested_values={'sector':4})},[])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class FacingBuildTests(unittest.TestCase):
    def test_saved_source_facing_composes_with_placements_and_package_readback(self):
        private=Path(__file__).resolve().parents[3]/'local-output/sdk-20260909'
        with tempfile.TemporaryDirectory(prefix='facing-build-',dir=private) as raw:
            p=ProjectService(Path(raw));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town0b'),os.environ['LEGAIA_DISC_BIN'])
            imported=deepcopy(p.imports);owner='scene://town0b/actors/man-p1/0019'
            context=p._facing_context(owner);baseline=context._man
            target=next(row for row in context.options(owner)['targets'] if row['pc']==17)
            p.command(dict(type='set_facing_target',entity_id=owner,facing_id=target['semantic_id'],values={'sector':5}))
            actor=next(row for row in imported[p.active_scene]['actors'] if row['semantic_id']==owner)
            for combined in (False,True):
                if combined:p.command(dict(type='set_transform',entity_id=owner,position={'x':actor['imported_transform']['position']['x']+64}))
                reopened=ProjectService.open(p.save());before=deepcopy(reopened._document())
                result=build_project(reopened)
                audit=json.loads(Path(result['audit']).read_text(encoding='utf-8'))
                self.assertEqual(len(audit['overlays']),1)
                overlay=audit['overlays'][0]
                payload=(Path(result['package_directory'])/overlay['file']).read_bytes()
                decoded,_=decompress_lzs(payload,len(baseline))
                rows=[row for row in audit['edits'] if row.get('scope')=='script-facing-sector-only']
                self.assertEqual(len(rows),1);self.assertEqual(rows[0]['decoded_byte_offset'],9479)
                self.assertEqual((rows[0]['before_byte'],rows[0]['after_byte']),(0x81,0x85))
                changed=[i for i,(a,b) in enumerate(zip(baseline,decoded)) if a!=b]
                self.assertEqual(changed,sorted(row['decoded_byte_offset'] for row in audit['edits']))
                self.assertEqual(len(changed),2 if combined else 1)
                self.assertEqual(decoded[9479],0x85)
                self.assertEqual(overlay['sha256'],sha256(payload).hexdigest())
                with zipfile.ZipFile(result['path']) as archive:
                    self.assertEqual(archive.read(overlay['file']),payload)
                self.assertIn('script facing operands',package_change_kinds(audit['edits']))
                self.assertEqual(audit['validation']['live_runtime'],'not_run')
                self.assertEqual(reopened._document(),before);self.assertEqual(reopened.imports,imported)
                self.assertIn('script.facing_sector',[row['field'] for row in result['report']['changes']])

if __name__=='__main__':unittest.main()

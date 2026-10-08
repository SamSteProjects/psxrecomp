"""Actual project Review/history/persistence and independently read native Build."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from importer.pipeline import import_scene
from importer.core import decompress_lzs, ImportError as RetailImportError
from importer.branch_authoring import BranchAuthoringContext
from sdk.project import ProjectService, ProjectError
from sdk.system_flags import snapshot, review
from sdk.build import build_project, package_change_kinds
from sdk.build_review import review as build_review


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'Private Retail disc required')
class SystemFlagWorkflowTests(unittest.TestCase):
    owner = 'scene://town01/actors/man-p1/0011'
    operand = 'script://town01/actors/man-p1/0011/system-flag/0016'

    def project(self, path):
        p = ProjectService(Path(path))
        p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'], 'town01'), os.environ['LEGAIA_DISC_BIN'])
        return p

    def apply(self, p, value):
        r = review(p, self.owner, self.operand, value)
        p.command(dict(type='set_system_flag_selector', entity_id=self.owner, operand_id=self.operand,
                       value=value, review_key=r['review_key']))
        return r

    def test_readonly_review_history_save_open_and_clear(self):
        with tempfile.TemporaryDirectory() as path:
            p = self.project(path); imported = deepcopy(p.imports)
            before = deepcopy((p._document(), p.undo_stack, p.redo_stack))
            r = review(p, self.owner, self.operand, {'index':4095})
            self.assertEqual((p._document(), p.undo_stack, p.redo_stack), before)
            self.assertEqual(next(n for n in r['current_report']['instructions'] if n['pc']==22)['operands']['index'],326)
            self.assertEqual(next(n for n in r['proposed_report']['instructions'] if n['pc']==22)['operands']['index'],4095)
            self.assertFalse(r['project_changed']); self.assertFalse(r['gameplay_verified'])
            self.apply(p, {'index':4095}); current = deepcopy(p.overrides)
            self.assertEqual(len(p.undo_stack),1)
            p.undo(); self.assertFalse(p.overrides)
            p.redo(); self.assertEqual(p.overrides,current)
            p.save(); q = ProjectService.open(p.root)
            self.assertEqual(q.overrides,current); self.assertEqual(q.imports,imported)
            self.assertEqual(next(t for t in snapshot(q,self.owner)['targets'] if t['pc']==22)['current_index'],4095)
            self.apply(q,None); self.assertFalse(q.overrides)
            q.undo(); self.assertEqual(q.overrides,current)

    def test_stale_key_invalid_commands_and_source_gates_preserve_state(self):
        with tempfile.TemporaryDirectory() as path:
            p = self.project(path)
            stale = review(p,self.owner,self.operand,{'index':4095})
            self.apply(p,{'index':327})
            before = deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):
                p.command(dict(type='set_system_flag_selector',entity_id=self.owner,operand_id=self.operand,value={'index':4095},review_key=stale['review_key']))
            for value in ({'index':True},{'index':4096},{'bit':3}):
                with self.assertRaises(ProjectError): review(p,self.owner,self.operand,value)
            with self.assertRaises(ProjectError): review(p,self.owner,self.operand.replace('/0011/','/0012/'),{'index':3})
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            p.mode='live'
            with self.assertRaises(ProjectError): self.apply(p,{'index':4095})

    def test_normal_package_exact_full_man_and_branch_composition(self):
        from sdk.script_branches import review as branch_review, snapshot as branch_snapshot
        with tempfile.TemporaryDirectory() as path:
            p = self.project(path); source=p._dialogue_context(self.owner)
            offset,record,entry=source.verified_record(self.owner)
            self.apply(p,{'index':4095})
            branch='script://town01/actors/man-p1/0011/branch/0016'
            inspected,_=branch_review(p,self.owner,branch,{'target_pc':26})
            p.command(dict(type='set_branch',entity=self.owner,branch_id=branch,value={'target_pc':26},review_key=inspected['review']['review_key']))
            self.assertEqual(next(n for n in branch_snapshot(p,self.owner)['current_report']['instructions'] if n['pc']==22)['operands']['index'],4095)
            self.assertTrue(build_review(p)['normal_build_ready'])
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            built=build_project(p)
            with zipfile.ZipFile(built['path']) as package:
                payload=package.read('assets/town01-man.lzs')
            decoded=decompress_lzs(payload,len(source._man))[0]
            expected=bytearray(source._man); expected[offset+22:offset+24]=b'\x7f\xff';expected[offset+24:offset+26]=b'\x02\0'
            self.assertEqual(decoded,bytes(expected))
            audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
            self.assertIn('script system selectors',package_change_kinds(audit['edits']))
            row=next(c for c in built['report']['changes'] if c['scope']=='script-system-selector-only')
            self.assertEqual((row['asset_id'],row['before'],row['after']),(self.operand,326,4095))
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
            # Without explicit selector bindings the generic branch guard refuses.
            with self.assertRaises(RetailImportError):BranchAuthoringContext(source).inspect_owner(self.owner,decoded)

    def test_npc_package_keeps_original_selector_edit_separate_from_donor_clone(self):
        import tomllib
        from importer.pipeline import _disc_context
        from importer.core import parse_scene_table
        from importer.man_layout import read_man_layout
        with tempfile.TemporaryDirectory() as path:
            p=self.project(path);source=p._dialogue_context(self.owner)
            _,original,entry=source.verified_record(self.owner)
            self.apply(p,{'index':4095})
            p.command(dict(type='create_actor_draft',donor_entity_id=self.owner,position={'x':3008,'z':5440},name='Candidate'))
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            self.assertTrue(build_review(p)['normal_build_ready'])
            built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
            metadata=audit['npc_candidates']['scene://town01'];span=metadata['physical_owner']
            with _disc_context(p.disc_path) as (_,_,_,archive),zipfile.ZipFile(built['path']) as package:
                carrier=bytearray(archive.image.read_user(archive.node.extent_lba,span['byte_offset'],span['byte_length'],archive.node.size))
                manifest=tomllib.loads(package.read('manifest.toml').decode())
                for overlay in manifest['overlay']:
                    at=overlay['offset']-archive.node.extent_lba*2048-span['byte_offset']
                    payload=package.read(overlay['file']);self.assertGreaterEqual(at,0);self.assertLessEqual(at+len(payload),len(carrier));carrier[at:at+len(payload)]=payload
            table=parse_scene_table(bytes(carrier),span['entry_index']);descriptor=next(d for d in table.descriptors if d.type_byte==3 and d.size)
            man=decompress_lzs(carrier[descriptor.data_offset:],descriptor.size)[0]
            rows=read_man_layout(man)['records']
            donor=next(r for r in rows if r['partition']==1 and r['record_index']==11)
            clone=next(r for r in rows if r['partition']==1 and r['record_index']==53)
            self.assertEqual(man[donor['byte_offset']+22:donor['byte_offset']+26],b'\x7f\xff'+original[24:26])
            self.assertEqual(man[clone['byte_offset']+22:clone['byte_offset']+26],original[22:26])
            self.assertEqual(len(metadata['draft_audit']['system_flag_changes']),1)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)


class SystemFlagMergeTests(unittest.TestCase):
    def test_malformed_missing_unaudited_and_noop_overlap_receipts_refuse(self):
        from sdk.system_flags import merge_patch
        from sdk.build import BuildError
        from importer.system_flag_authoring import SystemFlagAuthoringContext
        from test_importer_dialogue_authoring import fixture,ACTOR
        source,baseline=fixture(b'\x50\x02\x3f\0\0\x06town01\x01\x02\x03opaque')
        ctx=SystemFlagAuthoringContext(source);target=ctx.options(ACTOR)['targets'][0];key=target['semantic_id']
        patched,audit=ctx.patch({key:{'index':4095}});expected={key:dict(target,requested_values={'index':4095})}
        self.assertEqual(merge_patch(baseline,baseline,patched,audit,expected,[]),patched)
        for field,value in (('before_hex','0000'),('after_index',3),('byte_length',1),('source_record_sha256','a'*64)):
            bad=deepcopy(audit);bad[0][field]=value
            with self.assertRaises(BuildError):merge_patch(baseline,baseline,patched,bad,expected,[])
        with self.assertRaises(BuildError):merge_patch(baseline,baseline,patched,[],expected,[])
        extra=bytearray(patched);extra[-1]^=1
        with self.assertRaises(BuildError):merge_patch(baseline,baseline,bytes(extra),audit,expected,[])
        noop={key:dict(target,requested_values=target['values'])}
        with self.assertRaises(BuildError):merge_patch(baseline,baseline,baseline,[],noop,[{'decoded_byte_offset':target['decoded_byte_offset'],'byte_length':1}])


if __name__=='__main__':unittest.main()

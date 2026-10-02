"""Atomic decoration groups preserve shared transforms and encoded source limits."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from importer.core import ImportError
from importer.environment_authoring import patch_environment_overrides
from sdk.project import ProjectService, ProjectError
from sdk.environment_group import review, apply
from test_project_workflow import synthetic_scene

SCENE = 'scene://fixture'
def identity(cell):
    return f'environment://fixture/field-map/decorations/{cell:05d}'
IDS = [identity(129), identity(258)]

def source_map():
    source = bytearray(0x12000)
    struct.pack_into('<3h', source, 4 * 32, 10, 20, 30)
    struct.pack_into('<3H', source, 4 * 32 + 8, 100, 200, 300)
    for cell in (129, 258, 387):
        struct.pack_into('<H', source, 0x8000 + cell * 2, 0x2004)
    return bytes(source)

class EnvironmentGroupTests(unittest.TestCase):
    def project(self, directory):
        project = ProjectService(Path(directory))
        project.import_metadata(synthetic_scene())
        return project

    def apply_review(self, project, report):
        apply(project, dict(type='apply_environment_group', entity_id=SCENE, entity_ids=report['entity_ids'], delta=report['delta'], review_key=report['review_key']))

    def test_common_offset_atomic_history_and_preserved_components(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map(); source_hash = sha256(source).hexdigest()
            with patch.object(ProjectService, '_environment_source', return_value=source):
                binding = dict(source_sha256=source_hash, edits=[dict(record_index=4, offset=dict(x=40,z=60,y=50))], instances=[dict(cell_index=129, offset=dict(x=70,y=80), rotation_psx=dict(y=777)), dict(cell_index=387, offset=dict(z=120))])
                p.command(dict(type='set_environment_transforms', entity_id=SCENE, value=binding))
                p.command(dict(type='set_collision_walls', entity_id=SCENE, value=dict(source_sha256=source_hash, edits=[dict(row=1,column=0,quadrant=0,blocked=True)])))
                p.save(); before = deepcopy(p.overrides); depth = len(p.undo_stack)
                r = review(p, SCENE, IDS[::-1], dict(x=15,z=-25))
                self.assertEqual(r['entity_ids'], IDS); self.assertEqual(r['affected_count'], 2)
                self.assertEqual(r['targets'][0]['retail'], dict(x=202,z=162))
                self.assertEqual(r['targets'][0]['current'], dict(x=262,z=132))
                self.assertEqual(r['targets'][0]['proposed'], dict(x=277,z=107))
                self.assertEqual(p.overrides,before); self.assertEqual(len(p.undo_stack),depth)
                self.apply_review(p,r); self.assertEqual(len(p.undo_stack),depth+1)
                edited = p.overrides[SCENE]['Environment']
                self.assertEqual(edited['edits'],binding['edits'])
                self.assertEqual(edited['instances'][0], dict(cell_index=129, offset=dict(x=85,y=80,z=85),rotation_psx=dict(y=777)))
                self.assertEqual(edited['instances'][2],binding['instances'][1])
                self.assertEqual(p.overrides[SCENE]['Collision'],before[SCENE]['Collision'])
                changed,_ = patch_environment_overrides(source,edited)
                self.assertEqual(changed[0x4000:0x8000],source[0x4000:0x8000])
                p.undo(); self.assertEqual(p.overrides,before); p.redo()
                reopened=ProjectService.open(p.save()); self.assertEqual(reopened.overrides,p.overrides)
                noop=review(p,SCENE,IDS,dict(x=0,z=0)); self.assertFalse(noop['project_change'])
                depth=len(p.undo_stack);self.apply_review(p,noop);self.assertEqual(len(p.undo_stack),depth)

    def test_restore_inherited_axes_removes_instances_and_clear_is_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.project(directory);source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                r=review(p,SCENE,IDS,dict(x=20,z=-10));self.apply_review(p,r)
                r=review(p,SCENE,IDS,dict(x=-20,z=10));self.assertEqual(r['value']['instances'],[])
                self.apply_review(p,r);self.assertEqual(p.overrides,{})
                p.undo();self.assertEqual(len(p.overrides[SCENE]['Environment']['instances']),2)
                p.redo();depth=len(p.undo_stack)
                r=review(p,SCENE,IDS,dict(x=0,z=0));self.assertFalse(r['project_change']);self.apply_review(p,r);self.assertEqual(len(p.undo_stack),depth)

    def test_zero_offset_preserves_redundant_axes_and_instance_order(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.project(directory);source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                binding=dict(source_sha256=sha256(source).hexdigest(),edits=[dict(record_index=4,offset=dict(x=40))],instances=[dict(cell_index=258,offset=dict(z=90)),dict(cell_index=129,offset=dict(x=40),rotation_psx=dict(y=777))])
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=binding))
                p.save();before=deepcopy(p.overrides);depth=len(p.undo_stack)
                r=review(p,SCENE,IDS,dict(x=0,z=0))
                self.assertEqual(r['value'],binding);self.assertFalse(r['project_change']);self.assertEqual(r['affected_count'],0)
                self.apply_review(p,r)
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth);self.assertFalse(p.dirty)

    def test_invalid_selection_offsets_and_unsupported_source_have_no_history(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.project(directory);source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                for ids in [IDS[:1],IDS*2,IDS+[identity(387)]*127,[identity(129),identity(16384)],[IDS[0],'environment://other/field-map/decorations/00258'],[IDS[0], 'environment://fixture/field-map/decorations/258'],[IDS[0],identity(0)]]:
                    with self.assertRaises(ProjectError):review(p,SCENE,ids,dict(x=1,z=1))
                for delta in [dict(x=True,z=0),dict(x=1.0,z=0),dict(x=65536,z=0),dict(x=32768,z=0),dict(x=0,z=-32768),dict(x=0,z=0,y=0)]:
                    with self.assertRaises(ProjectError):review(p,SCENE,IDS,delta)
                p.mode='live'
                with self.assertRaises(ProjectError):review(p,SCENE,IDS,dict(x=1,z=1))
                p.mode='edit';p.active_scene=None
                with self.assertRaises(ProjectError):review(p,SCENE,IDS,dict(x=1,z=1))
            p.active_scene=SCENE
            unsupported=bytearray(source);struct.pack_into('<H',unsupported,4*32+18,4)
            with patch.object(p,'_environment_source',return_value=bytes(unsupported)):
                with self.assertRaises(ProjectError):review(p,SCENE,IDS,dict(x=1,z=1))
            self.assertEqual(p.undo_stack,[]);self.assertEqual(p.overrides,{})

    def test_complete_merged_capacity_rejects_and_stale_key_never_applies(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.project(directory);source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                r=review(p,SCENE,IDS,dict(x=1,z=2));p.name='Changed'
                with self.assertRaises(ProjectError):self.apply_review(p,r)
                r=review(p,SCENE,IDS,dict(x=1,z=2))
                with self.assertRaises(ProjectError):apply(p,dict(type='apply_environment_group',entity_id=SCENE,entity_ids=IDS,delta=dict(x=2,z=2),review_key=r['review_key']))
                with self.assertRaises(ProjectError):apply(p,dict(type='apply_environment_group',entity_id=SCENE,entity_ids=IDS,delta=r['delta'],review_key=r['review_key'],extra=True))
            full=bytearray(source)
            for record in range(5,512):full[record*32+31]=1
            with patch.object(p,'_environment_source',return_value=bytes(full)):
                with self.assertRaisesRegex(ImportError,'No unused'):review(p,SCENE,IDS,dict(x=1,z=1))
            full[5*32:7*32]=bytes(64)
            bounded=bytes(full)
            with patch.object(p,'_environment_source',return_value=bounded):
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=dict(source_sha256=sha256(bounded).hexdigest(),instances=[dict(cell_index=387,offset=dict(x=100))])))
                before=deepcopy(p.overrides);depth=len(p.undo_stack)
                with self.assertRaisesRegex(ImportError,'No unused'):review(p,SCENE,IDS,dict(x=1,z=1))
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)
                p.undo()
            p.undo_stack.clear();p.redo_stack.clear()
            def drift(scene):p.name='Drifted';return source
            with patch.object(p,'_environment_source',side_effect=drift):
                with self.assertRaisesRegex(ProjectError,'changed while'):review(p,SCENE,IDS,dict(x=1,z=1))
            self.assertEqual(p.undo_stack,[]);self.assertEqual(p.overrides,{})

if __name__=='__main__':unittest.main()

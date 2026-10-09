"""Static scenery layout contracts, source limits and atomic history."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from importer.core import ImportError
from sdk.project import ProjectService, ProjectError
from sdk.environment_layout import review, apply
from test_environment_group import SCENE, IDS, identity, source_map
from test_project_workflow import synthetic_scene


class EnvironmentLayoutTests(unittest.TestCase):
    def project(self, directory):
        project = ProjectService(Path(directory))
        project.import_metadata(synthetic_scene())
        return project

    def apply_review(self, project, report):
        apply(project, dict(type='apply_environment_layout', entity_id=SCENE,
                            entity_ids=report['entity_ids'], operation=report['operation'], review_key=report['review_key']))

    def test_alignment_preserves_shared_axes_rotation_collision_and_atomic_history(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map(); source_hash = sha256(source).hexdigest()
            with patch.object(ProjectService, '_environment_source', return_value=source):
                binding = dict(source_sha256=source_hash, edits=[dict(record_index=4, offset=dict(x=40,y=50,z=60))],
                               instances=[dict(cell_index=129, offset=dict(x=70,y=80), rotation_psx=dict(y=777)),
                                          dict(cell_index=387, offset=dict(z=120))])
                p.command(dict(type='set_environment_transforms', entity_id=SCENE, value=binding))
                p.command(dict(type='set_collision_walls', entity_id=SCENE, value=dict(source_sha256=source_hash,
                               edits=[dict(row=1,column=0,quadrant=0,blocked=True)])))
                p.save(); before = deepcopy(p.overrides); depth = len(p.undo_stack)
                r = review(p, SCENE, IDS[::-1], dict(kind='align',axis='x',anchor=IDS[0]))
                self.assertEqual(r['schema_version'], 'legaia.environment-layout-review.v1')
                self.assertEqual(r['entity_ids'], IDS); self.assertEqual(r['affected_count'], 1)
                self.assertEqual([t['proposed']['x'] for t in r['targets']], [262,262])
                self.assertEqual([t['proposed']['z'] for t in r['targets']], [132,260])
                self.assertEqual(p.overrides, before); self.assertEqual(len(p.undo_stack), depth)
                self.apply_review(p, r); self.assertEqual(len(p.undo_stack), depth+1)
                edited = p.overrides[SCENE]['Environment']
                self.assertEqual(edited['edits'], binding['edits'])
                self.assertEqual(edited['instances'][0], binding['instances'][0])
                self.assertEqual(edited['instances'][1], dict(cell_index=258,offset=dict(x=-58)))
                self.assertEqual(edited['instances'][2], binding['instances'][1])
                self.assertEqual(p.overrides[SCENE]['Collision'], before[SCENE]['Collision'])
                p.undo(); self.assertEqual(p.overrides, before); p.redo()
                reopened = ProjectService.open(p.save()); self.assertEqual(reopened.overrides, p.overrides)

    def test_distribution_integer_half_up_stable_order_and_endpoints(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map()
            with patch.object(p, '_environment_source', return_value=source) as loader:
                # World X values -10, -9, -5: midpoint -7.5 rounds to -7.
                binding = dict(source_sha256=sha256(source).hexdigest(), instances=[
                    dict(cell_index=129,offset=dict(x=-202)), dict(cell_index=258,offset=dict(x=-329)),
                    dict(cell_index=387,offset=dict(x=-453))])
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=binding))
                loader.reset_mock()
                ids = [identity(387), IDS[1], IDS[0]]
                r = review(p, SCENE, ids, dict(kind='distribute',axis='x'))
                self.assertEqual(loader.call_count, 1)
                self.assertEqual([t['proposed']['x'] for t in r['targets']],[-10,-7,-5])
                self.assertEqual([t['proposed']['z'] for t in r['targets']], [162,290,418])
                self.assertEqual(r['affected_count'],1)
                self.assertEqual(r['review_key'], review(p,SCENE,ids[::-1],r['operation'])['review_key'])
                # Equal current coordinates are ordered by canonical ID.
                binding['instances'][1]['offset']['x'] = -330
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=binding))
                tied = review(p,SCENE,ids,dict(kind='distribute',axis='x'))
                self.assertEqual([t['proposed']['x'] for t in tied['targets']],[-10,-7,-5])

    def test_z_alignment_sign_and_inherited_axis_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map()
            with patch.object(p, '_environment_source', return_value=source):
                binding = dict(source_sha256=sha256(source).hexdigest(),instances=[dict(cell_index=129,offset=dict(z=-98))])
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=binding))
                r = review(p,SCENE,IDS,dict(kind='align',axis='z',anchor=IDS[1]))
                self.assertEqual([t['proposed']['z'] for t in r['targets']], [290,290])
                self.assertEqual(r['affected_count'],0)
                binding['instances'].append(dict(cell_index=258,offset=dict(z=158)))
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=binding))
                restored = review(p,SCENE,IDS,dict(kind='align',axis='z',anchor=IDS[1]))
                self.assertEqual(restored['value']['instances'],[dict(cell_index=258,offset=dict(z=158))])
                # Aligning the other endpoint to row-one retail Z creates positive encoded Z.
                p.command(dict(type='clear_environment_transforms',entity_id=SCENE))
                r = review(p,SCENE,IDS,dict(kind='align',axis='z',anchor=IDS[0]))
                self.assertEqual(r['value']['instances'],[dict(cell_index=258,offset=dict(z=158))])
                self.apply_review(p,r)
                r = review(p,SCENE,IDS,dict(kind='align',axis='z',anchor=IDS[1]))
                self.assertFalse(r['project_change'])

    def test_all_noop_preserves_exact_binding_order_and_redundancy(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map()
            with patch.object(p,'_environment_source',return_value=source):
                binding = dict(source_sha256=sha256(source).hexdigest(),edits=[dict(record_index=4,offset=dict(x=40))],
                    instances=[dict(cell_index=258,offset=dict(z=30)),dict(cell_index=129,offset=dict(x=40),rotation_psx=dict(y=777))])
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=binding));p.save()
                before = deepcopy(p.overrides); depth = len(p.undo_stack)
                r = review(p,SCENE,IDS,dict(kind='distribute',axis='x'))
                self.assertEqual(r['value'],binding);self.assertFalse(r['project_change']);self.assertEqual(r['affected_count'],0)
                self.apply_review(p,r);self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth);self.assertFalse(p.dirty)

    def test_invalid_operation_selection_collapsed_span_and_range(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory);source = source_map()
            with patch.object(p,'_environment_source',return_value=source):
                for operation in [None,{},dict(kind='rotate',axis='x'),dict(kind='align',axis='y',anchor=IDS[0]),
                    dict(kind='align',axis='x'),dict(kind='align',axis='x',anchor=[]),dict(kind='align',axis='x',anchor=identity(387)),
                    dict(kind='distribute',axis='x',anchor=IDS[0]),dict(kind='distribute',axis='x',extra=True)]:
                    with self.assertRaises(ProjectError):review(p,SCENE,IDS,operation)
                for ids in [IDS[:1],IDS*2,IDS+[identity(387)]*127,[IDS[0],identity(0)],[IDS[0],'environment://other/field-map/decorations/00258']]:
                    with self.assertRaises(ProjectError):review(p,SCENE,ids,dict(kind='distribute',axis='x'))
                binding = dict(source_sha256=sha256(source).hexdigest(),instances=[dict(cell_index=258,offset=dict(x=-118)),dict(cell_index=387,offset=dict(x=-246))])
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=binding))
                with self.assertRaisesRegex(ProjectError,'interval'):review(p,SCENE,IDS+[identity(387)],dict(kind='distribute',axis='x'))
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=dict(source_sha256=sha256(source).hexdigest(),instances=[dict(cell_index=387,offset=dict(x=32767))])))
                before=deepcopy(p.overrides);depth=len(p.undo_stack)
                with self.assertRaisesRegex(ProjectError,'signed'):review(p,SCENE,[IDS[0],identity(387)],dict(kind='align',axis='x',anchor=identity(387)))
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)

    def test_stale_operation_source_context_and_exact_apply_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.project(directory);source=source_map()
            with patch.object(p,'_environment_source',return_value=source):
                r=review(p,SCENE,IDS,dict(kind='align',axis='x',anchor=IDS[0]));p.name='Changed'
                with self.assertRaises(ProjectError):self.apply_review(p,r)
                r=review(p,SCENE,IDS,dict(kind='align',axis='x',anchor=IDS[0]))
                command=dict(type='apply_environment_layout',entity_id=SCENE,entity_ids=IDS,operation=r['operation'],review_key=r['review_key'])
                with self.assertRaises(ProjectError):apply(p,{**command,'operation':dict(kind='align',axis='z',anchor=IDS[0])})
                with self.assertRaises(ProjectError):apply(p,{**command,'type':'other'})
                with self.assertRaises(ProjectError):apply(p,{**command,'extra':True})
            changed=bytearray(source);changed[4*32]=11
            with patch.object(p,'_environment_source',return_value=bytes(changed)):
                with self.assertRaises(ProjectError):self.apply_review(p,r)
            def drift(scene):p.name='Drifted';return source
            with patch.object(p,'_environment_source',side_effect=drift):
                with self.assertRaisesRegex(ProjectError,'changed while'):review(p,SCENE,IDS,dict(kind='distribute',axis='x'))
            self.assertEqual(p.undo_stack,[]);self.assertEqual(p.overrides,{})

    def test_complete_merged_capacity_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.project(directory);source=bytearray(source_map())
            for record in range(5,512):source[record*32+31]=1
            with patch.object(p,'_environment_source',return_value=bytes(source)):
                with self.assertRaisesRegex(ImportError,'No unused'):review(p,SCENE,IDS,dict(kind='align',axis='x',anchor=IDS[0]))
            source[5*32:7*32]=bytes(64);source=bytes(source)
            with patch.object(p,'_environment_source',return_value=source):
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=dict(source_sha256=sha256(source).hexdigest(),instances=[dict(cell_index=387,offset=dict(x=100))])))
                before=deepcopy(p.overrides);depth=len(p.undo_stack)
                # Distribution moves only the middle selected target, while the unselected cell consumes another slot.
                r=review(p,SCENE,IDS,dict(kind='align',axis='x',anchor=IDS[0]))
                self.assertEqual(r['affected_count'],1)
                # Group includes all three and requires two changed copies plus the existing override.
                with self.assertRaisesRegex(ImportError,'No unused'):review(p,SCENE,IDS+[identity(387)],dict(kind='align',axis='x',anchor=identity(387)))
                self.assertEqual(p.overrides,before);self.assertEqual(len(p.undo_stack),depth)


    def test_scale_spacing_mirror_exact_coordinates_preserve_layers_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            p = self.project(directory); source = source_map(); ids = IDS + [identity(387)]
            positions = [(0, 0), (-3, 3), (3, -3)]
            entries = []
            for cell, (x, z) in zip((129, 258, 387), positions):
                entries.append(dict(cell_index=cell, offset=dict(x=x-(cell%128)*128-64, y=17, z=(cell//128)*128+64-z), rotation_psx=dict(y=777)))
            with patch.object(ProjectService, '_environment_source', return_value=source):
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=dict(source_sha256=sha256(source).hexdigest(),edits=[],instances=entries)))
                before = deepcopy(p._document()); depth = len(p.undo_stack)
                scaled = review(p, SCENE, ids, dict(kind='scale',anchor=ids[0],percent=50))
                self.assertEqual([t['proposed'] for t in scaled['targets']],[dict(x=0,z=0),dict(x=-2,z=2),dict(x=2,z=-2)])
                self.assertEqual(p._document(), before)
                self.apply_review(p,scaled); self.assertEqual(len(p.undo_stack),depth+1)
                for item in p.overrides[SCENE]['Environment']['instances']:
                    self.assertEqual(item['offset']['y'],17);self.assertEqual(item['rotation_psx'],dict(y=777))
                p.undo();self.assertEqual(p._document(),before);p.redo();p.save();self.assertEqual(ProjectService.open(p.root)._document(),p._document());p.undo()
                mirrored = review(p,SCENE,ids,dict(kind='mirror',axis='x',anchor=ids[0]))
                self.assertEqual([t['proposed'] for t in mirrored['targets']],[dict(x=0,z=0),dict(x=3,z=3),dict(x=-3,z=-3)])
                self.apply_review(p,mirrored);p.undo();self.assertEqual(p._document(),before)
                noop=review(p,SCENE,ids,dict(kind='scale',anchor=ids[0],percent=100));self.assertFalse(noop['project_change']);self.assertEqual(noop['affected_count'],0)
                for operation in [dict(kind='scale',anchor=ids[0],percent=True),dict(kind='scale',anchor=ids[0],percent=0),dict(kind='scale',anchor=ids[0],percent=1001),dict(kind='scale',anchor=ids[0],percent=50.5),dict(kind='scale',anchor='foreign',percent=50),dict(kind='scale',anchor=ids[0],percent=50,axis='x'),dict(kind='mirror',anchor=ids[0],axis='y')]:
                    with self.assertRaises(ProjectError):review(p,SCENE,ids,operation)
                self.assertEqual(p._document(),before)

    def test_retail_reset_compensates_shared_offsets_preserving_unselected_and_other_axes(self):
        with tempfile.TemporaryDirectory() as directory:
            p=self.project(directory);source=source_map()
            with patch.object(ProjectService,'_environment_source',return_value=source):
                binding=dict(source_sha256=sha256(source).hexdigest(),edits=[dict(record_index=4,offset=dict(x=40,y=50,z=60))],instances=[dict(cell_index=129,offset=dict(x=70,y=80),rotation_psx=dict(y=777)),dict(cell_index=258,offset=dict(z=100)),dict(cell_index=387,offset=dict(x=900))])
                p.command(dict(type='set_environment_transforms',entity_id=SCENE,value=binding));before=deepcopy(p._document());depth=len(p.undo_stack)
                reset=review(p,SCENE,IDS,dict(kind='reset'));self.assertEqual([r['proposed'] for r in reset['targets']],[dict(x=202,z=162),dict(x=330,z=290)])
                self.assertEqual(p._document(),before);self.apply_review(p,reset);self.assertEqual(len(p.undo_stack),depth+1)
                value=p.overrides[SCENE]['Environment'];self.assertEqual(value['edits'],binding['edits']);self.assertEqual(value['instances'][2],binding['instances'][2])
                self.assertEqual(value['instances'][0],dict(cell_index=129,offset=dict(x=10,y=80,z=30),rotation_psx=dict(y=777)));self.assertEqual(value['instances'][1],dict(cell_index=258,offset=dict(x=10,z=30)))
                repeated=review(p,SCENE,IDS,dict(kind='reset'));self.assertFalse(repeated['project_change']);self.assertEqual(repeated['affected_count'],0)
                p.save();self.assertEqual(ProjectService.open(p.root)._document(),p._document());p.undo();self.assertEqual(p._document(),before);p.redo();p.undo();self.assertEqual(p._document(),before)
                for field in ['axis','anchor','percent']:
                    with self.assertRaises(ProjectError):review(p,SCENE,IDS,dict(kind='reset',**{field:1}))

if __name__ == '__main__':unittest.main()

from copy import deepcopy
from hashlib import sha256
import struct,tempfile,unittest
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.scene_placement_group import layout_review
import test_scene_placement_group as fixtures
from test_scene_placement_group import SCENE,ACTOR,MIXED,IDS,source_map

class MixedLayoutTests(unittest.TestCase):
 def test_alignment_atomic_history_save_noop_and_preservation(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory)
   with patch.object(ProjectService,'_environment_source',return_value=source_map()):
    p.command(dict(type='set_transform',entity_id=ACTOR,position=dict(y=77)))
    before=deepcopy(p.overrides);depth=len(p.undo_stack);op=dict(kind='align',axis='x',anchor_entity_id=ACTOR)
    r=layout_review(p,SCENE,MIXED,op);self.assertEqual(p.overrides,before);self.assertEqual(r['affected_count'],1)
    p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']))
    self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.overrides[ACTOR],before[ACTOR]);after=deepcopy(p.overrides);p.undo();self.assertEqual(p.overrides,before);p.redo();self.assertEqual(p.overrides,after);self.assertEqual(ProjectService.open(p.save()).overrides,after)
    r=layout_review(p,SCENE,MIXED,op);self.assertFalse(r['project_change']);p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=MIXED,operation=op,review_key=r['review_key']));self.assertEqual(len(p.undo_stack),depth+1)
 def test_distribution_grid_endpoints_rejections_and_stale(self):
  with tempfile.TemporaryDirectory() as directory:
   p=fixtures.ScenePlacementGroupTests().project(directory);source=bytearray(source_map());struct.pack_into('<h',source,4*32,0)
   with patch.object(p,'_environment_source',return_value=bytes(source)):
    r=layout_review(p,SCENE,MIXED+[IDS[1]],dict(kind='distribute',axis='x'));positions={t['entity_id']:t['proposed']['x'] for t in r['targets']};self.assertEqual(positions,{ACTOR:128,IDS[0]:256,IDS[1]:320})
    for op in (dict(kind='align',axis='y',anchor_entity_id=ACTOR),dict(kind='align',axis='x',anchor_entity_id='other'),dict(kind='distribute',axis='x',extra=1)):
     with self.assertRaises(ProjectError):layout_review(p,SCENE,MIXED,op)
    p.name='Changed'
    with self.assertRaises(ProjectError):p.command(dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=r['entity_ids'],operation=r['operation'],review_key=r['review_key']))
    self.assertEqual(p.overrides,{})
   with patch.object(p,'_environment_source',return_value=source_map()):
    with self.assertRaisesRegex(ProjectError,'grid'):layout_review(p,SCENE,MIXED,dict(kind='align',axis='x',anchor_entity_id=IDS[0]))
    with self.assertRaisesRegex(ProjectError,'grid'):layout_review(p,SCENE,MIXED,dict(kind='distribute',axis='x'))

if __name__=='__main__':unittest.main()

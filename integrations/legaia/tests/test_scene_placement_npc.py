from copy import deepcopy
from pathlib import Path
import tempfile, unittest
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.scene_placement_group import review, layout_review, apply
import test_scene_placement_group as fixtures
ACTOR=fixtures.ACTOR
from test_environment_group import SCENE, IDS, source_map

class MixedNpcPlacementTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.p=fixtures.ScenePlacementGroupTests().project(self.directory.name)
        for i in range(2):self.p.command(dict(type='create_actor_draft',name=f'NPC {i}',donor_entity_id=ACTOR,position=dict(x=256+i*64,z=512)))
        self.ids=list(self.p.actor_drafts);self.p.save()
        self.source=patch.object(ProjectService,'_environment_source',return_value=source_map());self.source.start();self.addCleanup(self.source.stop)
    def test_three_kinds_atomic_undo_redo_persistence_preserves_unselected(self):
        p=self.p;before=deepcopy((p.overrides,p.actor_drafts));imports=deepcopy(p.imports);depth=len(p.undo_stack)
        r=review(p,SCENE,[ACTOR,self.ids[0],IDS[0]],dict(x=64,z=64))
        self.assertEqual(r['schema_version'],'legaia.scene-placement-group-review.v2');npc=next(t for t in r['targets'] if t['kind']=='actor_draft');self.assertIsNone(npc['retail']);self.assertEqual(npc['draft'],before[1][self.ids[0]])
        self.assertEqual((p.overrides,p.actor_drafts),before)
        apply(p,dict(type='apply_scene_placement_group',entity_id=SCENE,entity_ids=r['entity_ids'],delta=r['delta'],review_key=r['review_key']))
        self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.undo_stack[-1]['target'],'scene_placement_batch');self.assertEqual(p.actor_drafts[self.ids[0]]['position'],dict(x=320,z=576));self.assertEqual(p.actor_drafts[self.ids[1]],before[1][self.ids[1]]);self.assertEqual(p.imports,imports)
        after=deepcopy((p.overrides,p.actor_drafts));p.undo();self.assertEqual((p.overrides,p.actor_drafts),before);p.redo();self.assertEqual((p.overrides,p.actor_drafts),after)
        restored=ProjectService.open(p.save());self.assertEqual((restored.overrides,restored.actor_drafts),after)
    def test_whole_degree_rotation_preserves_npc_donor_and_unselected_draft(self):
        p=self.p;before=deepcopy(p.actor_drafts);depth=len(p.undo_stack)
        op=dict(kind='rotate_angle',anchor_entity_id=ACTOR,angle_degrees=45)
        r=layout_review(p,SCENE,[ACTOR,self.ids[0],IDS[0]],op)
        npc=next(t for t in r['targets'] if t['entity_id']==self.ids[0]);self.assertEqual(npc['proposed'],dict(x=64,z=512))
        apply(p,dict(type='apply_scene_placement_layout',entity_id=SCENE,entity_ids=r['entity_ids'],operation=op,review_key=r['review_key']))
        self.assertEqual(len(p.undo_stack),depth+1);self.assertEqual(p.actor_drafts[self.ids[0]],dict(before[self.ids[0]],position=npc['proposed']));self.assertEqual(p.actor_drafts[self.ids[1]],before[self.ids[1]])
        p.undo();self.assertEqual(p.actor_drafts,before);p.redo();self.assertEqual(ProjectService.open(p.save()).actor_drafts,p.actor_drafts)

    def test_npc_anchor_layout_and_noop_preserve_redo(self):
        p=self.p;members=[ACTOR,self.ids[0]]
        for operation in (dict(kind='align',axis='x',anchor_entity_id=self.ids[0]),dict(kind='rotate',quarter_turns=1,anchor_entity_id=self.ids[0]),dict(kind='mirror',axis='x',anchor_entity_id=self.ids[0])):
            r=layout_review(p,SCENE,members,operation)
            anchor=next(t for t in r['targets'] if t['entity_id']==self.ids[0])
            self.assertEqual(anchor['current'],anchor['proposed'])
        r=review(p,SCENE,members,dict(x=64,z=0))
        apply(p,dict(type='apply_scene_placement_group',entity_id=SCENE,entity_ids=r['entity_ids'],delta=r['delta'],review_key=r['review_key']))
        p.undo();before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        r=review(p,SCENE,members,dict(x=0,z=0));self.assertFalse(r['project_change'])
        apply(p,dict(type='apply_scene_placement_group',entity_id=SCENE,entity_ids=r['entity_ids'],delta=r['delta'],review_key=r['review_key']))
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
    def test_two_kind_pairs_native_layout_and_reset_bounds_stale_reject(self):
        p=self.p
        for members in ([ACTOR,self.ids[0]],[self.ids[0],IDS[0]]):
            r=review(p,SCENE,members,dict(x=64,z=0));self.assertEqual(len(r['targets']),2)
        r=layout_review(p,SCENE,[ACTOR,self.ids[0],IDS[0]],dict(kind='scale',anchor_entity_id=ACTOR,percent=50))
        self.assertTrue(all(t['proposed']['x']%64==0 and t['proposed']['z']%64==0 for t in r['targets'] if t['kind']!='decoration'))
        before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        with self.assertRaisesRegex(ProjectError,'no retail'):layout_review(p,SCENE,[self.ids[0],IDS[0]],dict(kind='reset'))
        with self.assertRaises(ProjectError):review(p,SCENE,[ACTOR,self.ids[0]],dict(x=16320,z=0))
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),before)
        r=review(p,SCENE,[ACTOR,self.ids[0]],dict(x=64,z=0));p.command(dict(type='rename_actor_draft',entity_id=self.ids[0],name='Changed'));before=deepcopy((p._document(),p.undo_stack))
        with self.assertRaises(ProjectError):apply(p,dict(type='apply_scene_placement_group',entity_id=SCENE,entity_ids=r['entity_ids'],delta=r['delta'],review_key=r['review_key']))
        self.assertEqual((p._document(),p.undo_stack),before)

if __name__=='__main__':unittest.main()

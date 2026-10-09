from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService
from sdk.build import authored_state_key
from test_project_appearance import appearance_scene


class AnimationUsage(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.p=ProjectService(Path(directory.name));self.document=appearance_scene();self.p.import_metadata(self.document)
        self.actor,self.donor=[a['semantic_id'] for a in self.document['actors']]

    def test_appearance_history_and_persistence_keep_retail_and_current_separate(self):
        p=self.p;baseline=p.animation_references();self.assertTrue(all(r['imported'] and r['effective'] for r in baseline))
        with patch.object(p,'appearance_options',return_value={'supported':True,'options':[{'donor_entity_id':self.donor}]}):
            p.command({'type':'set_actor_appearance','entity_id':self.actor,'donor_entity_id':self.donor})
        before=deepcopy((p._document(),p.imports,p.undo_stack,p.redo_stack,authored_state_key(p)))
        rows=[r for r in p.state()['animation_references'] if r['source_id']==self.actor]
        self.assertEqual([(r['target_id'],r['imported'],r['effective']) for r in rows],[('animation://fixture/scene-anm/0001',True,False),('animation://fixture/scene-anm/0002',False,True)])
        self.assertEqual(rows[1]['effective_model_id'],'asset://fixture/model/1');self.assertEqual(rows[1]['effective_source']['donor_entity_id'],self.donor)
        self.assertTrue(all(r['runtime_binding']=='not_asserted' for r in rows))
        self.assertEqual((p._document(),p.imports,p.undo_stack,p.redo_stack,authored_state_key(p)),before)
        opened=ProjectService.open(p.save());self.assertEqual(opened.animation_references(),p.animation_references())
        p.undo();self.assertEqual(p.animation_references(),baseline);p.redo();self.assertEqual(p.animation_references(),opened.animation_references())
        held=p.animation_references();p.active_scene=None;self.assertEqual(p.animation_references(),held)
        held[1]['effective_source']['donor_entity_id']='mutated';self.assertNotEqual(p.animation_references(),held)

    def test_draft_uses_retail_appearance_witness_not_authored_source_actor(self):
        p=self.p
        with patch.object(p,'appearance_options',return_value={'supported':True,'options':[{'donor_entity_id':self.donor}]}):
            p.command({'type':'set_actor_appearance','entity_id':self.actor,'donor_entity_id':self.donor})
        p.command({'type':'create_actor_draft','donor_entity_id':self.actor,'position':{'x':128,'z':256},'name':'Resident'})
        identifier=next(iter(p.actor_drafts));row=next(r for r in p.animation_references() if r['source_id']==identifier)
        self.assertEqual(row['kind'],'draft_initial_animation_assignment');self.assertFalse(row['imported']);self.assertTrue(row['effective'])
        self.assertEqual(row['target_id'],'animation://fixture/scene-anm/0001');self.assertEqual(row['effective_model_id'],'asset://fixture/model/0')
        # A qualified draft appearance witness is independent of the script donor.
        p.actor_drafts[identifier]['appearance']={'script_donor_entity_id':self.actor,'donor_entity_id':self.donor}
        row=next(r for r in p.animation_references() if r['source_id']==identifier)
        self.assertEqual(row['target_id'],'animation://fixture/scene-anm/0002');self.assertEqual(row['effective_source']['donor_entity_id'],self.donor)

    def test_metadata_retained_and_unresolved_clips_preserve_scene_ownership(self):
        p=self.p;record='12345678-1234-4123-8123-123456789abc'
        p.overrides[self.actor]={'ActorAllocatedAnimation':{'record_id':record,'scene_id':p.active_scene}}
        rows=[r for r in p.animation_references() if r['source_id']==self.actor]
        retained=rows[1];self.assertEqual(retained['target_id'],'animation://fixture/authored-record/'+record)
        self.assertEqual(retained['effective_source']['record_id'],record);self.assertFalse(retained['imported'])
        # The projection uses recorded identities, not native allocation or playback proof.
        del p.overrides[self.actor]
        other=deepcopy(self.document);other['scene']={'semantic_id':'scene://other','name':'other'}
        for a in other['actors']:a['semantic_id']=a['semantic_id'].replace('scene://fixture','scene://other')
        other['actors'][0]['model_reference']['model_index']=240;other['actors'][1]['placement_fields']['animation_id']=0
        p.import_metadata(other);self.assertEqual(len(p.animation_references()),2)
        self.assertTrue(all(r['scene_id']=='scene://fixture' for r in p.animation_references()))


if __name__=='__main__':unittest.main()

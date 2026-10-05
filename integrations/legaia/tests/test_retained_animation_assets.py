from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from sdk.project import ProjectService, ProjectError
from sdk.retained_animation_assets import records,preview


class RetainedAssetMetadata(unittest.TestCase):
 def setUp(self):
  self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.p=ProjectService(Path(self.temp.name));self.p.active_scene='scene://fixture';self.p.mode='live'
  self.owner='scene://fixture/actors/man-p1/0001';self.record='12345678-1234-4123-8123-123456789abc'
  self.id='animation://fixture/authored-record/'+self.record;self.model='asset://fixture/models/0'
  self.row=dict(record_id=self.record,animation_id=self.id,entity_id=self.owner,channel_owner_entity_id=self.owner,
    model_source_entity_id=self.owner,donor_asset_id=self.model,donor_animation_id='animation://fixture/scene-anm/0001',
    record_sha256='a'*64,frame_count=2,object_count=1,active=False,runtime_assigned=False)
  self.p.overrides[self.p.active_scene]={'AnimationRecords':{'records':[dict(record_id=self.record,donor_record_sha256='b'*64,donor_animation_id=self.row['donor_animation_id'])]}}
 def test_registered_authored_retired_metadata_detached_and_readonly(self):
  before=deepcopy(self.p._document())
  def library(view,*args):
   self.assertIsNot(view,self.p);self.assertEqual(view.mode,'edit');return {'records':[self.row]}
  with patch('sdk.retained_animation_assets.source_key',return_value='c'*64),patch('sdk.animation_allocation.record_library',side_effect=library):
   result=records(self.p);self.assertFalse(result[0]['retained_record']['active'])
   registered=self.p.assets.register_resources(self.p.active_scene,'c'*64,result,[])
   self.assertEqual(registered['records'][0]['layer'],'authored')
   result[0]['retained_record']['entity_id']='changed';self.assertEqual(self.row['entity_id'],self.owner)
  self.assertEqual(self.p.mode,'live');self.assertEqual(before,self.p._document())
 def test_preview_exact_identity_source_and_no_mutation(self):
  with patch('sdk.retained_animation_assets.source_key',return_value='c'*64),patch('sdk.animation_allocation.record_library',return_value={'records':[self.row]}):
   metadata=records(self.p)[0]
  before=deepcopy(self.p._document());animation=dict(semantic_id=self.id);asset=dict(semantic_id=self.model)
  with patch('sdk.retained_animation_assets.source_key',return_value='c'*64),patch('sdk.retained_animation_assets.records',return_value=[metadata]),patch('sdk.animation_allocation.pose_saved_record',return_value=(animation,asset)):
   result,_,view=preview(self.p,self.id,'c'*64);self.assertEqual(result['asset_source'],metadata);self.assertEqual(view.mode,'edit')
   for identity,key in [(self.id,'d'*64),(self.id+'/missing','c'*64)]:
    with self.assertRaises(ProjectError):preview(self.p,identity,key)
   asset['semantic_id']='asset://wrong'
   with self.assertRaises(ProjectError):preview(self.p,self.id,'c'*64)
  self.assertEqual(self.p.mode,'live');self.assertEqual(before,self.p._document())


if __name__=='__main__':unittest.main()

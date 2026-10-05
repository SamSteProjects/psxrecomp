"""Focused retained-clip reference regression; native qualification is separate."""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import unittest

import test_asset_references as source_tests
from sdk.asset_references import assemble
from sdk.allocated_animation_references import bindings
from sdk.project import ProjectError, digest


class RetainedReferenceGraph(unittest.TestCase):
 setUp=source_tests.AssetReferences.setUp
 def test_retained_replaces_only_effective_clip_and_has_inverse_model_edge(self):
  scene=self.p.active_scene;record='12345678-1234-4123-8123-123456789abc';clip=f'animation://fixture/authored-record/{record}'
  self.p.overrides[self.actor]={'ActorAllocatedAnimation':{'scene_id':scene,'record_id':record}}
  proof=dict(record_id=record,record_sha256='b'*64,ledger_sha256='c'*64,bank_sha256='d'*64,model_id=self.model,
             model_source_entity_id=self.actor,channel_owner_entity_id=self.actor,native_record_index=3,native_animation_id=4,frame_count=3,object_count=1)
  item=dict(owner_id=self.actor,animation_id=clip,model_id=self.model,proof=proof,
            assignment_proof={**proof,'assignment_owner_id':self.actor,'assignment_sha256':'e'*64})
  before=deepcopy(self.p._document())
  with patch('sdk.allocated_animation_references.bindings',return_value=[item]):
   actor=assemble(self.p,self.catalog,self.actor)
   kinds={e['kind'] for e in actor['outgoing']}
   self.assertIn('initial_animation_binding',kinds);self.assertNotIn('effective_initial_animation_binding',kinds)
   assigned=next(e for e in actor['outgoing'] if e['kind']=='allocated_initial_animation_binding')
   self.assertEqual(assigned['target_id'],clip);self.assertEqual(assigned['layer'],'effective')
   self.assertEqual(assigned['allocated_animation_evidence'],item['assignment_proof'])
   result=assemble(self.p,self.catalog,clip)
   self.assertEqual(result['incoming'][0]['source_id'],self.actor)
   self.assertEqual(result['outgoing'][0]['target_id'],self.model)
   self.assertEqual(result['outgoing'][0]['layer'],'authored')
   self.assertFalse(next(n for n in result['nodes'] if n['id']==clip)['available'])
   inverse=assemble(self.p,self.catalog,self.model)
   self.assertTrue(any(e['source_id']==clip for e in inverse['incoming']))
  self.assertEqual(self.p._document(),before)
  del self.p.overrides[self.actor]
  self.assertIn('effective_initial_animation_binding',{e['kind'] for e in assemble(self.p,self.catalog,self.actor)['outgoing']})

 def test_unavailable_derived_catalog_does_not_claim_retained_proof(self):
  with patch('sdk.allocated_animation_references.bindings',side_effect=AssertionError('must not verify without catalog')):
   assemble(self.p,dict(source_key=None,records=[]),self.actor)


class RetainedQualification(unittest.TestCase):
 def test_readonly_observation_view_and_mismatch_rejection(self):
  scene='scene://fixture';owner=scene+'/actors/man-p1/0001';record='12345678-1234-4123-8123-123456789abc'
  component=dict(scene_id=scene,record_id=record,record_sha256='a'*64,model_asset_id='asset://fixture/model/0')
  ledger={'records':[record]};project=SimpleNamespace(active_scene='scene://other',mode='live',overrides={scene:{'AnimationRecords':ledger},owner:{'ActorAllocatedAnimation':component}})
  entry=dict(record_id=record,record_sha256='a'*64,donor_asset_id=component['model_asset_id'],model_source_entity_id=owner,channel_owner_entity_id=owner)
  checked=dict(proposed_component=component,record_id=record,animation_id=f'animation://fixture/authored-record/{record}',
               effective_bank_sha256='b'*64,native_record_index=4,native_animation_id=5,frame_count=3,object_count=1)
  before=deepcopy(project.__dict__)
  def qualify(view,*args):
   self.assertIsNot(view,project);self.assertEqual((view.active_scene,view.mode),(scene,'edit'));return deepcopy(checked)
  with patch('sdk.allocated_animation_assignment.validate_binding',return_value=entry),patch('sdk.scene_preview.source_key',return_value='c'*64),patch('sdk.allocated_animation_assignment.review',side_effect=qualify):
   result=bindings(project,scene)
   self.assertEqual(result[0]['proof']['ledger_sha256'],digest(ledger))
   self.assertEqual(result[0]['assignment_proof']['assignment_sha256'],digest(component))
   checked['proposed_component']={**component,'record_sha256':'d'*64}
   with self.assertRaises(ProjectError):bindings(project,scene)
  self.assertEqual(project.__dict__,before)


if __name__=='__main__':unittest.main()

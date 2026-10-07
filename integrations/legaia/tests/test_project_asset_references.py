"""Project-wide derived edges must preserve provenance without mutating editor state."""
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from importer.core import ImportError as RetailImportError
from importer import textures  # Prevent lazy decoder imports from retaining a mocked disc reader.
from sdk.project import ProjectService,ProjectError,digest
from sdk.asset_references import assemble,assemble_project,inspect_project,source_key
from test_project_workflow import synthetic_scene

class ProjectAssetReferences(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.p=ProjectService(Path(self.tmp.name));self.p.disc_path='private-disc.bin'
  self.model='asset://shared/model/0';self.clip='animation://shared/clip/0'
  for name in ['fixture','other']:
   doc=synthetic_scene();doc['scene']={'semantic_id':'scene://'+name,'name':name}
   doc['actors'][0]['semantic_id']='scene://'+name+'/actors/man-p1/0001'
   doc['actors'][0]['model_reference']['asset_semantic_id']=self.model
   doc['assets']['models'][0]['semantic_id']=self.model
   self.p.import_metadata(doc)
  self.p.active_scene='scene://fixture';self.p.selected='scene://fixture/actors/man-p1/0001'
  self.catalogs={}
  for index,scene in enumerate(sorted(self.p.imports)):
   actor=self.p.imports[scene]['actors'][0]['semantic_id']
   self.catalogs[scene]=dict(scene_id=scene,source_key=str(index+1)*64,limitations=['Bounded fixture source'],records=[
    dict(id=self.clip,kind='animation',bindings=[dict(actor_semantic_id=actor,model_asset_semantic_id=self.model,initial_animation_id=2)]),
    dict(id='texture://shared',kind='texture'),
    dict(id='script://'+scene[8:]+'/actor',kind='script',actor_semantic_id=actor,model_selection_references=[{}])])
  self.materials={scene:dict(models=[],unresolved_reference_count=0,limitations=[]) for scene in self.p.imports}
 def test_shared_nodes_have_all_memberships_and_scene_qualified_edges(self):
  before=deepcopy(vars(self.p));report=assemble_project(self.p,self.catalogs,self.clip,self.materials)
  root=next(n for n in report['nodes'] if n['id']==self.clip)
  self.assertEqual(root['scene_ids'],['scene://fixture','scene://other']);self.assertEqual(root['scene_id'],'scene://fixture')
  self.assertEqual(len(report['incoming']),4);self.assertEqual(len(report['outgoing']),2)
  for edge in report['incoming']+report['outgoing']:
   self.assertEqual(edge['source_import_sha256'],digest(self.p.imports[edge['scene_id']]))
   self.assertEqual(edge['source_catalog_key'],self.catalogs[edge['scene_id']]['source_key'])
   self.assertEqual(edge['id'],digest({k:v for k,v in edge.items() if k!='id'}))
  self.assertEqual(report['coverage']['unresolved_reference_count'],2)
  self.assertEqual(report['source_key'],source_key(self.p));report['nodes'][0]['label']='mutated'
  self.assertEqual(before.keys(),vars(self.p).keys())
  self.assertEqual(before['imports'],self.p.imports);self.assertEqual(before['assets'].resource_catalogs,self.p.assets.resource_catalogs)
  # Default v1 and its shape retain their behavior.
  self.assertEqual(assemble(self.p,self.catalogs[self.p.active_scene],self.clip)['schema_version'],'legaia.asset-references.v1')
  self.assertNotIn('scene_ids',assemble(self.p,self.catalogs[self.p.active_scene],self.clip)['nodes'][0])
 def test_scene_navigation_prefers_actual_catalog_over_external_material_candidate(self):
  self.catalogs['scene://fixture']['records']=[r for r in self.catalogs['scene://fixture']['records'] if r['kind']!='texture']
  entry=dict(material_index=0,tpage=0,clut=0,uv_bounds=[0,0,0,0],evidence='static',status='address_match',source_ids=['texture://shared'])
  self.materials['scene://fixture']['models']=[dict(model_id=self.model,source_sha256='a'*64,materials=[entry])]
  report=assemble_project(self.p,self.catalogs,self.model,self.materials)
  texture=next(n for n in report['nodes'] if n['id']=='texture://shared')
  self.assertTrue(texture['available']);self.assertEqual(texture['scene_id'],'scene://other');self.assertEqual(texture['navigable_scene_ids'],['scene://other'])
  self.assertEqual(texture['scene_ids'],['scene://fixture','scene://other'])
 def test_unavailable_scene_explicit_and_imported_edges_still_present(self):
  report=assemble_project(self.p,{'scene://fixture':self.catalogs['scene://fixture']},self.model,
    {'scene://fixture':self.materials['scene://fixture']},{'scene://other':dict(status='unavailable',reason='Unsupported layout')})
  other=next(row for row in report['coverage']['scenes'] if row['scene_id']=='scene://other')
  self.assertEqual(other['status'],'unavailable');self.assertIsNone(other['resource_source_key'])
  self.assertEqual(other['reason'],'Unsupported layout');self.assertEqual(len(report['incoming']),7)
  self.assertEqual(next(n for n in report['nodes'] if n['id']==self.model)['scene_ids'],sorted(self.p.imports))
  with self.assertRaises(ProjectError):assemble_project(self.p,{},self.model)
 def mock_discovery(self,refresh=None,verify=None,material=None):
  return [patch('importer.pipeline._disc_context',return_value=nullcontext()),
   patch('sdk.resources._verify',side_effect=verify or (lambda p,d:None)),
   patch('sdk.resources.refresh_resource_catalog',side_effect=refresh or (lambda p:deepcopy(self.catalogs[p.active_scene]))),
   patch('sdk.material_references.verified_catalog',side_effect=material or (lambda p:deepcopy(self.materials[p.active_scene])))]
 def test_inspection_detaches_every_mutable_field_and_does_not_reuse_parent_caches(self):
  self.p.assets.resource_catalogs={'sentinel':{'records':['keep']}}
  self.p.assets.material_reference_catalogs={'sentinel':{'models':['keep']}}
  before=deepcopy(vars(self.p));events=[]
  def verify(p,d):events.append(('verify',d['scene']['semantic_id']));self.assertIsNot(p,self.p)
  def refresh(p):
   events.append(('decode',p.active_scene));self.assertIsNot(p.assets,self.p.assets)
   self.assertNotIn('sentinel',p.assets.resource_catalogs)
   # Transient decoder changes cannot leak into the active editor.
   p.selected='changed';p.undo_stack.append({'scratch':True})
   return deepcopy(self.catalogs[p.active_scene])
  mocks=self.mock_discovery(refresh=refresh,verify=verify)
  with mocks[0],mocks[1],mocks[2],mocks[3]:report=inspect_project(self.p,self.clip)
  self.assertEqual(events[:2],[('verify','scene://fixture'),('verify','scene://other')])
  for key in ['imports','overrides','actor_drafts','scene_views','selected','undo_stack','active_scene']:
   self.assertEqual(vars(self.p)[key],before[key])
  self.assertEqual(self.p.assets.resource_catalogs,before['assets'].resource_catalogs)
  self.assertEqual(self.p.assets.material_reference_catalogs,before['assets'].material_reference_catalogs)
  self.assertEqual(report['coverage']['resource_scene_id'],'scene://fixture')
 def test_source_verification_failure_precedes_any_decode_and_drift_rejects(self):
  before=deepcopy(self.p._document())
  def persistent_change(view):
   view.audio_bank_overrides['fixture']={'changed':True}
   return deepcopy(self.catalogs[view.active_scene])
  mocks=self.mock_discovery(refresh=persistent_change)
  with mocks[0],mocks[1],mocks[2],mocks[3],self.assertRaisesRegex(ProjectError,'source changed'):inspect_project(self.p,self.clip)
  self.assertEqual(self.p._document(),before)
  def stale(p,d):raise ProjectError('stale source')
  mocks=self.mock_discovery(verify=stale)
  with mocks[0],mocks[1],mocks[2] as decoding,mocks[3]:
   with self.assertRaisesRegex(ProjectError,'stale source'):inspect_project(self.p,self.model)
   self.assertEqual(decoding.call_count,0)
  def drift(p):self.p.disc_path='different-disc.bin';return self.catalogs[p.active_scene]
  mocks=self.mock_discovery(refresh=drift)
  with mocks[0],mocks[1],mocks[2],mocks[3]:
   with self.assertRaisesRegex(ProjectError,'source changed'):inspect_project(self.p,self.model)
 def test_only_expected_import_error_yields_unavailable_scene(self):
  def unavailable(p):
   if p.active_scene=='scene://other':raise RetailImportError('No supported model table')
   return self.catalogs[p.active_scene]
  mocks=self.mock_discovery(refresh=unavailable)
  with mocks[0],mocks[1],mocks[2],mocks[3]:
   self.assertEqual(inspect_project(self.p,self.model)['coverage']['scenes'][1]['status'],'unavailable')
  for failure in [ProjectError('bad data'),ValueError('bad decoder')]:
   def invalid(p):raise failure
   mocks=self.mock_discovery(refresh=invalid)
   with mocks[0],mocks[1],mocks[2],mocks[3]:
    with self.assertRaises(type(failure)):inspect_project(self.p,self.model)
 def test_invalid_catalog_scope_kind_source_and_bounds_reject(self):
  for identity in [None,[], '', 'x'*1025,'asset://missing']:
   with self.assertRaises(ProjectError):assemble_project(self.p,self.catalogs,identity)
  malformed=deepcopy(self.catalogs);malformed['scene://other']['source_key']='invalid'
  with self.assertRaises(ProjectError):assemble_project(self.p,malformed,self.model)
  malformed=deepcopy(self.catalogs);malformed['scene://other']['records'].append(dict(id=self.clip,kind='texture'))
  with self.assertRaises(ProjectError):assemble_project(self.p,malformed,self.model)
  for scene in self.catalogs:
   self.catalogs[scene]['records'] += [dict(id='animation://'+scene[8:]+'/'+str(i),kind='animation',bindings=[dict(actor_semantic_id=self.p.selected,model_asset_semantic_id=self.model,initial_animation_id=2)]) for i in range(2100)]
  with self.assertRaisesRegex(ProjectError,'4096'):assemble_project(self.p,self.catalogs,self.p.selected)
 def test_global_graph_budget_and_response_bytes_are_bounded(self):
  for scene in self.catalogs:
   self.catalogs[scene]['records'] += [dict(id='texture://'+scene[8:]+'/'+str(i),kind='texture') for i in range(8200)]
  with self.assertRaisesRegex(ProjectError,'node limit'):assemble_project(self.p,self.catalogs,self.model)
  self.catalogs['scene://fixture']['records']=[];self.catalogs['scene://other']['records']=[]
  self.catalogs['scene://fixture']['limitations']=['x'*8193]
  with self.assertRaisesRegex(ProjectError,'bounded metadata'):assemble_project(self.p,self.catalogs,self.model)
  material=dict(material_index=0,tpage=0,clut=0,uv_bounds=[0,0,0,0],evidence='x'*(8*1024*1024),status='address_match',source_ids=['texture://outside'])
  self.materials['scene://fixture']['models']=[dict(model_id=self.model,source_sha256='a'*64,materials=[material])]
  self.catalogs['scene://fixture']['limitations']=[]
  with self.assertRaisesRegex(ProjectError,'8 MiB'):assemble_project(self.p,self.catalogs,self.model,self.materials)

 def test_global_edges_and_decoded_accumulation_are_bounded(self):
  actor=self.p.selected
  self.catalogs['scene://fixture']['records']=[dict(id=self.clip,kind='animation',bindings=[dict(actor_semantic_id=actor,model_asset_semantic_id=self.model,initial_animation_id=i) for i in range(32769)])]
  with self.assertRaisesRegex(ProjectError,'edge limit'):assemble_project(self.p,self.catalogs,self.model)
  self.catalogs['scene://fixture']['records']=[]
  self.materials['scene://fixture']['unused_payload']='x'*(32*1024*1024)
  with self.assertRaisesRegex(ProjectError,'32 MiB'):assemble_project(self.p,self.catalogs,self.model,self.materials)
  with self.assertRaisesRegex(ProjectError,'32 MiB'):
   mocks=self.mock_discovery()
   with mocks[0],mocks[1],mocks[2],mocks[3]:inspect_project(self.p,self.model)

if __name__=='__main__' :unittest.main()

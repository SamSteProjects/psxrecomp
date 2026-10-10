import base64
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_model_glb import export
from importer.assets import decode_tmd
from test_importer_assets import model

class WorldModelGlbTests(TestCase):
 def test_exact_native_export_and_source_refusals(self):
  content=model(0x22);identifier='asset://map01/worldmap/models/0000';key='b'*64;sha=sha256(content).hexdigest();native={'decoded_member_sha256':sha};source=dict(tmd_sha256=sha,tmd_base64=base64.b64encode(content).decode(),source_record=native)
  graph={'scene_graph':{'assets':[{'asset_id':identifier,'source_record':native,'preview':{**decode_tmd(content),'textures':[]}}]}}
  request=dict(asset_id=identifier,source_key=key,member_sha256=sha,effective_sha256=sha)
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));held=deepcopy(p._document())
   with patch('sdk.worldmap_model_glb.inspect',return_value=source),patch('sdk.worldmap_model_glb.geometry',return_value=graph),patch('sdk.worldmap_model_glb.state_key',return_value=key):
    result=export(p,request);self.assertEqual(result['native_roundtrip_sha256'],sha);self.assertEqual(result['binding']['source_scene_id'],'worldmap://map01/models');self.assertEqual(result['binding']['profile']['schema_version'],'legaia.model-glb-profile.v6');self.assertEqual(p._document(),held);self.assertEqual(p.undo_stack,[])
    for bad in [{**request,'extra':1},{k:v for k,v in request.items() if k!='effective_sha256'},{**request,'effective_sha256':'0'*64}]:
     with self.assertRaises(ProjectError):export(p,bad)
    foreign=deepcopy(graph);foreign['scene_graph']['assets'][0]['source_record']={'foreign':True}
    with patch('sdk.worldmap_model_glb.geometry',return_value=foreign),self.assertRaises(ProjectError):export(p,request)
    with patch('sdk.worldmap_model_glb.state_key',return_value='0'*64),self.assertRaises(ProjectError):export(p,request)
    with patch('sdk.worldmap_model_glb.import_model_glb',return_value=(content+b'x',{})),self.assertRaises(ProjectError):export(p,request)
    p.mode='live'
    with self.assertRaises(ProjectError):export(p,request)

 def test_import_retains_input_with_native_history_and_stale_refusals(self):
  from sdk.worldmap_model_glb import review_import,apply_import
  from importer.model_glb import _read_glb,_write_glb
  from sdk.model_glb_sources import library,library_download,read_source
  content=model(0x22);identifier='asset://map01/worldmap/models/0000';key='b'*64;sha=sha256(content).hexdigest();native={'decoded_member_sha256':sha}
  source=dict(tmd_sha256=sha,tmd_base64=base64.b64encode(content).decode(),source_record=native)
  graph={'scene_graph':{'assets':[{'asset_id':identifier,'source_record':native,'preview':{**decode_tmd(content),'textures':[]}}]}}
  context=dict(asset_id=identifier,source_key=key,member_sha256=sha,effective_sha256=sha)
  with TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path='fixture'
   with patch('sdk.worldmap_model_glb.inspect',return_value=source),patch('sdk.worldmap_model_glb.geometry',return_value=graph),patch('sdk.worldmap_model_glb.state_key',return_value=key),patch('sdk.worldmap_model_binding.source',return_value=(content,native)),patch('sdk.worldmap_model_replacement.source',return_value=(content,native)),patch('sdk.worldmap_model_replacement.state_key',return_value=key),patch('sdk.worldmap_authoring.state_key',return_value=key):
    exported=export(p,context);doc,binary=_read_glb(base64.b64decode(exported['glb_base64']));doc['nodes'][0]['translation']=[1,0,0];glb=_write_glb(doc,binary)
    request={**context,'binding':exported['binding'],'glb_base64':base64.b64encode(glb).decode()};held=deepcopy(p._document());report=review_import(p,request);self.assertEqual(p._document(),held);self.assertTrue(report['native_review']['changed'])
    for bad in [{**request,'extra':True},{**request,'binding':{**exported['binding'],'effective_sha256':'0'*64}},{**request,'glb_base64':'!bad'}]:
     with self.assertRaises(ProjectError):review_import(p,bad)
    with self.assertRaises(ProjectError):apply_import(p,request,'0'*64)
    from test_model_primitive_workflow import http_server
    with http_server(p) as (_,post):
     status,body=post('/api/worldmap-model-glb-review',request);self.assertEqual(status,200);self.assertEqual(body,report)
    apply_import(p,request,report['review_key']);candidate=base64.b64decode(report['candidate_base64']);self.assertEqual(p.read_model_replacement(identifier,p.model_overrides[identifier]),candidate);self.assertEqual(len(p.undo_stack),1);self.assertEqual(p.undo_stack[0]['target'],'model_source_import')
    record=next(iter(p.model_sources.values()));self.assertEqual(read_source(p,record),glb);self.assertEqual(record['scene_id'],'worldmap://map01/models');self.assertEqual(record['binding'],exported['binding'])
    catalog=library(p,str(p.root));download=library_download(p,record['receipt_key'],str(p.root),catalog['library_key']);self.assertEqual(base64.b64decode(download['glb_base64']),glb)
    p.undo();self.assertEqual(p.model_sources,{});self.assertEqual(p.model_overrides,{});p.redo();self.assertEqual(p.read_model_replacement(identifier,p.model_overrides[identifier]),candidate);self.assertEqual(read_source(p,record),glb)
    reopened=ProjectService.open(p.save());self.assertEqual(reopened.model_sources,p.model_sources);self.assertEqual(reopened.model_overrides,p.model_overrides)
    with self.assertRaises(Exception):apply_import(p,request,report['review_key'])

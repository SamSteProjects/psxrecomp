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

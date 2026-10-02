"""Group placement HTTP and private retail normal-Build acceptance."""
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import json,os,tempfile,threading,unittest,zipfile
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from sdk.project import ProjectService
from sdk.server import EditorServer
from sdk.environment_group import review
from importer.environment_authoring import patch_environment_overrides
from importer.collision_authoring import patch_collision_walls
from test_project_workflow import synthetic_scene
from test_environment_group import source_map,IDS,SCENE

class GroupHttp(unittest.TestCase):
 def test_review_fields_and_atomic_apply_stale_guards(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));p.import_metadata(synthetic_scene());saved_path=p.save()
   with patch.object(ProjectService,'_environment_source',return_value=source_map()):
    server=EditorServer(('127.0.0.1',0),p);thread=threading.Thread(target=server.serve_forever);thread.start()
    try:
     def post(route,body):
      request=Request(f'http://127.0.0.1:{server.server_port}{route}',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
      try:
       with urlopen(request,timeout=10) as r:return r.status,json.load(r)
      except HTTPError as e:
       with e:return e.code,json.load(e)
     body=dict(entity_id=SCENE,entity_ids=IDS,delta=dict(x=64,z=-32));before=deepcopy(p._document());saved=saved_path.read_bytes()
     for bad in [{}, {**body,'extra':True},{**body,'entity_ids':IDS[:1]},{**body,'delta':dict(x=True,z=0)}]:self.assertEqual(post('/api/environment-group-review',bad)[0],400)
     code,r=post('/api/environment-group-review',body);self.assertEqual(code,200,r);self.assertEqual(p._document(),before);self.assertEqual(p.undo_stack,[])
     command={**body,'type':'apply_environment_group','review_key':r['review_key']};self.assertEqual(post('/api/command',command)[0],200);self.assertEqual(len(p.undo_stack),1)
     after=deepcopy(p._document());self.assertEqual(post('/api/command',command)[0],400);self.assertEqual(p._document(),after);self.assertEqual(saved_path.read_bytes(),saved)
     self.assertEqual(post('/api/undo',{})[0],200);self.assertEqual(p._document(),before);self.assertEqual(post('/api/redo',{})[0],200);self.assertEqual(p._document(),after)
    finally:server.shutdown();server.server_close();thread.join(timeout=5)
    self.assertFalse(thread.is_alive())

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class GroupRetail(unittest.TestCase):
 def test_shared_source_group_preview_reopen_and_full_map_zip(self):
  from importer.pipeline import import_scene,_disc_context
  from importer.environment import load_environment_preview_catalog
  from sdk.scene_preview import environment_effective_transforms
  from sdk.build import build_project
  with tempfile.TemporaryDirectory() as d,_disc_context(os.environ['LEGAIA_DISC_BIN']):
   p=ProjectService(Path(d));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));scene=p.active_scene;source=p._environment_source(scene);key=sha256(source).hexdigest()
   p.command(dict(type='set_environment_transforms',entity_id=scene,value=dict(source_sha256=key,edits=[dict(record_index=194,offset=dict(x=64),rotation_psx=dict(y=64))])))
   p.command(dict(type='set_collision_walls',entity_id=scene,value=dict(source_sha256=key,edits=[dict(row=1,column=0,quadrant=0,blocked=not bool(source[0x4080]&16))])))
   p.save();before=deepcopy(p.overrides);ids=[f'environment://town01/field-map/decorations/{cell:05d}' for cell in (1833,2089)];r=review(p,scene,ids,dict(x=128,z=64));p.command(dict(type='apply_environment_group',entity_id=scene,entity_ids=ids,delta=r['delta'],review_key=r['review_key']));p.undo();self.assertEqual(p.overrides,before);p.redo();p=ProjectService.open(p.save())
   metadata=load_environment_preview_catalog(p.disc_path,'town01').metadata;transforms=environment_effective_transforms(p,metadata)
   for row in r['targets']:
    self.assertEqual({a:transforms[row['entity_id']]['position'][a] for a in ('x','z')},row['proposed']);self.assertEqual(transforms[row['entity_id']]['rotation_psx']['y'],64)
   build=build_project(p);audit=json.loads(Path(build['audit']).read_bytes());self.assertEqual(len(audit['overlays']),1);file=audit['overlays'][0]['file'];expected,_=patch_environment_overrides(source,p.overrides[scene]['Environment']);wall_data,walls=patch_collision_walls(source,key,p.overrides[scene]['Collision']['edits']);expected=bytearray(expected)
   for bit in walls:expected[bit['byte_offset']]=wall_data[bit['byte_offset']]
   with zipfile.ZipFile(build['path']) as archive:self.assertEqual(archive.read(file),bytes(expected))
   self.assertEqual(len(expected),0x12000);self.assertTrue(all((a&15)==(b&15) for a,b in zip(source[0x4000:0x8000],expected[0x4000:0x8000])))

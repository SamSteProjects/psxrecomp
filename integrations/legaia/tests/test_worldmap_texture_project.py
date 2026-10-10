"""World TIM source ownership, content integrity and persistent project history."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
import test_worldmap_texture_authoring as adapter_fixture

class WorldTextureProjectTests(TestCase):
 def test_history_persistence_and_source_refusal(self):
  fixture=adapter_fixture.WorldTextureAdapterTests();fixture.setUp();context=fixture.load()
  identifier='texture://map01/kingdom/0000'
  with TemporaryDirectory() as raw, fixture.scope('importer.texture_authoring._disc_context'), patch('importer.worldmap_texture_authoring.load_worldmap_texture_authoring_context',return_value=context):
   project=ProjectService(Path(raw));project.disc_path='fixture'
   original=context.original_tim(identifier);changed=bytearray(original);changed[-1]^=1;changed=bytes(changed)
   project.set_texture_replacement(identifier,changed)
   binding=deepcopy(project.texture_overrides[identifier])
   self.assertEqual(binding['source_scene_id'],'worldmap://map01/textures')
   self.assertEqual(binding['source_sha256'],sha256(original).hexdigest())
   self.assertEqual(binding['source_disc_sha256'],'a'*64)
   self.assertEqual(project.imports,{})
   self.assertEqual(project.read_texture_replacement(binding),changed)
   self.assertEqual(project.authored_assets()[0]['id'],identifier)
   project.undo();self.assertEqual(project.texture_overrides,{})
   project.redo();reopened=ProjectService.open(project.save())
   self.assertEqual(reopened.texture_overrides,project.texture_overrides)
   self.assertEqual(reopened._texture_context(identifier).original_tim(identifier),original)
   before=deepcopy(reopened.texture_overrides)
   with self.assertRaises(ProjectError):reopened.set_texture_replacement(identifier,changed,image_allocation=True)
   self.assertEqual(before,reopened.texture_overrides)
   reopened.texture_overrides[identifier]['source_sha256']='0'*64
   with self.assertRaises(ProjectError):reopened._texture_context(identifier)
   reopened.texture_overrides=before
   reopened.mode='live'
   with self.assertRaises(ProjectError):reopened.set_texture_replacement(identifier,changed)
   reopened.mode='edit'
   reopened.command({'type':'clear_texture_replacement','asset_id':identifier})
   self.assertEqual(reopened.texture_overrides,{})
   reopened.undo();self.assertEqual(reopened.texture_overrides,before)
   path=Path(raw)/'Authored'/'Textures'/(binding['asset_sha256']+'.tim')
   path.write_bytes(bytes(len(changed)))
   with self.assertRaises(ProjectError):reopened.save()

 def test_invalid_native_owner_bindings(self):
  with TemporaryDirectory() as raw:
   project=ProjectService(Path(raw))
   good=dict(asset_sha256='a'*64,byte_length=50,format='tim',source_scene_id='worldmap://map01/textures',source_disc_sha256='b'*64,source_sha256='c'*64)
   project._validate_texture_binding(good)
   for key,value in [('source_scene_id',[]),('source_disc_sha256','x'*64),('source_sha256',None),('format','tim-image-layout-v1')]:
    bad={**good,key:value}
    with self.subTest(key=key),self.assertRaises(ProjectError):project._validate_texture_binding(bad)

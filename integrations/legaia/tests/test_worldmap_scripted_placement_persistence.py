from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch

from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_scripted_placement_binding import COMPONENT,owner,read_base,base_path,compose
from sdk.worldmap_scripted_placement_allocation import source,review
from test_worldmap_scripted_placement_allocation import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class ScriptedPlacementPersistenceTests(TestCase):
    def test_two_http_applies_undo_redo_save_open_and_tampered_retained_base(self):
        raw,fallback,man,floor,requests=fixture()
        provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(man[2:34]).hexdigest())
        def inputs(project,scene,key,include_scripted=True):
            current,_=compose(project,scene,provenance,raw,fallback,man,man,floor) if include_scripted else (raw,[])
            return raw,provenance,floor,current,[],fallback,man,man,{},[]
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;project.import_metadata(doc)
            held=deepcopy(project._document())
            with patch('sdk.worldmap_scripted_placement_allocation._inputs',side_effect=inputs):
                key=state_key(project);first=review(project,'map01',key,requests)
                command=dict(type='allocate_scripted_worldmap_placements',scene='map01',source_key=key,requests=requests,review_key=first['review_key'])
                with http_server(project) as (_,post):
                    self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400)
                    self.assertEqual(project._document(),held)
                    self.assertFalse((Path(root)/'Authored'/'WorldMapBases').exists())
                    self.assertEqual(post('/api/command',command)[0],200)
                    self.assertEqual(post('/api/command',command)[0],400)
                binding=project.overrides[owner('map01')][COMPONENT]
                self.assertEqual(read_base(project,binding),raw)
                self.assertEqual(b64decode(source(project,'map01',state_key(project))['current_map_base64']),b64decode(first['proposed_map_base64']))
                after_first=deepcopy(project._document())
                with self.assertRaisesRegex(ProjectError,'creation budget'):
                    review(project,'map01',state_key(project),requests*32)
                self.assertEqual(project._document(),after_first)
                second_request=deepcopy(requests[0]);second_request.update(placement_id='placement://authored/66666666-6666-4666-8666-666666666666',donor_cell=200,target_cell=201,record_index=5)
                key=state_key(project);second=review(project,'map01',key,[second_request])
                project.command(dict(type='allocate_scripted_worldmap_placements',scene='map01',source_key=key,requests=[second_request],review_key=second['review_key']))
                after_second=deepcopy(project._document())
                self.assertEqual(len(project.overrides[owner('map01')][COMPONENT]['operations']),2)
                project.undo();self.assertEqual(project._document(),after_first)
                project.undo();self.assertEqual(project._document(),held)
                project.redo();self.assertEqual(project._document(),after_first)
                project.redo();self.assertEqual(project._document(),after_second)
                path=project.save();reopened=ProjectService.open(path)
                self.assertEqual(reopened._document(),after_second)
                self.assertEqual(b64decode(source(reopened,'map01',state_key(reopened))['current_map_base64']),b64decode(second['proposed_map_base64']))
                self.assertEqual(source(reopened,'map01',state_key(reopened))['remaining_creation_capacity'],30)
                self.assertTrue(any(r['id']==owner('map01') for r in reopened.authored_assets()))
                native=base_path(reopened,reopened.overrides[owner('map01')][COMPONENT]);altered=bytearray(native.read_bytes());altered[0]^=1;native.write_bytes(altered)
                with self.assertRaisesRegex(ProjectError,'base changed'):ProjectService.open(path)

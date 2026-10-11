from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct,tempfile
from unittest import TestCase
from unittest.mock import patch
from urllib.request import urlopen
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_footprint import inspect
from test_worldmap_placement_allocation import fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


def footprint_fixture(corrected=False):
    raw,floor=fixture();data=bytearray(raw)
    struct.pack_into('<2b',data,9*32+6,1,0)
    struct.pack_into('<2b',data,9*32+14,-3,-3)
    struct.pack_into('<H',data,9*32+18,0x1e if corrected else 0x16)
    struct.pack_into('<H',data,0x8000+200*2,0x1000|9)
    raw=bytes(data)
    provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(struct.pack('<16h',*floor)).hexdigest())
    return raw,floor,provenance


class WorldFootprintTests(TestCase):
    def test_native_offset_correction_http_and_immutable_project(self):
        for corrected in (False,True):
            with self.subTest(corrected=corrected),tempfile.TemporaryDirectory() as root:
                raw,floor,provenance=footprint_fixture(corrected)
                p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc);p.save()
                held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack));files={f.name:f.read_bytes() for f in Path(root).iterdir() if f.is_file()}
                ctx=(raw,provenance,{},48,floor,None,raw,[])
                with patch('sdk.worldmap_placement_allocation.context',return_value=ctx):
                    key=state_key(p);identifier='scene://map01/worldmap/placements/00c8';result=inspect(p,'map01',key,identifier)
                    dx,dz=(76,-36) if corrected else (80,-48)
                    self.assertEqual(result['offset'],dict(x=dx,z=dz))
                    self.assertEqual(result['centre'],dict(x=72*128+4+64+dx,z=128-12+64+dz))
                    self.assertEqual(result['anchor']['cell_index'],201);self.assertEqual(result['anchor']['bind_owner'],'init_bind')
                    self.assertEqual(result['extents'],'unknown');self.assertFalse(result['gameplay_verified'])
                    with http_server(p) as (server,post):
                        with urlopen(f'http://127.0.0.1:{server.server_address[1]}/worldmap-footprint.js') as response:
                            self.assertEqual(response.status,200)
                            self.assertIn(b'qualifyWorldFootprint',response.read())
                        body=dict(scene='map01',source_key=key,entity_id=identifier)
                        self.assertEqual(post('/api/worldmap-footprint',body)[0],200)
                        self.assertEqual(post('/api/worldmap-footprint',{**body,'extra':True})[0],400)
                        self.assertEqual(post('/api/worldmap-footprint',{**body,'source_key':'0'*64})[0],400)
                    for invalid in ('foreign','scene://map01/worldmap/placements/4000','scene://map01/worldmap/ground'):
                        with self.assertRaises(ProjectError):inspect(p,'map01',key,invalid)
                self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
                self.assertEqual({f.name:f.read_bytes() for f in Path(root).iterdir() if f.is_file()},files)

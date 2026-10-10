"""Literal clone edits, later-donor independence and shared workflow integrity."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64
import struct
import tempfile
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placement_allocation_binding import COMPONENT,SCHEMA,owner
from sdk.worldmap_placement_edit import review
from importer.worldmap_placement_allocation import allocate
from test_worldmap_placement_allocation import fixture,request
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class WorldDecorationEditTests(TestCase):
    def test_literal_parent_clone_edit_preserves_child_and_native_owners(self):
        raw,floor=fixture();provenance=dict(scene='map01',source_disc_sha256='b'*64,
            source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(struct.pack('<16h',*floor)).hexdigest())
        first=request();second=request(5,201,2);second['donor_cell']=200
        initial,a=allocate(raw,floor,'map01',[first]);current,b=allocate(initial,floor,'map01',[second])
        binding=dict(schema_version=SCHEMA,**provenance,operations=[dict(requests=[first],proposed_map_sha256=a['proposed_sha256']),dict(requests=[second],proposed_map_sha256=b['proposed_sha256'])])
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
            p.overrides[owner('map01')]={COMPONENT:binding};p.save()
            held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack));context=(raw,provenance,{},48,floor,None,raw,[])
            desired=dict(offset=dict(x=-32768,y=32767,z=-19),yaw_units=4095)
            with patch('sdk.worldmap_placement_allocation.context',return_value=context),patch('sdk.worldmap_placement_edit.context',return_value=context):
                key=state_key(p);value=review(p,'map01',key,first['placement_id'],desired)
                expected=bytearray(current);struct.pack_into('<3h',expected,128,-32768,32767,-19);struct.pack_into('<H',expected,138,0xafff)
                self.assertEqual(base64.b64decode(value['proposed_map_base64']),bytes(expected))
                self.assertEqual(expected[160:192],current[160:192]);self.assertEqual(value['binding']['operations'][1]['requests'],binding['operations'][1]['requests'])
                self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
                for bad in [dict(offset=dict(x=32768,y=0,z=0),yaw_units=0),dict(offset=dict(x=True,y=0,z=0),yaw_units=0),dict(offset=dict(x=0,y=0,z=0),yaw_units=4096)]:
                    with self.assertRaises(ProjectError):review(p,'map01',key,first['placement_id'],bad)
                with self.assertRaises(ProjectError):review(p,'map01',key,'foreign',desired)
                with self.assertRaises(ProjectError):review(p,'map01',key,first['placement_id'],first['values'])
                command=dict(type='set_worldmap_authored_placement',scene='map01',source_key=key,placement_id=first['placement_id'],values=desired,review_key=value['review_key'])
                with http_server(p) as (_,post):
                    self.assertEqual(post('/api/worldmap-decoration-transform-review',dict(scene='map01',source_key=key,placement_id=first['placement_id'],values=desired))[0],200)
                    self.assertEqual(post('/api/worldmap-decoration-transform-review',dict(scene='map01',source_key=key,placement_id=first['placement_id'],values=desired,extra=True))[0],400)
                    self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400)
                    self.assertEqual(post('/api/command',command)[0],200)
                    self.assertEqual(post('/api/command',command)[0],400)
                self.assertEqual(len(p.undo_stack),len(history[0])+1)
                applied=deepcopy(p._document());p.save();self.assertEqual(ProjectService.open(Path(root))._document(),applied)
                p.undo();self.assertEqual(p._document(),held);p.redo();self.assertEqual(p._document(),applied)
                p.undo();self.assertEqual(p._document(),held)

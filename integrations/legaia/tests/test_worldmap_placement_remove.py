"""Literal removal, dependent donor rebasing and empty-owner history."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64,struct,tempfile
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placement_allocation_binding import COMPONENT,SCHEMA,owner
from sdk.worldmap_placement_remove import review
from importer.worldmap_placement_allocation import allocate
from test_worldmap_placement_allocation import fixture,request
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class WorldDecorationRemovalTests(TestCase):
    def test_parent_removal_rebases_direct_children_preserves_grandchild_and_full_map(self):
        original,floor=fixture();data=bytearray(original)
        for cell in (202,203):struct.pack_into('<H',data,0x8000+cell*2,0x3400|10)
        raw=bytes(data);first=request();second=request(5,201,2);second['donor_cell']=200
        third=request(6,202,3);third['donor_cell']=200;fourth=request(7,203,4);fourth['donor_cell']=201
        provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(struct.pack('<16h',*floor)).hexdigest())
        current=raw;ops=[]
        for requests in ([first],[second,third],[fourth]):
            current,audit=allocate(current,floor,'map01',requests);ops.append(dict(requests=requests,proposed_map_sha256=audit['proposed_sha256']))
        binding=dict(schema_version=SCHEMA,**provenance,operations=ops)
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
            p.overrides[owner('map01')]={COMPONENT:binding};p.save();held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
            context=(raw,provenance,{},48,floor,None,raw,[])
            with patch('sdk.worldmap_placement_allocation.context',return_value=context),patch('sdk.worldmap_placement_remove.context',return_value=context):
                key=state_key(p);value=review(p,'map01',key,first['placement_id']);expected=bytearray(current)
                expected[128:160]=bytes(32);expected[0x8000+400:0x8000+402]=raw[0x8000+400:0x8000+402]
                self.assertEqual(base64.b64decode(value['proposed_map_base64']),bytes(expected));self.assertEqual(len(value['audit']['rebased_donors']),2)
                self.assertEqual([r['donor_cell'] for r in value['binding']['operations'][0]['requests']],[100,100])
                self.assertEqual(value['binding']['operations'][1]['requests'],[fourth]);self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
                with self.assertRaises(ProjectError):review(p,'map01',key,'foreign')
                command=dict(type='remove_worldmap_authored_placement',scene='map01',source_key=key,placement_id=first['placement_id'],review_key=value['review_key'])
                with http_server(p) as (_,post):
                    self.assertEqual(post('/api/worldmap-decoration-removal-review',dict(scene='map01',source_key=key,placement_id=first['placement_id']))[0],200)
                    self.assertEqual(post('/api/worldmap-decoration-removal-review',dict(scene='map01',source_key=key,placement_id=first['placement_id'],extra=True))[0],400)
                    self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400)
                    self.assertEqual(post('/api/command',command)[0],200);self.assertEqual(post('/api/command',command)[0],400)
                applied=deepcopy(p._document());self.assertEqual(len(p.undo_stack),len(history[0])+1);p.save();self.assertEqual(ProjectService.open(Path(root))._document(),applied)
                p.undo();self.assertEqual(p._document(),held);p.redo();self.assertEqual(p._document(),applied);p.undo();self.assertEqual(p._document(),held)

    def test_last_clone_removes_owner_and_restores_complete_original_map(self):
        raw,floor=fixture();first=request();current,audit=allocate(raw,floor,'map01',[first])
        provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256=sha256(struct.pack('<16h',*floor)).hexdigest())
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
            p.overrides[owner('map01')]={COMPONENT:dict(schema_version=SCHEMA,**provenance,operations=[dict(requests=[first],proposed_map_sha256=audit['proposed_sha256'])])}
            held=deepcopy(p._document());context=(raw,provenance,{},48,floor,None,raw,[])
            with patch('sdk.worldmap_placement_allocation.context',return_value=context),patch('sdk.worldmap_placement_remove.context',return_value=context):
                key=state_key(p);value=review(p,'map01',key,first['placement_id']);self.assertIsNone(value['binding']);self.assertEqual(base64.b64decode(value['proposed_map_base64']),raw)
                p.command(dict(type='remove_worldmap_authored_placement',scene='map01',source_key=key,placement_id=first['placement_id'],review_key=value['review_key']))
                self.assertNotIn(owner('map01'),p.overrides);p.save();self.assertEqual(ProjectService.open(Path(root))._document(),p._document())
                p.undo();self.assertEqual(p._document(),held);p.redo();self.assertNotIn(owner('map01'),p.overrides)

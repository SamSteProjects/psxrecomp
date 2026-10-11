"""Literal native cell movement, clone lineage, refusal and command persistence."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64
import struct
import tempfile
from unittest import TestCase
from unittest.mock import patch

from importer.worldmap_placement_allocation import allocate
from importer.worldmap_placements import decode_worldmap_placements
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placement_allocation_binding import COMPONENT, SCHEMA, owner
from sdk.worldmap_placement_relocate import review
from test_worldmap_placement_allocation import fixture, request
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class WorldDecorationCellTests(TestCase):
    def test_native_cell_move_preserves_children_offsets_and_history(self):
        original, floor = fixture()
        data = bytearray(original)
        # Different terrain and floor, beyond the first 4096 cells.
        destination = 16000
        data[11*32+20:11*32+24] = bytes([9,8,7,6])
        for cell in (202,203):
            struct.pack_into('<H',data,0x8000+cell*2,0x3400|10)
        struct.pack_into('<H',data,0x8000+destination*2,0x1400|11)
        data[0x4000+destination] = 8
        raw = bytes(data)
        first=request();second=request(5,201,2);second['donor_cell']=200
        third=request(6,202,3);third['donor_cell']=200
        fourth=request(7,203,4);fourth['donor_cell']=201
        provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),
            source_floor_lut_sha256=sha256(struct.pack('<16h',*floor)).hexdigest())
        current=raw;ops=[]
        for requests in ([first],[second,third],[fourth]):
            current,audit=allocate(current,floor,'map01',requests)
            ops.append(dict(requests=requests,proposed_map_sha256=audit['proposed_sha256']))
        binding=dict(schema_version=SCHEMA,**provenance,operations=ops)
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64
            p.import_metadata(doc);p.overrides[owner('map01')]={COMPONENT:binding};p.save()
            held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
            context=(raw,provenance,{},48,floor,None,raw,[])
            with patch('sdk.worldmap_placement_allocation.context',return_value=context),patch('sdk.worldmap_placement_relocate.context',return_value=context):
                key=state_key(p);value=review(p,'map01',key,first['placement_id'],destination)
                expected=bytearray(current)
                expected[0x8000+400:0x8000+402]=raw[0x8000+400:0x8000+402]
                struct.pack_into('<H',expected,0x8000+destination*2,0x1400|4)
                expected[4*32+20:4*32+24]=bytes([9,8,7,6])
                candidate=base64.b64decode(value['proposed_map_base64'])
                self.assertEqual(candidate,bytes(expected))
                self.assertEqual(candidate[128:148],current[128:148]);self.assertEqual(candidate[152:160],current[152:160])
                self.assertEqual(len(value['audit']['rebased_donors']),2)
                self.assertEqual([r['donor_cell'] for r in value['binding']['operations'][1]['requests']],[destination,destination])
                self.assertEqual(value['binding']['operations'][2]['requests'],[fourth])
                self.assertEqual(value['binding']['operations'][0]['requests'][0],{**first,'target_cell':destination})
                old={s['source_cell']:s for s in decode_worldmap_placements(current,floor,scene='map01')['placements']}
                new={s['source_cell']:s for s in decode_worldmap_placements(candidate,floor,scene='map01')['placements']}
                for cell in (100,101,201,202,203):self.assertEqual(old[cell],new[cell])
                self.assertEqual(new[destination]['source_position'],dict(x=(destination%128)*128+192,y=-24,z=(destination//128)*128+16))
                self.assertNotIn(200,new);self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)
                for invalid in (True,-1,16384,1.0,'16000',200,201,0):
                    with self.subTest(invalid=invalid),self.assertRaises(ProjectError):review(p,'map01',key,first['placement_id'],invalid)
                with self.assertRaises(ProjectError):review(p,'map01',key,'foreign',destination)
                command=dict(type='relocate_worldmap_authored_placement',scene='map01',source_key=key,
                    placement_id=first['placement_id'],target_cell=destination,review_key=value['review_key'])
                with http_server(p) as (_,post):
                    body={k:command[k] for k in ('scene','source_key','placement_id','target_cell')}
                    self.assertEqual(post('/api/worldmap-decoration-cell-review',body)[0],200)
                    self.assertEqual(post('/api/worldmap-decoration-cell-review',{**body,'extra':True})[0],400)
                    self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400)
                    self.assertEqual(post('/api/command',command)[0],200)
                    self.assertEqual(post('/api/command',command)[0],400)
                applied=deepcopy(p._document());self.assertEqual(len(p.undo_stack),len(history[0])+1)
                p.save();self.assertEqual(ProjectService.open(Path(root))._document(),applied)
                p.undo();self.assertEqual(p._document(),held);p.redo();self.assertEqual(p._document(),applied)
                p.undo();self.assertEqual(p._document(),held)

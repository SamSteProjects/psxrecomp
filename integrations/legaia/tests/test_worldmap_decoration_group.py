"""Complete group patches, donor independence and atomic history."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64
import struct
import tempfile
from unittest import TestCase
from unittest.mock import patch

from importer.worldmap_placement_allocation import allocate
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_decoration_group import arguments, revised_binding, review
from sdk.worldmap_placement_allocation_binding import COMPONENT, SCHEMA, MODEL_SCHEMA, owner
from test_worldmap_placement_allocation import fixture, request
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


def group_fixture(model=False):
    raw, floor = fixture(); data = bytearray(raw)
    struct.pack_into('<H', data, 0x8000 + 202 * 2, 0x3400 | 10)
    raw = bytes(data)
    provenance = dict(scene='map01', source_disc_sha256='b' * 64,
        source_map_sha256=sha256(raw).hexdigest(),
        source_floor_lut_sha256=sha256(struct.pack('<16h', *floor)).hexdigest())
    rows = [request(), request(5, 201, 2), request(6, 202, 3)]
    rows[1]['donor_cell'] = 200; rows[2]['donor_cell'] = 201
    rows[1]['values']['offset']['x'] = -128
    rows[1]['values']['yaw_units'] = 4090
    if model: rows[0]['model_pool_index'] = 2
    current = raw; operations = []
    for row in rows:
        current, audit = allocate(current, floor, 'map01', [row])
        operations.append(dict(requests=[row], proposed_map_sha256=audit['proposed_sha256']))
    binding = dict(schema_version=MODEL_SCHEMA if model else SCHEMA, **provenance, operations=operations)
    return raw, floor, provenance, rows, current, binding


class WorldDecorationGroupTests(TestCase):
    def test_domains_overflow_and_no_partial_recipe_mutation(self):
        raw, floor, _, rows, _, binding = group_fixture()
        ids = sorted(r['placement_id'] for r in rows[:2]); delta = dict(x=1,y=0,z=0,yaw_units=1)
        for bad_ids in ([], ids[::-1], [ids[0]] * 2, ['foreign'], ids * 17, [True]):
            with self.subTest(ids=bad_ids), self.assertRaises(ProjectError):
                revised_binding(raw, floor, binding, bad_ids, delta)
        for bad in ({**delta,'x':True}, {**delta,'z':65536}, {**delta,'yaw_units':4096},
                    {**delta,'extra':1}, dict(x=0,y=0,z=0,yaw_units=0)):
            with self.subTest(delta=bad), self.assertRaises(ProjectError): arguments(ids,bad)
        held = deepcopy(binding)
        # The first selection fits; the second overflows after earlier draft work.
        with self.assertRaises(ProjectError): revised_binding(raw,floor,binding,ids,{**delta,'x':-32700})
        self.assertEqual(binding,held)

    def test_full_literal_group_v1_v2_http_history_and_persistence(self):
        for model in (False, True):
            with self.subTest(model=model), tempfile.TemporaryDirectory() as root:
                raw,floor,provenance,rows,current,binding = group_fixture(model)
                p = ProjectService(Path(root)); doc = synthetic_scene()
                doc['source']['disc_identity'] = 'sha256:' + 'b' * 64; p.import_metadata(doc)
                p.overrides[owner('map01')] = {COMPONENT:binding}; p.save()
                held = deepcopy(p._document()); history = deepcopy((p.undo_stack,p.redo_stack))
                # A separate original source-record transform must survive exactly.
                transformed = bytearray(raw); struct.pack_into('<h',transformed,9*32,-99)
                current = bytearray(current); struct.pack_into('<h',current,9*32,-99); current=bytes(current)
                context = (raw,provenance,{},48,floor,None,bytes(transformed),[])
                ids = sorted(r['placement_id'] for r in rows[:2]); delta=dict(x=16,y=-4,z=32,yaw_units=32)
                with patch('sdk.worldmap_placement_allocation.context',return_value=context), patch('sdk.worldmap_decoration_group.context',return_value=context):
                    key = state_key(p); receipt = review(p,'map01',key,ids,delta)
                    expected = bytearray(current)
                    for row in rows[:2]:
                        at=row['record_index']*32
                        struct.pack_into('<3h',expected,at,row['values']['offset']['x']+16,-20,80)
                        struct.pack_into('<H',expected,at+10,0xa000|((row['values']['yaw_units']+32)%4096))
                    self.assertEqual(base64.b64decode(receipt['proposed_map_base64']),bytes(expected))
                    self.assertEqual(receipt['binding']['operations'][2]['requests'],binding['operations'][2]['requests'])
                    self.assertEqual(receipt['binding']['schema_version'],binding['schema_version'])
                    self.assertEqual(p._document(),held); self.assertEqual((p.undo_stack,p.redo_stack),history)
                    command=dict(type='transform_worldmap_authored_placements',scene='map01',source_key=key,
                        placement_ids=ids,delta=delta,review_key=receipt['review_key'])
                    with http_server(p) as (_,post):
                        body={k:v for k,v in command.items() if k not in ('type','review_key')}
                        self.assertEqual(post('/api/worldmap-decoration-group-review',body)[0],200)
                        self.assertEqual(post('/api/worldmap-decoration-group-review',{**body,'extra':True})[0],400)
                        self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400)
                        self.assertEqual(post('/api/command',command)[0],200)
                        self.assertEqual(post('/api/command',command)[0],400)
                    self.assertEqual(len(p.undo_stack),len(history[0])+1)
                    applied=deepcopy(p._document()); p.save()
                    self.assertEqual(ProjectService.open(Path(root))._document(),applied)
                    p.undo(); self.assertEqual(p._document(),held)
                    p.redo(); self.assertEqual(p._document(),applied)
                    p.undo(); self.assertEqual(p._document(),held)

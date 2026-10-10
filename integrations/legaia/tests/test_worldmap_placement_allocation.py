"""Complete literal allocation bytes, terrain retention and read-only HTTP gates."""
from copy import deepcopy
from pathlib import Path
import base64
import struct
from hashlib import sha256
import tempfile
from unittest import TestCase
from unittest.mock import patch

from importer.core import ImportError
from importer.terrain import decode_terrain
from importer.worldmap_placement_allocation import allocate, inventory
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placement_allocation import source, review
from test_model_primitive_workflow import http_server
from test_project_workflow import synthetic_scene


def fixture():
    data = bytearray(0x12000)
    # Donor placement has opaque tail, upper yaw bits and a different ground.
    struct.pack_into('<3h', data, 9*32, 4,-8,12)
    struct.pack_into('<H', data, 9*32+10, 0xa040)
    struct.pack_into('<2H', data, 9*32+16, 1,0x13)
    data[9*32+20:9*32+24] = bytes([6,7,8,9])
    data[9*32+24:9*32+32] = bytes(range(8))
    data[10*32+20:10*32+24] = bytes([3,2,64,0])
    for cell in (100,101): struct.pack_into('<H', data, 0x8000+cell*2, 0x1000|9)
    for cell in (200,201): struct.pack_into('<H', data, 0x8000+cell*2, 0x3400|10)
    data[0x4000+200] = 3
    return bytes(data), list(range(16))


def request(index=4, cell=200, ordinal=1):
    return dict(placement_id=f'placement://authored/00000000-0000-4000-8000-{ordinal:012x}',
        donor_cell=100, target_cell=cell, record_index=index,
        values=dict(offset=dict(x=128,y=-16,z=48),yaw_units=1024))


def terrain_view(data, floor):
    value = decode_terrain(data, floor)
    for cell in value['cells']: cell.pop('object_record_index')
    return value


class WorldPlacementAllocationTests(TestCase):
    def test_full_native_clone_bytes_and_unchanged_ground_existing_seeds(self):
        raw, floor = fixture();requests=[request(),request(5,201,2)]
        candidate, audit = allocate(raw,floor,'map01',requests)
        expected = bytearray(raw)
        for row in requests:
            at = row['record_index']*32
            expected[at:at+32] = raw[9*32:10*32]
            expected[at+20:at+24] = raw[10*32+20:10*32+24]
            struct.pack_into('<3h',expected,at,128,-16,48)
            struct.pack_into('<H',expected,at+10,0xa400)
            struct.pack_into('<H',expected,0x8000+row['target_cell']*2,0x3400|row['record_index'])
        self.assertEqual(candidate,bytes(expected))
        self.assertEqual(terrain_view(candidate,floor),terrain_view(raw,floor))
        self.assertEqual((audit['original_placement_count'],audit['proposed_placement_count']),(2,4))
        self.assertEqual(audit['allocations'][0]['native_seed']['source_position'],dict(x=9408,y=-19,z=144))
        self.assertEqual(raw,fixture()[0])

    def test_native_owner_domains_aliases_and_current_capacity(self):
        raw,floor=fixture();good=request()
        alterations=[dict(donor_cell=0),dict(donor_cell=True),dict(target_cell=100),dict(target_cell=0),
            dict(record_index=9),dict(record_index=10),dict(record_index=1),dict(record_index=True),
            dict(placement_id='foreign'),dict(extra=True),dict(values=dict(offset=dict(x=32768,y=0,z=0),yaw_units=0)),
            dict(values=dict(offset=dict(x=0,y=0,z=0),yaw_units=4096))]
        for change in alterations:
            with self.subTest(change=change),self.assertRaises(ImportError): allocate(raw,floor,'map01',[{**good,**change}])
        for rows in ([good,good],[good,request(5,200,2)],[good,request(4,201,2)],[],[good]*33):
            with self.assertRaises(ImportError): allocate(raw,floor,'map01',rows)
        occupied=bytearray(raw);occupied[4*32]=1
        with self.assertRaises(ImportError): allocate(bytes(occupied),floor,'map01',[good])
        anchored=bytearray(raw)
        # An existing placed actor can own a model-free cell as its footprint
        # anchor. It must not be offered or overwritten by a decoration clone.
        struct.pack_into('<2H',anchored,11*32+16,1,4)
        struct.pack_into('<2b',anchored,11*32+6,1,0)
        struct.pack_into('<H',anchored,0x8000+199*2,11)
        self.assertNotIn(200,inventory(bytes(anchored),floor,'map01')['target_cells'])
        with self.assertRaises(ImportError): allocate(bytes(anchored),floor,'map01',[good])

    def test_readonly_http_source_review_exact_scope_and_stale_live_refusal(self):
        raw,floor=fixture()
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
            key=state_key(p);held=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
            provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256='c'*64)
            context=(raw,provenance,{},0,floor,None,raw,[])
            with patch('sdk.worldmap_placement_allocation.context',return_value=context):
                value=source(p,'map01',key);self.assertEqual(value['current_map_base64'],base64.b64encode(raw).decode('ascii'))
                result=review(p,'map01',key,[request()]);self.assertFalse(result['build_ready'])
                with http_server(p) as (_,post):
                    self.assertEqual(post('/api/worldmap-placement-allocation-source',dict(scene='map01',source_key=key))[0],200)
                    self.assertEqual(post('/api/worldmap-placement-allocation-review',dict(scene='map01',source_key=key,requests=[request()]))[0],200)
                    for route,body in [('/api/worldmap-placement-allocation-source',dict(scene='map01',source_key=key,extra=True)),
                            ('/api/worldmap-placement-allocation-review',dict(scene='map01',source_key=key,requests=[request()],extra=True)),
                            ('/api/worldmap-placement-allocation-review',dict(scene='map01',source_key='0'*64,requests=[request()]))]:
                        self.assertEqual(post(route,body)[0],400)
                with self.assertRaises(ProjectError): review(p,'map01','0'*64,[request()])
                p.mode='live'
                with self.assertRaises(ProjectError): review(p,'map01',state_key(p),[request()])
                p.mode='edit'
            self.assertEqual(p._document(),held);self.assertEqual((p.undo_stack,p.redo_stack),history)

    def test_retained_authored_donor_apply_history_save_open_and_guarded_build_merge(self):
        from sdk.worldmap_placement_allocation import build
        from sdk.worldmap_placement_allocation_binding import COMPONENT,owner,validate,replay
        raw,floor=fixture()
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc);p.save()
            provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256='c'*64)
            transformed=bytearray(raw);struct.pack_into('<h',transformed,9*32,96)
            native_context=(raw,provenance,{},200,floor,None,bytes(transformed),[])
            with patch('sdk.worldmap_placement_allocation.context',return_value=native_context):
                before=deepcopy(p._document());first=review(p,'map01',state_key(p),[request()])
                command=dict(type='allocate_worldmap_placements',scene='map01',source_key=state_key(p),requests=[request()],review_key=first['review_key'])
                with self.assertRaises(ProjectError):p.command({**command,'review_key':'0'*64})
                self.assertEqual(p._document(),before)
                with http_server(p) as (_,post):self.assertEqual(post('/api/command',command)[0],200)
                after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before);p.redo();self.assertEqual(p._document(),after)
                current=source(p,'map01',state_key(p));self.assertEqual(len(current['authored_allocations']),1)
                second=request(5,201,2);second['donor_cell']=200
                receipt=review(p,'map01',state_key(p),[second]);p.command(dict(type='allocate_worldmap_placements',scene='map01',source_key=state_key(p),requests=[second],review_key=receipt['review_key']))
                p.save();opened=ProjectService.open(p.root);self.assertEqual(opened.overrides,p.overrides)
                binding=p.overrides[owner('map01')][COMPONENT];literal,_=replay(raw,floor,binding)
                from sdk.worldmap_placement_export import export
                old_disc=p.disc_path;p.disc_path='fixture-disc'
                with patch('sdk.worldmap_placement_export.load_worldmap_geometry',side_effect=AssertionError('allocated GLB must not omit clones')):
                    with self.assertRaisesRegex(ProjectError,'allocated decorations'):export(p,'map01',state_key(p))
                p.disc_path=old_disc
                expected=bytearray(literal);expected[9*32:9*32+2]=transformed[9*32:9*32+2]
                self.assertEqual(base64.b64decode(receipt['proposed_map_base64']),bytes(expected))
                disjoint=bytearray(transformed);disjoint[0x11000]=77
                overlays=[dict(offset=200,size=len(raw),payload=bytes(disjoint),expected_sha256=sha256(raw).hexdigest())]
                changes=build(p,overlays);expected[0x11000]=77;self.assertEqual(overlays[0]['payload'],bytes(expected));self.assertEqual(len(changes),2)
                bad=deepcopy(binding);bad['operations'][1]['requests'][0]['placement_id']=bad['operations'][0]['requests'][0]['placement_id']
                with self.assertRaises(ProjectError):validate(p,owner('map01'),bad)
                bad=deepcopy(binding);bad['operations'][0]['proposed_map_sha256']='0'*64
                with self.assertRaises(ProjectError):replay(raw,floor,bad)
                conflict=bytearray(raw);conflict[4*32]=77
                with self.assertRaises(ProjectError):build(p,[dict(offset=200,size=len(raw),payload=bytes(conflict),expected_sha256=sha256(raw).hexdigest())])
                self.assertEqual(p.imports,opened.imports)

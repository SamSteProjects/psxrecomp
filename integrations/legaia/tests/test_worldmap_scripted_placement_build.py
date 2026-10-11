from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import struct
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from sdk.project import ProjectService,ProjectError,atomic_write
from sdk.worldmap_scripted_placement_binding import COMPONENT,owner,base_path
from sdk.worldmap_scripted_placement_allocation import build
from sdk.build import package_change_kinds
from test_worldmap_scripted_placement_binding import ledger
from test_project_workflow import synthetic_scene


class ScriptedPlacementBuildTests(TestCase):
    def test_world_height_and_script_share_one_native_man_writer(self):
        from sdk.worldmap_script_operands import build as build_man
        from importer.core import decompress_lzs
        retail=bytes(64)+b'\x01\x02\x03\x04'
        current=retail[:-1]+b'\x09'
        packed=b''.join(bytes([(1<<len(retail[i:i+8]))-1])+retail[i:i+8] for i in range(0,len(retail),8))
        slot=dict(compressed_stream_offset=0,compressed_bytes_consumed=len(packed))
        archive=SimpleNamespace(node=SimpleNamespace(extent_lba=10),entry=lambda _:SimpleNamespace(start_lba=20))
        provenance=dict(map_entry_index=8)
        def archive_patches(_,patches):
            return [dict(offset=100,payload=patches[0]['payload'],expected_sha256=patches[0]['expected_sha256'])],[dict(provenance)]
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root));project.imports['scene://map01']=dict(scene=dict(name='map01'))
            project.overrides['scene://map01']={'FloorHeights':dict(source_sha256=sha256(retail).hexdigest(),edits=[dict(tier=0,height=17)])}
            for script_changes in (False,True):
                before=current if script_changes else retail
                script_audit=[dict(scope='script-fixture',scene='map01',semantic_id='script://map01/fixture',field='fixture',before_value=4,after_value=9)] if script_changes else []
                context=(retail,{},None,8,0,slot,packed,None,before,script_audit)
                with patch('sdk.worldmap_script_operands.context',return_value=context),patch('sdk.texture_build.archive_overlay_patches',side_effect=archive_patches),patch('importer.prot_layout.locate_physical_span',return_value=dict(entry_index=8,offset_within_span=0)):
                    overlays,audit=build_man(project,archive)
                self.assertEqual(len(overlays),1)
                decoded,_=decompress_lzs(overlays[0]['payload'],len(retail))
                expected=bytearray(before);struct.pack_into('<h',expected,2,17)
                self.assertEqual(decoded,bytes(expected))
                self.assertEqual(len(audit),1+int(script_changes))
                from sdk.build import build_report
                report=build_report(dict(edits=audit,validation={},overlays=overlays))
                height=next(c for c in report['changes'] if c['field']=='floor_height')
                self.assertEqual((height['scene'],height['owner_id'],height['before'],height['after']),('map01','scene://map01',0,17))

    def test_complete_overlay_composition_and_declared_scope(self):
        base,fallback,man,floor,binding,expected,_=ledger()
        provenance={k:binding[k] for k in ('scene','source_disc_sha256','source_map_sha256','source_floor_lut_sha256')}
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;project.import_metadata(doc)
            project.overrides[owner('map01')]={COMPONENT:binding};atomic_write(base_path(project,binding),base)
            held=deepcopy(project._document());history=deepcopy((project.undo_stack,project.redo_stack))
            inputs=(base,provenance,floor,base,[],fallback,man,man,{},[])
            geometry=dict(scene_graph=dict(assets=[dict(asset_id='asset://map01/worldmap/models/0001',preview=dict(vertices=[0],triangles=[0]))]))
            with patch('sdk.worldmap_scripted_placement_allocation._inputs',return_value=inputs),patch('sdk.worldmap_placements.source',return_value=(base,provenance,{},12345,floor)),patch('sdk.worldmap_geometry.inspect',return_value=geometry):
                overlays=[];changes=build(project,overlays)
                self.assertEqual(overlays[0]['payload'],expected)
                self.assertEqual(overlays[0]['expected_sha256'],sha256(base).hexdigest())
                self.assertIn('scripted World placements',package_change_kinds(changes))
                overlays=[dict(offset=12345,size=len(base),payload=base,expected_sha256=sha256(base).hexdigest(),file='assets/existing.map')]
                build(project,overlays);self.assertEqual(overlays[0]['payload'],expected)
                self.assertEqual(overlays[0]['file'],'assets/existing.map')
                for case in ('partial','preimage','missing_coauthor'):
                    rows=[dict(offset=12345,size=len(base),payload=base,expected_sha256=sha256(base).hexdigest())]
                    if case=='partial':rows[0]['size']=4
                    if case=='preimage':rows[0]['expected_sha256']='0'*64
                    if case=='missing_coauthor':rows[0]['payload']=base[:0x4000]+bytes([base[0x4000]^16])+base[0x4001:]
                    with self.subTest(case=case),self.assertRaises(ProjectError):build(project,rows)
                with patch('sdk.worldmap_geometry.inspect',return_value=dict(scene_graph=dict(assets=[]))),self.assertRaisesRegex(ProjectError,'drawable'):
                    build(project,[])
            self.assertEqual(project._document(),held);self.assertEqual((project.undo_stack,project.redo_stack),history)

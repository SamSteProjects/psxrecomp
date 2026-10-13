import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from importer.animation import load_animation_preview
from importer.assets import load_model_source
from importer.pipeline import import_scene
from importer.textures import parse_tim
from sdk.field_equipment_playback import preview
from sdk.project import ProjectService, ProjectError
from sdk.project_assets import source_key
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Retail source is private')
class FieldEquipmentPlaybackTests(unittest.TestCase):
    def make_project(self, root):
        p = ProjectService(Path(root)); p.disc_path = os.environ['LEGAIA_DISC_BIN']
        p.import_metadata(import_scene(p.disc_path, 'town01'))
        for slot in range(3):
            asset = f'asset://legaia/models/global-special/{240+slot:04x}'
            raw = load_model_source(p.disc_path, p.assets.records[asset])
            edited = bytearray(raw); at = 12 + struct.unpack_from('<I', raw, 40)[0]
            struct.pack_into('<h', edited, at, struct.unpack_from('<h', raw, at)[0] + 21)
            p.set_model_replacement(asset, bytes(edited))
        for slot in range(8):
            asset = f'texture://legaia/field-party/874/2/{slot}'
            source = p._texture_context(asset).original_tim(asset); tim = parse_tim(source)
            candidate = bytearray(source)
            candidate[20:20+len(tim.clut.data)] = struct.pack('<H', 0x03e0) * (len(tim.clut.data)//2)
            p.set_texture_replacement(asset, bytes(candidate))
        p.save(); return ProjectService.open(p.root)

    def test_all_models_variants_layers_clips_match_literal_channels_and_native_poses(self):
        cases = []; checked = 0
        with tempfile.TemporaryDirectory() as root:
            p = self.make_project(root); before = deepcopy((p._document(), p.undo_stack))
            for slot in range(3):
                asset = f'asset://legaia/models/global-special/{240+slot:04x}'
                for layer in ('retail', 'current'):
                    effective = p.read_model_replacement(asset, p.model_overrides[asset]) if layer=='current' else None
                    for equipment in (0, 1):
                        for clip in ('idle', 'walk'):
                            native = load_animation_preview(p.disc_path, p.assets.records[asset], clip,
                                equipment_byte=equipment, model_source=effective)
                            index = slot*7+(clip=='idle'); count = native['frame_count']
                            context = dict(projectPath=str(p.root), sourceKey=source_key(p), assetId=asset,
                                modelLayer=layer, equipmentByte=equipment, clipId=clip, frameIndex=count//2)
                            args = dict(expected_project_path=str(p.root), expected_source_key=source_key(p),
                                asset_id=asset, equipment_byte=equipment, clip_id=clip, frame_index=count//2)
                            receipt = preview(p, **args, model_layer=layer)
                            record = base64.b64decode(receipt['record_base64']); bank=base64.b64decode(receipt['bank_base64'])
                            self.assertEqual(sha256(record).hexdigest(), receipt['record_sha256'])
                            self.assertEqual(sha256(bank).hexdigest(), receipt['bank_sha256'])
                            self.assertEqual(struct.unpack_from('<I', bank)[0], 23)
                            start = struct.unpack_from('<I', bank, 4+index*4)[0]
                            end = struct.unpack_from('<I', bank, 8+index*4)[0] if index<22 else len(bank)
                            self.assertEqual(record, bank[start:end]); self.assertEqual(len(record), 16+count*80)
                            selected = []
                            for frame in sorted({0, count//2, count-1}):
                                literal = []
                                for obj in range(10):
                                    d=record[8+(frame*10+obj)*8:16+(frame*10+obj)*8]
                                    xyz=[d[0]+(d[2]&15)*256,d[1]+(d[2]>>4)*256,d[3]+(d[4]&15)*256]
                                    literal.append(dict(object_index=obj, translation=[v-4096 if v>=2048 else v for v in xyz],
                                                        rotation_psx=[v*16 for v in d[5:8]],opaque_nibble=d[4]>>4))
                                self.assertEqual(literal, native['frames'][frame]['object_transforms'])
                                selected.append(native['frames'][frame]); checked += 1
                            self.assertEqual(receipt['preview']['geometry']['vertices'], native['frames'][count//2]['vertices'])
                            self.assertEqual(receipt['preview']['base_geometry']['texture_layer'], layer)
                            self.assertEqual(len(receipt['preview']['base_geometry']['texture_bindings']), 8 if layer=='current' else 0)
                            cases.append(dict(context=context, value=receipt, frames=selected))
            self.assertEqual((p._document(), p.undo_stack), before)
        output = os.getenv('LEGAIA_FIELD_EQUIPMENT_PLAYBACK_CASES')
        if output:
            Path(output).write_text(json.dumps(cases), encoding='utf-8')
            Path(output).with_name('native-proof.json').write_text(json.dumps(dict(cases=len(cases),poses=checked,
                three_models=True,both_variants=True,both_layers=True,idle_walk=True,literal_channels=True,
                native_pose_agreement=True,document_history_unchanged=True,gameplay_verified=False),indent=2),encoding='utf-8')

    def test_source_frame_variant_and_exact_http_refusals(self):
        with tempfile.TemporaryDirectory() as root:
            p = self.make_project(root); before = deepcopy((p._document(), p.undo_stack))
            args = dict(expected_project_path=str(p.root),expected_source_key=source_key(p),
                asset_id='asset://legaia/models/global-special/00f0',equipment_byte=0,clip_id='idle',frame_index=0)
            with http_server(p) as (_, post):
                for path in ('/api/field-equipment-playback','/api/field-equipment-current-playback'):
                    status, value=post(path,args);self.assertEqual(status,200,value)
                    self.assertEqual(value['schema_version'],'legaia.field-equipment-playback.v1')
                    for change in (dict(frame_index=True),dict(frame_index=-1),dict(frame_index=999),dict(clip_id=None),
                        dict(clip_id='battle'),dict(equipment_byte=True),dict(equipment_byte=256),
                        dict(asset_id='asset://legaia/models/global-special/00f3'),dict(expected_source_key='0'*64),
                        dict(expected_project_path='stale'),dict(display_fps=30),dict(export_fps=30)):
                        self.assertEqual(post(path,dict(args,**change))[0],400,change)
            self.assertEqual((p._document(),p.undo_stack),before)

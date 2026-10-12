import os,struct,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from importer.pipeline import import_scene
from importer.assets import load_model_source,decode_tmd
from importer.field_equipment import project_field_equipment,load_field_equipment_preview
from importer.animation import load_animation_preview
from importer.core import ImportError
from sdk.project import ProjectService
from sdk.project_assets import source_key
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class FieldEquipmentTests(unittest.TestCase):
    def test_all_party_template_copies_and_native_poses(self):
        disc=os.environ['LEGAIA_DISC_BIN'];document=import_scene(disc,'town01')
        for slot,target in enumerate((0,3,5)):
            asset=next(m for m in document['assets']['models'] if m['semantic_id']==f'asset://legaia/models/global-special/{0xf0+slot:04x}');raw=load_model_source(disc,asset)
            for value in (0,1,255):
                projected,proof=project_field_equipment(raw,slot,value);source=12+(11 if value==0 else 10)*28;destination=12+target*28;self.assertEqual(projected[destination:destination+28],raw[source:source+28]);self.assertEqual(projected[:destination],raw[:destination]);self.assertEqual(projected[destination+28:],raw[destination+28:]);self.assertEqual(struct.unpack_from('<I',projected,8)[0],12)
                g=load_field_equipment_preview(disc,asset,value);self.assertEqual(len(g['objects']),10);expected=decode_tmd(projected);self.assertEqual(g['vertices'],expected['vertices'][:len(g['vertices'])]);self.assertEqual(g['triangles'],expected['triangles'][:len(g['triangles'])]);self.assertEqual(g['equipment_variant'],proof)
                posed=load_animation_preview(disc,asset,'idle',equipment_byte=value);self.assertEqual(posed['geometry']['vertices'],g['vertices']);self.assertEqual(len(posed['frames'][0]['object_transforms']),10);self.assertEqual(len(posed['geometry']['objects']),10)
            self.assertEqual(project_field_equipment(raw,slot,1)[0],project_field_equipment(raw,slot,255)[0])
            for value in (True,-1,256,.5):
                with self.assertRaises(ImportError):project_field_equipment(raw,slot,value)

    def test_exact_http_fields_and_source_only_state(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));before=deepcopy((p._document(),p.undo_stack));args=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id='asset://legaia/models/global-special/00f0',equipment_byte=0,clip_id='idle',frame_index=0)
            with http_server(p) as (_,post):
                status,body=post('/api/field-equipment-preview',args);self.assertEqual(status,200,body);self.assertEqual(body['layer'],'retail_selected_variant');self.assertTrue(body['geometry']['posed']);self.assertEqual(body['geometry']['equipment_variant']['runtime_equipment'],'not_observed')
                for change in (dict(equipment_byte=True),dict(equipment_byte=256),dict(frame_index=True),dict(frame_index=999),dict(asset_id='asset://legaia/models/global-special/00f3'),dict(expected_source_key='0'*64),dict(extra=True)):
                    self.assertEqual(post('/api/field-equipment-preview',dict(args,**change))[0],400)
            self.assertEqual((p._document(),p.undo_stack),before)

import base64,json,os,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from importer.pipeline import import_scene
from importer.texture_png import decode_png
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.field_equipment import preview,export
from test_importer_export import parse_glb
from test_animation_clip_export import values


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class FieldEquipmentExportTests(unittest.TestCase):
    def test_all_active_corners_and_embedded_original_crops(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));before=deepcopy((p._document(),p.undo_stack));cases=[];corners=pixels=0
            for slot in range(3):
                for byte in (0,1):
                    for clip in (None,'idle','walk'):
                        ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=f'asset://legaia/models/global-special/{0xf0+slot:04x}',equipment_byte=byte,clip_id=clip,frame_index=0 if clip else None);held=preview(p,**ctx);result=export(p,**ctx);doc,binary=parse_glb(base64.b64decode(result['glb_base64']));g=held['geometry'];self.assertEqual(doc['extras']['source_record']['equipment_variant'],g['equipment_variant']);self.assertNotIn('animations',doc);self.assertNotIn('skins',doc)
                        for node in doc['nodes']:
                            if 'mesh' not in node:continue
                            o=node['extras']['source_object']
                            for primitive in doc['meshes'][node['mesh']]['primitives']:
                                expected=[]
                                for t in range(o['triangle_start'],o['triangle_start']+o['triangle_count']):
                                    if g['triangle_materials'][t]!=primitive['material']:continue
                                    for c in (0,2,1):x,y,z=g['vertices'][g['triangles'][t][c]];expected.append((x,-y,z))
                                actual=values(doc,binary,primitive['attributes']['POSITION']);self.assertEqual(len(actual),len(expected));corners+=len(actual)
                                for a,b in zip(actual,expected):
                                    for v,w in zip(a,b):self.assertAlmostEqual(v,w,delta=.0002)
                        textures=[t for t in g['textures'] if t['status']=='address_match'];self.assertEqual(len(doc.get('images',[])),len(textures))
                        for image,t in zip(doc.get('images',[]),textures):
                            v=doc['bufferViews'][image['bufferView']];rgba=decode_png(binary[v['byteOffset']:v['byteOffset']+v['byteLength']])['rgba'];self.assertEqual(rgba,base64.b64decode(t['rgba_base64']));pixels+=len(rgba)//4
                        cases.append(dict(context=dict(projectPath=str(p.root),sourceKey=source_key(p),assetId=ctx['asset_id'],equipmentByte=byte,clipId=clip,frameIndex=ctx['frame_index']),held=held,value=result))
            self.assertEqual((p._document(),p.undo_stack),before)
            output=os.getenv('LEGAIA_FIELD_EXPORT_CASES')
            if output:Path(output).write_text(json.dumps(dict(cases=cases,corners=corners,pixels=pixels)),encoding='utf-8')

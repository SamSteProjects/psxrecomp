import base64,json,os,struct,tempfile,unittest
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from importer.pipeline import import_scene
from importer.assets import load_model_source
from importer.field_equipment import project_field_equipment
from importer.animation import pose_vertices
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.field_equipment import preview,export,export_clip
from sdk.build import build_project
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb
from test_animation_clip_export import values

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class CurrentFieldEquipmentTests(unittest.TestCase):
 def test_saved_current_variants_and_exports(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save();originals={};cases=[]
   for slot in range(3):
    asset=f'asset://legaia/models/global-special/{240+slot:04x}';raw=load_model_source(p.disc_path,p.assets.records[asset]);originals[asset]=raw;edited=bytearray(raw);at=12+struct.unpack_from('<I',raw,12+28)[0];x=struct.unpack_from('<h',raw,at)[0];struct.pack_into('<h',edited,at,x+21);p.set_model_replacement(asset,bytes(edited))
   after=deepcopy(p._document());p.undo();p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);before=deepcopy((p._document(),p.undo_stack))
   with http_server(p) as (_,post):
    for slot in range(3):
     asset=f'asset://legaia/models/global-special/{240+slot:04x}'
     for byte in (0,1):
      for clip in (None,'idle','walk'):
       ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,equipment_byte=byte,clip_id=clip,frame_index=0 if clip else None);status,r=post('/api/field-equipment-current-preview',ctx);self.assertEqual(status,200,r);self.assertEqual(r['model_binding'],p.model_overrides[asset]);self.assertEqual(r['retail_model_sha256'],sha256(originals[asset]).hexdigest());current=p.read_model_replacement(asset,p.model_overrides[asset]);self.assertEqual(base64.b64decode(r['source_tmd_base64']),current);self.assertEqual(base64.b64decode(r['projected_tmd_base64']),project_field_equipment(current,slot,byte)[0]);retail=preview(p,**ctx);self.assertNotEqual(r['base_geometry']['vertices'],retail['base_geometry']['vertices'])
       if clip:self.assertEqual(r['geometry']['vertices'],pose_vertices(r['base_geometry']['vertices'],r['base_geometry']['objects'],r['geometry']['object_transforms']))
       exported=export(p,**ctx,model_layer='current');doc,binary=parse_glb(base64.b64decode(exported['glb_base64']));self.assertEqual(doc['extras']['source_record']['model_binding'],p.model_overrides[asset]);self.assertTrue(exported['filename'].startswith('current-model-'));g=r['geometry']
       for node in doc['nodes']:
        if 'mesh' not in node:continue
        obj=node['extras']['source_object']
        for primitive in doc['meshes'][node['mesh']]['primitives']:
         expected=[]
         for tri in range(obj['triangle_start'],obj['triangle_start']+obj['triangle_count']):
          if g['triangle_materials'][tri]!=primitive['material']:continue
          for c in (0,2,1):x,y,z=g['vertices'][g['triangles'][tri][c]];expected.append((x,-y,z))
         for a,b in zip(values(doc,binary,primitive['attributes']['POSITION']),expected):
          for v,w in zip(a,b):self.assertAlmostEqual(v,w,delta=.0002)
       full=export_clip(p,17.5,**ctx,model_layer='current') if clip else None
       if full:self.assertEqual(full['audit']['frame_count'],r['animation']['frame_count']);self.assertEqual(full['audit']['source_record']['model_binding'],r['model_binding'])
       cases.append(dict(context=dict(projectPath=str(p.root),sourceKey=source_key(p),assetId=asset,equipmentByte=byte,clipId=clip,frameIndex=0 if clip else None,modelLayer='current'),held=r,value=exported,full=full))
   self.assertEqual((p._document(),p.undo_stack),before);built=build_project(p);self.assertEqual((p._document(),p.undo_stack),before)
   output=os.getenv('LEGAIA_CURRENT_FIELD_CASES')
   if output:Path(output).write_text(json.dumps(dict(cases=cases,history=True,save_open=True,build_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')

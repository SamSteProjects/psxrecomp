import base64,json,os,struct,tempfile,unittest,zipfile
from copy import deepcopy
from pathlib import Path
from importer.pipeline import import_scene,_disc_context
from importer.core import parse_lzs_sections,decompress_lzs
from importer.textures import parse_tim
from importer.assets import load_model_source
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.field_equipment import preview,export
from sdk.build import build_project

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class SharedFieldTextureWorkflowTests(unittest.TestCase):
 def test_global_ownership_history_current_pixels_and_composed_package(self):
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save();asset='asset://legaia/models/global-special/00f0';raw=load_model_source(p.disc_path,p.assets.records[asset]);edited=bytearray(raw);at=12+struct.unpack_from('<I',raw,40)[0];struct.pack_into('<h',edited,at,struct.unpack_from('<h',raw,at)[0]+21);p.set_model_replacement(asset,bytes(edited));model_only=deepcopy(p._document());candidates={}
   for slot in range(8):
    identifier=f'texture://legaia/field-party/874/2/{slot}';ctx=p._texture_context(identifier);source=ctx.original_tim(identifier);tim=parse_tim(source);candidate=bytearray(source);candidate[20:20+len(tim.clut.data)]=struct.pack('<H',0x03e0)*(len(tim.clut.data)//2);candidate=bytes(candidate);p.set_texture_replacement(identifier,candidate);self.assertEqual(p.texture_overrides[identifier]['source_scene_id'],'field-party://textures');candidates[identifier]=candidate
   authored=deepcopy(p._document());self.assertEqual(len(p.undo_stack),9)
   for _ in range(8):p.undo()
   self.assertEqual(p._document(),model_only)
   for _ in range(8):p.redo()
   self.assertEqual(p._document(),authored);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),authored);self.assertFalse(p.dirty);cases=[];pixels=0
   for slot in range(3):
    for byte in (0,1):
     ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=f'asset://legaia/models/global-special/{240+slot:04x}',equipment_byte=byte,clip_id='walk',frame_index=0);current=preview(p,**ctx,model_layer='current');retail=preview(p,**ctx);self.assertEqual(current['base_geometry']['texture_layer'],'current');self.assertEqual(len(current['base_geometry']['texture_bindings']),8);self.assertNotEqual(current['geometry']['textures'],retail['geometry']['textures']);matched=0
     for texture in current['geometry']['textures']:
      if texture['status']!='address_match':continue
      rgba=base64.b64decode(texture['rgba_base64']);self.assertEqual(set(tuple(rgba[i:i+4]) for i in range(0,len(rgba),4)),{(0,255,0,255)});pixels+=len(rgba)//4;matched+=1
     self.assertGreater(matched,0);receipt=export(p,**ctx,model_layer='current');cases.append(dict(context=dict(projectPath=str(p.root),sourceKey=source_key(p),assetId=ctx['asset_id'],equipmentByte=byte,clipId='walk',frameIndex=0,modelLayer='current'),held=current,value=receipt,full=None))
   held=deepcopy((p._document(),p.undo_stack));built=build_project(p);self.assertEqual((p._document(),p.undo_stack),held);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
   with _disc_context(p.disc_path) as (_,_,_,archive),zipfile.ZipFile(built['path']) as package:
    body=archive.read_entry(archive.entry(874),extended=True);s=parse_lzs_sections(body)[2];section,consumed=decompress_lzs(body[s.stream_offset:],s.decoded_size);offset=(archive.node.extent_lba+archive.entry(874).start_lba)*2048+s.stream_offset;overlay=next(o for o in audit['overlays'] if o['offset']==offset);payload=package.read(overlay['file']);decoded=decompress_lzs(payload,s.decoded_size)[0]
    for identifier,candidate in candidates.items():
     source=p._texture_context(identifier).options(identifier)['source_record'];start=source['byte_offset'];self.assertEqual(decoded[start:start+len(candidate)],candidate)
    self.assertEqual((Path(built['package_directory'])/overlay['file']).read_bytes(),payload)
   output=os.getenv('LEGAIA_FIELD_TEXTURE_CASES')
   if output:Path(output).write_text(json.dumps(dict(cases=cases,pixels=pixels,history=True,save_open=True,composed_model_texture_build=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')

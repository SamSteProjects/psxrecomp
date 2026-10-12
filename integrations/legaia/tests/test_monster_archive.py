import base64,json,os,struct,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
from importer import monster_archive as native
from importer.pipeline import _disc_context
from sdk.project import ProjectService
from sdk.project_assets import source_key
from test_model_primitive_workflow import http_server

class MonsterArchiveBoundsTests(unittest.TestCase):
 def test_slot_and_stream_bounds(self):
  for identifier in (0,True,513):
   with self.assertRaises(native.ImportError):native.block(bytes(4),identifier)
  with self.assertRaises(native.ImportError):native.decode_catalog(bytes(4),'invalid')
  empty=native.decode_catalog(bytes(4),'a'*64)
  self.assertEqual(empty['models'],[]);self.assertEqual(empty['unavailable_slots'][0]['status'],'empty_or_unsupported_header')
  broken=native.decode_catalog(struct.pack('<I',0x4c),'a'*64)
  self.assertEqual(broken['models'],[]);self.assertEqual(broken['unavailable_slots'][0]['status'],'invalid_stream')

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterArchiveTests(unittest.TestCase):
 def test_catalog_and_source_vertex_preview(self):
  disc=os.environ['LEGAIA_DISC_BIN'];catalog=native.discover(disc)
  self.assertEqual(catalog['slot_count'],194);self.assertEqual(len(catalog['records']),186);self.assertEqual(len(catalog['models']),186);self.assertEqual(len(catalog['textures']),186);self.assertEqual(len(catalog['unavailable_slots']),8)
  with _disc_context(disc) as (_,digest,_,archive):
   raw=archive.read_entry(archive.entry(867))
   for row in catalog['records']:
    data,used=native.block(raw,row['monster_id']);self.assertEqual(row['stored_stats']['hp'],struct.unpack_from('<H',data,12)[0]);self.assertEqual(row['stored_stats']['mp'],struct.unpack_from('<H',data,16)[0]);self.assertEqual(row['source_record']['sha256'],sha256(data[:0x4c]).hexdigest());pool=data[row['texture_offset']:];self.assertIn(len(pool),(16864,33248));self.assertEqual(next(t for t in catalog['textures'] if t['monster_id']==row['monster_id'])['source_record']['sha256'],sha256(pool).hexdigest())
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=disc;p.save();context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));before=deepcopy((p._document(),p.undo_stack));values=[];texture_values=[]
   with http_server(p) as (_,post):
    status,report=post('/api/monster-resources',context);self.assertEqual(status,200,report)
    for identifier in (10,62,63):
     body=dict(context,asset_id=f'asset://legaia/models/monster-archive/{identifier:04d}',catalog_source_key=catalog['source_key'])
     status,value=post('/api/monster-preview',body);self.assertEqual(status,200,value);source=base64.b64decode(value['source_tmd_base64']);vertices=[]
     for i in range(struct.unpack_from('<I',source,8)[0]):
      offset,count=struct.unpack_from('<2I',source,12+i*28);vertices.extend([list(struct.unpack_from('<3h',source,12+offset+n*8)) for n in range(count)])
     self.assertEqual(value['geometry']['vertices'],vertices);self.assertEqual(sha256(source).hexdigest(),value['record']['source_record']['sha256']);values.append(value)
     for changed in (dict(body,catalog_source_key='0'*64),dict(body,expected_source_key='0'*64),dict(body,asset_id='asset://legaia/models/monster-archive/0000'),dict(body,palette_index=0)):
      self.assertEqual(post('/api/monster-preview',changed)[0],400)
    for identifier in (10,62,63):
     for palette in (0,14):
      body=dict(context,asset_id=f'texture://legaia/monster-archive/{identifier:04d}/pool',catalog_source_key=catalog['source_key'],palette_index=palette)
      status,value=post('/api/monster-texture-preview',body);self.assertEqual(status,200,value);pool=base64.b64decode(value['source_pool_base64']);decoded=base64.b64decode(value['preview']['rgba_base64']);mask=base64.b64decode(value['preview']['stp_base64']);width=value['record']['width']
      for index in range(width*256):
       nibble=pool[480+index//2]>>((index&1)*4)&15;word=struct.unpack_from('<H',pool,palette*32+nibble*2)[0];expected=bytes([((word>>(c*5))&31)*8+(((word>>(c*5))&31)>>2) for c in range(3)]+[0 if word==0 else 255]);self.assertEqual(decoded[index*4:index*4+4],expected);self.assertEqual(mask[index],word>>15)
      texture_values.append(value)
     for changed in (dict(body,palette_index=True),dict(body,palette_index=15),dict(body,catalog_source_key='0'*64)):
      self.assertEqual(post('/api/monster-texture-preview',changed)[0],400)
   self.assertEqual((p._document(),p.undo_stack),before)
   if os.getenv('LEGAIA_MONSTER_CASES'):Path(os.environ['LEGAIA_MONSTER_CASES']).write_text(json.dumps(dict(report=report,previews=values,texture_previews=texture_values,all_record_heads=True,source_vertices=True,unchanged=True,gameplay_verified=False)),encoding='utf-8')

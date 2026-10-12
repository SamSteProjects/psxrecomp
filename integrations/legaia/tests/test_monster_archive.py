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
  self.assertEqual(catalog['slot_count'],194);self.assertEqual(len(catalog['records']),186);self.assertEqual(len(catalog['models']),186);self.assertEqual(len(catalog['unavailable_slots']),8)
  with _disc_context(disc) as (_,digest,_,archive):
   raw=archive.read_entry(archive.entry(867))
   for row in catalog['records']:
    data,used=native.block(raw,row['monster_id']);self.assertEqual(row['stored_stats']['hp'],struct.unpack_from('<H',data,12)[0]);self.assertEqual(row['stored_stats']['mp'],struct.unpack_from('<H',data,16)[0]);self.assertEqual(row['source_record']['sha256'],sha256(data[:0x4c]).hexdigest())
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));p.disc_path=disc;p.save();context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));before=deepcopy((p._document(),p.undo_stack));values=[]
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
   self.assertEqual((p._document(),p.undo_stack),before)
   if os.getenv('LEGAIA_MONSTER_CASES'):Path(os.environ['LEGAIA_MONSTER_CASES']).write_text(json.dumps(dict(report=report,previews=values,all_record_heads=True,source_vertices=True,unchanged=True,gameplay_verified=False)),encoding='utf-8')

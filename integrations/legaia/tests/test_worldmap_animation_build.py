from hashlib import sha256
from types import SimpleNamespace
from pathlib import Path
import struct,tempfile
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_animation_binding import owner,COMPONENT,SCHEMA
from sdk.worldmap_animation_build import prepare
from sdk.build import build_report,package_change_kinds
from importer.core import parse_scene_assets,decompress_lzs
from importer.serialization import compress_lzs
from importer.worldmap_geometry import _slot
from importer.animation_bank_growth import grow_scene_animation_bank
from test_worldmap_object_animation import fixture
from test_project_workflow import synthetic_scene


class WorldAnimationBuildTests(TestCase):
 def test_typed_receipt_descriptor_and_all_siblings(self):
  _,bank,_=fixture();payloads=[bytes([i])*8 for i in range(1,8)];payloads[4]=bank;raw=bytearray(64);struct.pack_into('<2I',raw,0,7,0xabcddcba)
  for i,data in enumerate(payloads):struct.pack_into('<2I',raw,8+8*i,((i+1)<<24)|len(data),len(raw));raw.extend(compress_lzs(data))
  raw=bytes(raw);bundle=parse_scene_assets(raw,1,0);_,source=_slot(bundle,raw,4);disc='b'*64
  with tempfile.TemporaryDirectory() as root:
   p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+disc;p.import_metadata(doc)
   binding=dict(schema_version=SCHEMA,scene='map01',source_disc_sha256=disc,source_bank_sha256=sha256(bank).hexdigest(),entries={'0000':dict(source_record_sha256=sha256(bank[8:]).hexdigest(),edits=[dict(frame_index=0,object_index=0,translation=dict(x=2047))])});p.overrides[owner('map01')]={COMPONENT:binding}
   archive=SimpleNamespace(node=SimpleNamespace(extent_lba=10,size=len(raw)),entry=lambda index:SimpleNamespace(index=index,start_lba=0),image=SimpleNamespace(read_user=lambda *args:raw))
   with patch('sdk.worldmap_animation_binding.load_bank',return_value=(bank,source,disc)),patch('sdk.worldmap_animation_build._kingdom_table',return_value=(None,1,0,bundle,raw)),patch('sdk.worldmap_animation_build.locate_physical_span',return_value=dict(entry_index=1,offset_within_span=0,byte_offset=0,byte_length=len(raw))):
    requests,receipt,changes=prepare(p,archive)
    expected=bytearray(bank);expected[16]=255;expected[18]=7;self.assertEqual(requests[0]['bank'],bytes(expected));self.assertEqual(requests[0]['descriptor_index'],4);self.assertEqual(receipt['carriers'][0]['current_bank_sha256'],sha256(expected).hexdigest())
    output,_=grow_scene_animation_bank(raw,sha256(raw).hexdigest(),0,4,sha256(bank).hexdigest(),requests[0]['bank']);updated=parse_scene_assets(output,1,0)
    for i,data in enumerate(payloads):self.assertEqual(decompress_lzs(output[updated.descriptors[i].data_offset:],updated.descriptors[i].size)[0],bytes(expected) if i==4 else data)
    report=build_report(dict(edits=changes,validation={},overlays=[]));row=report['changes'][0];self.assertEqual((row['before'],row['after']),(1,2047));self.assertEqual(row['frame_index'],0);self.assertEqual(row['object_index'],0);self.assertTrue(row['shared_record']);self.assertEqual(package_change_kinds(changes),['World animation channels'])
    binding['source_bank_sha256']='0'*64
    with self.assertRaises(ProjectError):prepare(p,archive)

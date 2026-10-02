import struct,unittest
from importer.textures import TextureCatalog,Tim,TimBlock,associate_material

class MaterialMetadata(unittest.TestCase):
 def test_pixel_free_result_matches_same_address_evidence(self):
  catalog=TextureCatalog(scene='fixture',disc_sha256='a'*64)
  image=TimBlock(0,0,2,1,struct.pack('<2H',31,992));catalog.textures.append((Tim(16,image,None,16),dict(semantic_id='texture://fixture/0')))
  material=dict(textured=True,tpage=256,clut=0,semi_transparent=False)
  full=associate_material(catalog,material,(0,0,1,0));metadata=associate_material(catalog,material,(0,0,1,0),include_pixels=False)
  self.assertEqual(metadata,{key:value for key,value in full.items() if key not in ('rgba','stp')});self.assertEqual(metadata['status'],'address_match');self.assertEqual(metadata['source_ids'],['texture://fixture/0'])
  catalog.textures.append((Tim(16,TimBlock(0,0,2,1,struct.pack('<2H',0,0)),None,16),dict(semantic_id='texture://fixture/conflict')))
  conflict=associate_material(catalog,material,(0,0,1,0),include_pixels=False);self.assertEqual(conflict['status'],'ambiguous');self.assertNotIn('rgba',conflict)
  missing=associate_material(TextureCatalog(scene='empty',disc_sha256='a'*64),material,(0,0,1,0),include_pixels=False);self.assertEqual(missing['status'],'missing');self.assertNotIn('stp',missing)

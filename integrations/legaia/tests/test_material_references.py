import struct,unittest
import tempfile,json
from pathlib import Path
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.material_references import verified_catalog
from test_project_workflow import synthetic_scene
from importer.textures import TextureCatalog,Tim,TimBlock,associate_material

class MaterialMetadata(unittest.TestCase):
 def test_imported_cache_is_detached_bounded_and_source_keyed(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='source.bin';result=dict(models=[],unresolved_reference_count=0,limitations=[])
   with patch('sdk.material_references.discover',return_value=result) as discover:
    first=verified_catalog(p);first['models'].append({'changed':True});p.overrides={'unrelated':{}};self.assertEqual(verified_catalog(p)['models'],[]);self.assertEqual(discover.call_count,1)
    p.disc_path='different.bin';verified_catalog(p);self.assertEqual(discover.call_count,2);p.imports[p.active_scene]['scene']['name']='changed';verified_catalog(p);self.assertEqual(discover.call_count,3);self.assertEqual(len(p.assets.material_reference_catalogs),2)
    p.save();saved=json.loads((p.root/'project.legaia.json').read_text());self.assertNotIn('material_reference_catalogs',saved)
 def test_failed_verification_blocks_cached_reference_query(self):
  from sdk.asset_references import inspect
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='source.bin'
   with patch('importer.pipeline._disc_context') as context,patch('sdk.resources._verify',side_effect=ProjectError('Source changed')),patch('sdk.material_references.verified_catalog') as cached:
    with self.assertRaises(ProjectError):inspect(p,'scene://fixture')
    cached.assert_not_called()
 def test_discovery_source_drift_never_installs_cache(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='source.bin'
   def discover(project):project.disc_path='changed.bin';return dict(models=[],unresolved_reference_count=0,limitations=[])
   with patch('sdk.material_references.discover',side_effect=discover):
    with self.assertRaises(ProjectError):verified_catalog(p)
   self.assertEqual(p.assets.material_reference_catalogs,{})
   with patch('sdk.material_references.discover',return_value=dict(models=[],limitations=['x'*(8*1024*1024)])):
    with self.assertRaises(ProjectError):verified_catalog(p)
   self.assertEqual(p.assets.material_reference_catalogs,{})
 def test_pixel_free_result_matches_same_address_evidence(self):
  catalog=TextureCatalog(scene='fixture',disc_sha256='a'*64)
  image=TimBlock(0,0,2,1,struct.pack('<2H',31,992));catalog.textures.append((Tim(16,image,None,16),dict(semantic_id='texture://fixture/0')))
  material=dict(textured=True,tpage=256,clut=0,semi_transparent=False)
  full=associate_material(catalog,material,(0,0,1,0));metadata=associate_material(catalog,material,(0,0,1,0),include_pixels=False)
  self.assertEqual(metadata,{key:value for key,value in full.items() if key not in ('rgba','stp')});self.assertEqual(metadata['status'],'address_match');self.assertEqual(metadata['source_ids'],['texture://fixture/0'])
  catalog.textures.append((Tim(16,TimBlock(0,0,2,1,struct.pack('<2H',0,0)),None,16),dict(semantic_id='texture://fixture/conflict')))
  conflict=associate_material(catalog,material,(0,0,1,0),include_pixels=False);self.assertEqual(conflict['status'],'ambiguous');self.assertNotIn('rgba',conflict)
  missing=associate_material(TextureCatalog(scene='empty',disc_sha256='a'*64),material,(0,0,1,0),include_pixels=False);self.assertEqual(missing['status'],'missing');self.assertNotIn('stp',missing)

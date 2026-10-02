import tempfile,unittest,os,zipfile,tomllib
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_settings import view
from test_project_workflow import synthetic_scene

class ProjectSettings(unittest.TestCase):
 def test_name_history_persistence_noop_and_import_preservation(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.save();before=deepcopy(p.imports);original=p.name;key=view(p)['review_key']
   p.command(dict(type='rename_project',name='  SDK "Renamed"  ',review_key=key));self.assertEqual(p.name,'SDK "Renamed"');self.assertEqual(len(p.undo_stack),1);self.assertIn('Project name',p.unsaved_sections);self.assertEqual(p.imports,before)
   self.assertEqual(ProjectService.open(p.save()).name,p.name);p.undo();self.assertEqual(p.name,original);p.redo();self.assertEqual(p.name,'SDK "Renamed"')
   p.command(dict(type='rename_project',name=p.name,review_key=view(p)['review_key']));self.assertEqual(len(p.undo_stack),1)
   with self.assertRaises(ProjectError):p.command(dict(type='rename_project',name='Other',review_key=key))
   self.assertEqual(p.imports,before)
 def test_invalid_names_context_and_live_mode_reject_without_changes(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));original=p.name;command=dict(type='rename_project',name='Valid',review_key=view(p)['review_key'])
   for value in ['', ' '*10,'x'*121,'a\nb','\ud800',True,None]:
    with self.assertRaises(ProjectError):p.command({**command,'name':value})
   with self.assertRaises(ProjectError):p.command({**command,'path':'another-folder'})
   p.mode='live'
   with self.assertRaises(ProjectError):p.command(command)
   self.assertEqual(p.name,original);self.assertEqual(p.undo_stack,[])

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class ProjectNamePackage(unittest.TestCase):
 def test_non_bmp_name_remains_valid_toml_in_normal_build(self):
  from importer.pipeline import import_scene
  from sdk.build import build_project
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.command(dict(type='rename_project',name='SDK "Motion" \U0001f680',review_key=view(p)['review_key']));output=build_project(p)
   with zipfile.ZipFile(output['path']) as archive:manifest=tomllib.loads(archive.read('manifest.toml').decode('utf-8'))
   self.assertTrue(manifest['name'].startswith(p.name));self.assertEqual(manifest['target'][0]['game_id'],'SCUS-94254')

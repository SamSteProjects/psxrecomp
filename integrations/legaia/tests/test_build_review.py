import os,tempfile,unittest,hashlib,json,zipfile
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.build import authored_state_key,build_project
from sdk.build_review import review
from test_project_workflow import synthetic_scene

class BuildReview(unittest.TestCase):
 def test_blocked_drafts_are_retained_and_detached_assessment_is_explicit(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='source.bin';p.actor_drafts={'draft://one':{'retained':True}};before=deepcopy((p.imports,p.overrides,p.actor_drafts,p.undo_stack))
   def prepare(snapshot,output,review_only):self.assertEqual(snapshot.actor_drafts,{});self.assertTrue(review_only);return {'metadata':'review'}
   with patch('sdk.build_review._build_project',side_effect=prepare):r=review(p)
   self.assertFalse(r['normal_build_ready']);self.assertEqual(r['excluded_npc_draft_count'],1);self.assertEqual(r['blockers'][0]['owner_id'],'draft://one');self.assertEqual(before,(p.imports,p.overrides,p.actor_drafts,p.undo_stack));self.assertEqual(r['source_key'],authored_state_key(p));self.assertEqual(list(Path(directory).rglob('*')),[])
 def test_failed_serializer_and_stale_state_are_not_successful_reviews(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.import_metadata(synthetic_scene());p.disc_path='source.bin'
   with patch('sdk.build_review._build_project',side_effect=ProjectError('Invalid source span')):r=review(p)
   self.assertIsNone(r['assessment']);self.assertEqual(r['status'],'blocked');self.assertEqual(r['blockers'][0]['kind'],'serialization')
   def drift(*args,**kwargs):p.name='Changed';return {}
   with patch('sdk.build_review._build_project',side_effect=drift):
    with self.assertRaises(ProjectError):review(p)
 def test_stale_reviewed_build_rejects_before_packaging_and_preserves_previous_build(self):
  from sdk.server import EditorHandler
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));handler=object.__new__(EditorHandler);handler.server=SimpleNamespace(project=p,last_build='previous')
   with patch('sdk.build.build_project',side_effect=AssertionError('must not package')):
    for command in [{'review_key':'a'*64},{'unexpected':True}]:
     with self.assertRaises(ProjectError):handler._command('/api/build',command)
   self.assertEqual(handler.server.last_build,'previous')

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailBuildReview(unittest.TestCase):
 def test_no_outputs_and_same_serialized_audit_as_normal_build(self):
  from importer.pipeline import import_scene
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save();actor=p.imports[p.active_scene]['actors'][10];p.command(dict(type='set_transform',entity_id=actor['semantic_id'],position={'x':actor['imported_transform']['position']['x']+128}));p.actor_drafts={'draft://test':{'retained':True}};before=deepcopy((p.imports,p.overrides,p.actor_drafts,p.undo_stack));files={str(f.relative_to(p.root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.root.rglob('*') if f.is_file()}
   with patch('sdk.build._write_exact',side_effect=AssertionError('review must not write')),patch('sdk.build.subprocess.run',side_effect=AssertionError('review must not pack')):blocked=review(p)
   self.assertEqual(blocked['status'],'blocked');self.assertIsNotNone(blocked['assessment'],blocked['blockers']);self.assertEqual(before,(p.imports,p.overrides,p.actor_drafts,p.undo_stack));self.assertEqual(files,{str(f.relative_to(p.root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.root.rglob('*') if f.is_file()})
   snapshot=deepcopy(p);snapshot.actor_drafts={};ready=review(snapshot);self.assertTrue(ready['normal_build_ready']);output=build_project(snapshot);audit=Path(output['audit']).read_bytes();self.assertEqual(ready['assessment']['audit_sha256'],hashlib.sha256(audit).hexdigest());self.assertEqual(ready['assessment']['report'],output['report'])
   with zipfile.ZipFile(output['path']) as archive:self.assertEqual(ready['assessment']['manifest_sha256'],hashlib.sha256(archive.read('manifest.toml')).hexdigest())

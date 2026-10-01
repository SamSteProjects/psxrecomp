import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError,digest
from sdk.script_operand_bundle import parse,review
from test_project_workflow import synthetic_scene

A='scene://fixture/actors/man-p1/0001';B='scene://fixture/scripts/man-p2/0000'
class BundleTests(unittest.TestCase):
 def fixture(self,p):
  p.import_metadata(synthetic_scene());p.disc_path='fixture.bin'
  return dict(schema_version='legaia.script-operand-bundle.v1',scene_id=p.active_scene,source_import_sha256=digest(p.imports[p.active_scene]),owners=[dict(owner_id=owner,components={'ScriptFlags':{'entries':{'script://'+owner.removeprefix('scene://')+'/flag-bit/0000':{'bit':3}}}}) for owner in [A,B]])
 def owner_review(self,p,owner,content):
  file=json.loads(content);before=deepcopy(p.overrides.get(owner));after=deepcopy(before or {});after.update(file['components']);return dict(owner_id=owner,before=before,after=after,change_count=int(before!=after))
 def context(self,p,owner):
  class Context:
   def patch(self,entries):
    data=bytearray(16);at=3 if owner==A else 7;data[at]=next(iter(entries.values()))['bit'];return bytes(data),[{'decoded_byte_offset':at}]
  return Context()
 def test_atomic_two_owner_history_persistence_noop_and_stale(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));file=self.fixture(p);content=json.dumps(file);original=deepcopy(p.overrides)
   with patch('importer.pipeline._disc_context'),patch('sdk.resources._verify'),patch('sdk.script_operand_bundle.review_file',side_effect=self.owner_review),patch.object(ProjectService,'_flag_context',lambda project,owner:self.context(project,owner)):
    report=review(p,content);self.assertEqual(p.overrides,original);self.assertEqual(p.undo_stack,[]);self.assertEqual(report['owner_count'],2)
    p.command(dict(type='import_script_operand_bundle',content=content,review_key=report['review_key']));self.assertEqual(len(p.undo_stack),1);self.assertEqual(set(p.overrides),{A,B});self.assertEqual(ProjectService.open(p.save()).overrides,p.overrides)
    p.undo();self.assertEqual(p.overrides,original);p.redo();expected=deepcopy(p.overrides);same=review(p,content);p.command(dict(type='import_script_operand_bundle',content=content,review_key=same['review_key']));self.assertEqual(len(p.undo_stack),1)
    with self.assertRaises(ProjectError):p.command(dict(type='import_script_operand_bundle',content=content,review_key=report['review_key']))
    self.assertEqual(p.overrides,expected)
 def test_failure_on_last_owner_and_conflicting_byte_writes_are_atomic(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));file=self.fixture(p);content=json.dumps(file)
   def fail(p,owner,content):
    if owner==B:raise ProjectError('Unsupported source instruction')
    return self.owner_review(p,owner,content)
   with patch('importer.pipeline._disc_context'),patch('sdk.resources._verify'),patch('sdk.script_operand_bundle.review_file',side_effect=fail):
    with self.assertRaises(ProjectError):review(p,content)
    self.assertEqual(p.overrides,{});self.assertEqual(p.undo_stack,[])
   class Context:
    def patch(self,entries):
     data=bytes([next(iter(entries.values()))['bit']]);return data,[{'decoded_byte_offset':0}]
   file['owners'][1]['components']['ScriptFlags']['entries'][next(iter(file['owners'][1]['components']['ScriptFlags']['entries']))]['bit']=4
   with patch('importer.pipeline._disc_context'),patch('sdk.resources._verify'),patch('sdk.script_operand_bundle.review_file',side_effect=self.owner_review),patch.object(ProjectService,'_flag_context',return_value=Context()):
    with self.assertRaisesRegex(ProjectError,'conflicting'):review(p,json.dumps(file))
    self.assertEqual(p.overrides,{});self.assertEqual(p.undo_stack,[])
 def test_duplicate_unknown_and_owner_entry_bounds(self):
  with tempfile.TemporaryDirectory() as directory:
   p=ProjectService(Path(directory));file=self.fixture(p)
   for mutate in [lambda v:v['owners'].append(v['owners'][0]),lambda v:v.update(unknown=1),lambda v:v.update(owners=[v['owners'][0]]*129),lambda v:v['owners'][0]['components'].update(Unknown={'entries':{'x':{}}})]:
    bad=deepcopy(file);mutate(bad)
    with self.assertRaises(ProjectError):parse(json.dumps(bad))
   bad=deepcopy(file);bad['owners'][0]['components']['ScriptFlags']['entries']={str(index):{'bit':3} for index in range(257)}
   with self.assertRaises(ProjectError):parse(json.dumps(bad))
if __name__=='__main__':unittest.main()

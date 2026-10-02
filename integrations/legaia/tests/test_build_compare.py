import os,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.build_compare import compare_builds

def result(changes,source='a'*64):
 return {'report':{'changes':changes},'receipt':{'source_disc_sha256':source,'audit_sha256':'b'*64,'archive_sha256':'c'*64,'authored_state_key':'d'*64}}
def row(value,**extra):
 return dict(scene='town01',owner_id='actor://one',asset_id='actor://one',field='position.x',scope='initial-man-placement-only',before=0,after=value,**extra)

class BuildCompare(unittest.TestCase):
 def compare(self,p,left,right):
  with patch('sdk.build_compare.verify_build',side_effect=[left,right]),patch('sdk.build_compare._load',side_effect=[(left['receipt'],{}),(right['receipt'],{})]):return compare_builds(p,'a'*16,'b'*16)
 def test_exact_audit_comparison_distinguishes_missing_records_and_details(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));left=result([row(10),row(2,frame_index=1,object_index=0)]);right=result([row(20),row(2,frame_index=2,object_index=0)]);before=deepcopy((left,right));r=self.compare(p,left,right);self.assertEqual(r['difference_count'],3);self.assertEqual({x['status'] for x in r['differences']},{'different_audit','only_left_audit','only_right_audit'});self.assertFalse(r['gameplay_verified']);self.assertEqual(before,(left,right))
   left=result([row(2,coordinate_changes=[{'value':1}])]);right=result([row(2,coordinate_changes=[{'value':2}])]);self.assertEqual(self.compare(p,left,right)['difference_count'],1);self.assertEqual(self.compare(p,left,left)['unchanged_change_count'],1);self.assertEqual(self.compare(p,result([row(1)]),result([row(True)]))['difference_count'],1)
 def test_foreign_disc_duplicate_identity_and_same_build_reject(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d))
   for a,b in [(result([]),result([],'f'*64)),(result([row(1),row(2)]),result([]))]:
    with self.assertRaises(ProjectError):self.compare(p,a,b)
   with self.assertRaises(ProjectError):compare_builds(p,'a'*16,'a'*16)
 def test_context_drift_and_metadata_budget_reject(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));a=result([row(1)]);b=result([])
   with patch('sdk.build_compare.MAX_METADATA',1):
    with self.assertRaises(ProjectError):self.compare(p,a,b)
   def drift(*args):p.name='changed';return b
   calls=[]
   def verify(*args):calls.append(1);return a if len(calls)==1 else drift()
   with patch('sdk.build_compare.verify_build',side_effect=verify),patch('sdk.build_compare._load',return_value=(a['receipt'],{})):
    with self.assertRaises(ProjectError):compare_builds(p,'a'*16,'b'*16)
   with patch('sdk.build_compare.verify_build',side_effect=[a,b]),patch('sdk.build_compare._load',return_value=({'changed':True},{})):
    with self.assertRaises(ProjectError):compare_builds(p,'a'*16,'b'*16)

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailBuildCompare(unittest.TestCase):
 def test_verified_baseline_and_authored_package_compare_without_writes(self):
  from sdk.build import build_project
  from importer.pipeline import import_scene,_disc_context
  with tempfile.TemporaryDirectory() as d,_disc_context(os.environ['LEGAIA_DISC_BIN']):
   p=ProjectService(Path(d));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));baseline=build_project(p);actor=p.imports[p.active_scene]['actors'][10];p.command(dict(type='set_transform',entity_id=actor['semantic_id'],position={'x':actor['imported_transform']['position']['x']+64}));p.save();authored=build_project(p);before={str(f):f.read_bytes() for f in p.root.rglob('*') if f.is_file()};a=Path(baseline['audit']).parent.name;b=Path(authored['audit']).parent.name;r=compare_builds(p,a,b);self.assertEqual(r['difference_count'],1);self.assertEqual(r['differences'][0]['status'],'only_right_audit');self.assertEqual(r['differences'][0]['right']['after'],actor['imported_transform']['position']['x']+64);self.assertEqual(before,{str(f):f.read_bytes() for f in p.root.rglob('*') if f.is_file()});Path(authored['path']).write_bytes(b'corrupt')
   with self.assertRaises(ProjectError):compare_builds(p,a,b)

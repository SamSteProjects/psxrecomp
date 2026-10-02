import hashlib,json,os,tempfile,unittest,zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from sdk.build import build_project,authored_state_key
from sdk.build_history import list_builds,verify_build
from sdk.project import ProjectService,ProjectError

class BuildHistory(unittest.TestCase):
 def test_additional_input_receipt_is_exactly_bound_and_primary_is_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   p,i,directory,archive=self.fixture(Path(d));primary=(directory/'build-receipt.json').read_bytes();receipt=json.loads(primary);p.name='A second authored context';key=authored_state_key(p);receipt['authored_state_key']=key;(directory/'input-receipts').mkdir();candidate=directory/'input-receipts'/(key+'.json');candidate.write_text(json.dumps(receipt));self.assertTrue(list_builds(p)['builds'][0]['matches_current_inputs']);self.assertTrue(verify_build(p,i)['matches_current_inputs']);self.assertEqual(primary,(directory/'build-receipt.json').read_bytes());receipt['archive_sha256']='c'*64;candidate.write_text(json.dumps(receipt));self.assertEqual(list_builds(p)['builds'][0]['status'],'invalid')
 def test_history_scan_is_bounded_and_does_not_claim_newest(self):
  with tempfile.TemporaryDirectory() as d:
   p=ProjectService(Path(d));(p.root/'Builds').mkdir()
   for index in range(257):(p.root/'Builds'/f'{index:016x}').mkdir()
   result=list_builds(p);self.assertEqual(len(result['builds']),256);self.assertTrue(result['truncated']);self.assertEqual(result['coverage'],'project_Builds_only_identity_order')
   class Entries:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def __iter__(self):
     for index in range(4098):
      if index==4097:raise AssertionError('scan exceeded bound')
      yield SimpleNamespace(name=f'ignored-{index}')
   with patch('sdk.build_history.os.scandir',return_value=Entries()):
    result=list_builds(p);self.assertTrue(result['truncated']);self.assertEqual(result['builds'],[])
 def fixture(self,root):
  p=ProjectService(root);key=authored_state_key(p);h=lambda data:hashlib.sha256(data).hexdigest()
  payload=b'private test overlay';audit=dict(schema_version='legaia.build-audit.v1',disc_sha256='a'*64,build_kind='authored',edits=[],validation={'live_runtime':'not_run'},overlays=[dict(file='assets/test.bin',size=len(payload),offset=0,sha256=h(payload),expected_sha256='b'*64)])
  data=json.dumps(audit).encode();identifier=h(data+key.encode())[:16];directory=root/'Builds'/identifier;package=directory/'package';(package/'assets').mkdir(parents=True)
  manifest=(f'format_version=6\nid="legaia.sdk.123456789abc"\nversion="0.1.0-{identifier}"\n[[target]]\ngame_id="SCUS-94254"\ndisc_sha256="'+ 'a'*64+'"\n[[overlay]]\nfeature="placements"\ntarget="disc_user"\noffset=0\nfile="assets/test.bin"\nsha256="'+h(payload)+'"\nexpected_sha256="'+'b'*64+'"\n').encode()
  (package/'manifest.toml').write_bytes(manifest);(package/'assets/test.bin').write_bytes(payload);(directory/'build-audit.json').write_bytes(data)
  archive=directory/f'legaia.sdk.123456789abc-0.1.0-{identifier}.psxmod'
  with zipfile.ZipFile(archive,'w') as z:z.writestr('manifest.toml',manifest);z.writestr('assets/test.bin',payload)
  receipt=dict(schema_version='legaia.build-receipt.v1',authored_state_key=key,audit_sha256=h(data),manifest_sha256=h(manifest),archive_file=archive.name,archive_sha256=h(archive.read_bytes()),archive_bytes=archive.stat().st_size,package_id='legaia.sdk.123456789abc',version='0.1.0-'+identifier,source_disc_sha256='a'*64,build_kind='authored',runtime_status='package_built_not_launched',feature_id='placements')
  (directory/'build-receipt.json').write_text(json.dumps(receipt))
  return p,identifier,directory,archive
 def test_reopen_and_input_comparison_are_separate_from_integrity(self):
  with tempfile.TemporaryDirectory() as d:
   p,i,directory,archive=self.fixture(Path(d));p.save();p=ProjectService.open(Path(d));before={str(f):f.read_bytes() for f in Path(d).rglob('*') if f.is_file()}
   entry=list_builds(p)['builds'][0];self.assertTrue(entry['matches_current_inputs']);self.assertEqual(entry['integrity'],'not_checked');verified=verify_build(p,i);self.assertEqual(verified['integrity'],'verified');self.assertFalse(verified['gameplay_verified']);self.assertEqual(verified['source_disc_integrity'],'not_checked');self.assertEqual(before,{str(f):f.read_bytes() for f in Path(d).rglob('*') if f.is_file()})
   p.name='Changed';self.assertFalse(list_builds(p)['builds'][0]['matches_current_inputs']);self.assertFalse(verify_build(p,i)['matches_current_inputs'])
 def test_tampered_payload_archive_manifest_and_audit_reject(self):
  for target in ['package/assets/test.bin','package/manifest.toml','build-audit.json','archive']:
   with self.subTest(target=target),tempfile.TemporaryDirectory() as d:
    p,i,directory,archive=self.fixture(Path(d));file=archive if target=='archive' else directory/target;file.write_bytes(file.read_bytes()+b'X')
    with self.assertRaises(ProjectError):verify_build(p,i)
 def test_duplicate_ZIP_members_reject_even_with_updated_archive_hash(self):
  with tempfile.TemporaryDirectory() as d:
   p,i,directory,archive=self.fixture(Path(d))
   import warnings
   with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    with zipfile.ZipFile(archive,'a') as z:z.writestr('assets/test.bin',b'private test overlay')
   receipt=json.loads((directory/'build-receipt.json').read_text());receipt.update(archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),archive_bytes=archive.stat().st_size);(directory/'build-receipt.json').write_text(json.dumps(receipt))
   with self.assertRaises(ProjectError):verify_build(p,i)
 def test_legacy_invalid_and_path_guards(self):
  with tempfile.TemporaryDirectory() as d:
   p,i,directory,archive=self.fixture(Path(d));(directory/'build-receipt.json').unlink();entry=list_builds(p)['builds'][0];self.assertEqual(entry['status'],'legacy_or_incomplete');self.assertIsNone(entry['matches_current_inputs'])
   for identity in ['../escape','a'*16+'/x','A'*16]:
    with self.assertRaises(ProjectError):verify_build(p,identity)
   (directory/'build-receipt.json').write_text('{}');self.assertEqual(list_builds(p)['builds'][0]['status'],'invalid')
   # Windows reparse points and symlinks use the shared output boundary guard.
   import stat
   original=Path.lstat
   def reparse(path,*args,**kwargs):
    value=original(path,*args,**kwargs)
    if path==p.root/'Builds':return SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=0x400)
    return value
   with patch.object(Path,'lstat',reparse):
    with self.assertRaises(ProjectError):list_builds(p)

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailBuildHistory(unittest.TestCase):
 def test_actual_repeated_package_and_reopened_receipt(self):
  from importer.pipeline import import_scene,_disc_context
  with tempfile.TemporaryDirectory() as d,_disc_context(os.environ['LEGAIA_DISC_BIN']):
   p=ProjectService(Path(d));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(p.disc_path,'town01'));p.save();first=build_project(p);receipt=Path(first['receipt']).read_bytes();second=build_project(p);self.assertEqual(first['sha256'],second['sha256']);self.assertEqual(receipt,Path(second['receipt']).read_bytes());p=ProjectService.open(Path(d));entry=list_builds(p)['builds'][0];self.assertTrue(entry['matches_current_inputs']);verified=verify_build(p,entry['id']);self.assertEqual(verified['report'],first['report'])

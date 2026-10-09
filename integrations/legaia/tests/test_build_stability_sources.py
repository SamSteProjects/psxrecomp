from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json,os,tempfile,unittest
from unittest.mock import patch
from sdk.build_stability_sources import capture,validate
from sdk.project import ProjectError,ProjectService

class BuildSourceEvidence(unittest.TestCase):
 def test_deterministic_and_independent_hashes_with_explicit_drift(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'runtime.c').write_bytes(b'accepted runtime');expected=sha256(b'accepted runtime').hexdigest()
   manifest=dict(schema_version='legaia.stability-source-manifest.v1',basis_revision='a'*40,release_reference_revision='b'*40,comparison_receipt_sha256='c'*64,execution_evidence_date='2026-10-04',files=[dict(path='runtime.c',category='source_sha256',expected_sha256=expected)])
   first=capture(root,manifest);self.assertEqual(first,capture(root,manifest));self.assertNotIn('checked_at',first);self.assertEqual(first['files'][0]['actual_sha256'],expected)
   (root/'runtime.c').write_bytes(b'new runtime');changed=capture(root,manifest);self.assertFalse(changed['all_matched']);self.assertEqual(changed['files'][0]['status'],'changed');self.assertEqual(changed['files'][0]['actual_sha256'],sha256(b'new runtime').hexdigest())
   self.assertEqual(validate(changed),changed);(root/'runtime.c').unlink();missing=capture(root,manifest);self.assertEqual(missing['files'][0]['status'],'missing');self.assertIsNone(missing['files'][0]['actual_sha256'])
 def test_scope_hash_summary_path_and_extra_field_refusal(self):
  base=capture()
  for mutate in [lambda v:v.update(runtime_binary_verified=True),lambda v:v.update(gameplay_verified=True),lambda v:v.update(execution_repeated=True),lambda v:v.update(checked_at='2026-10-09'),lambda v:v.update(all_matched=not v['all_matched']),lambda v:v['files'][0].update(path='../outside'),lambda v:v['files'][0].update(actual_sha256='d'*64),lambda v:v['files'][0].update(status='missing'),lambda v:v['files'].append(deepcopy(v['files'][0])),lambda v:v['files'][0].update(extra=True)]:
   value=deepcopy(base);mutate(value)
   with self.assertRaises(ProjectError):validate(value)

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailBuildSourceEvidence(unittest.TestCase):
 def project(self,root):
  from importer.pipeline import import_scene
  p=ProjectService(root);p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN']);p.save();return p
 def test_review_build_saved_verification_exact_stamp_and_reproducibility(self):
  from sdk.build import build_project
  from sdk.build_review import review
  from sdk.build_history import verify_build
  with tempfile.TemporaryDirectory() as folder:
   p=self.project(Path(folder));before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports));a=review(p);self.assertTrue(a['normal_build_ready']);expected=capture();self.assertEqual(a['assessment']['report']['validation']['runtime_source_inclusion'],expected)
   built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));self.assertEqual(a['assessment']['audit_sha256'],sha256(Path(built['audit']).read_bytes()).hexdigest());self.assertEqual(audit['validation']['runtime_source_inclusion'],expected)
   identifier=Path(built['audit']).parent.name;verified=verify_build(p,identifier);self.assertEqual(verified['report']['validation']['runtime_source_inclusion'],expected);self.assertEqual(built['path'],build_project(p)['path']);self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack,p.imports))
 def test_mid_serialization_and_mid_packing_drift_refuse_receipt(self):
  from sdk.build import build_project,BuildError
  with tempfile.TemporaryDirectory() as folder:
   p=self.project(Path(folder));first=capture();changed=deepcopy(first);changed['files'][0].update(actual_sha256='d'*64,status='changed');changed['all_matched']=False
   for sequence in [[first,changed],[first,first,changed]]:
    with patch('sdk.build_stability_sources.capture',side_effect=sequence):
     with self.assertRaisesRegex(BuildError,'stability sources changed'):build_project(p)
    self.assertEqual(list(p.root.glob('Builds/*/build-receipt.json')),[])

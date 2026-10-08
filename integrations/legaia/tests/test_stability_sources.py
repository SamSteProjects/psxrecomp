from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from sdk.stability_sources import audit_stability_sources


class StabilitySourcesTests(unittest.TestCase):
    def manifest(self, files):
        return dict(schema_version='legaia.stability-source-manifest.v1', basis_revision='a'*40,
                    release_reference_revision='b'*40, execution_evidence_date='2026-10-04',
                    comparison_receipt_sha256='c'*64, files=files)

    def test_match_changed_missing_and_oversized_are_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'source.c').write_bytes(b'original');expected=sha256(b'original').hexdigest()
            manifest=self.manifest([dict(path='source.c',category='source_sha256',expected_sha256=expected)])
            self.assertTrue(audit_stability_sources(root,manifest)['all_matched'])
            (root/'source.c').write_bytes(b'changed');report=audit_stability_sources(root,manifest)
            self.assertEqual(report['files'][0]['status'],'changed');self.assertFalse(report['all_matched']);self.assertEqual((root/'source.c').read_bytes(),b'changed')
            (root/'source.c').unlink();self.assertEqual(audit_stability_sources(root,manifest)['files'][0]['status'],'missing')
            (root/'source.c').write_bytes(b'x'*(2*1024*1024+1));self.assertEqual(audit_stability_sources(root,manifest)['files'][0]['status'],'oversized')
            self.assertFalse(report['execution_repeated']);self.assertFalse(report['runtime_binary_verified']);self.assertFalse(report['gameplay_verified'])

    def test_manifest_refuses_paths_and_duplicate_or_missing_identity(self):
        base=self.manifest([dict(path='source.c',category='source_sha256',expected_sha256='d'*64)])
        for path in ['../outside','C:/outside','/outside','a\\b','a/./b','a//b','']:
            bad=deepcopy(base);bad['files'][0]['path']=path
            with self.assertRaises(ValueError):audit_stability_sources(manifest=bad)
        for mutate in [lambda m:m['files'].append(deepcopy(m['files'][0])),lambda m:m['files'][0].update(expected_sha256=3),lambda m:m.update(basis_revision='unknown'),lambda m:m.update(files=[]),lambda m:m['files'][0].update(extra=True)]:
            bad=deepcopy(base);mutate(bad)
            with self.assertRaises(ValueError):audit_stability_sources(manifest=bad)

    def test_recorded_manifest_current_inclusion(self):
        report=audit_stability_sources();self.assertEqual(len(report['files']),8)
        self.assertTrue(report['all_matched'],report['files']);self.assertEqual(report['scope'],'recorded_source_inclusion_only')

if __name__=='__main__':unittest.main()

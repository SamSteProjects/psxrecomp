from copy import deepcopy
from contextlib import nullcontext
from unittest.mock import patch
import base64,unittest
from sdk import model_mesh_library
from sdk.project import ProjectError
from test_model_mesh_source_retention import MeshSourceTests
from test_model_primitive_workflow import http_server
import test_model_mesh_append as fixtures

class MeshLibraryTests(unittest.TestCase):
    def fixture(self):
        helper=MeshSourceTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture();content=fixtures.glb();helper.apply(p,asset,donor,content,new_group=True)
        self.enterContext(patch('importer.pipeline._disc_context',lambda path:nullcontext()))
        return p,asset,content

    def test_recovery_exact_http_no_changes_and_stale_keys(self):
        p,asset,raw=self.fixture();held=deepcopy((p._document(),p.undo_stack,p.redo_stack));files={str(f):f.read_bytes() for f in p.root.rglob('*') if f.is_file()}
        value=model_mesh_library.library(p,str(p.root));self.assertEqual(value['receipt_count'],1);row=value['imports'][0];self.assertEqual(row['receipt'],p.model_overrides[asset]['mesh_imports'][0])
        body=dict(expected_project_path=str(p.root),expected_library_key=value['library_key'],receipt_key=row['receipt']['receipt_key'])
        with http_server(p) as (_,post):
            status,catalog=post('/api/mesh-source-library',dict(expected_project_path=str(p.root)));self.assertEqual(status,200,catalog);self.assertEqual(catalog,value)
            status,result=post('/api/mesh-library-download',body);self.assertEqual(status,200,result);self.assertEqual(base64.b64decode(result['content_base64']),raw);self.assertEqual(result['selected'],row)
            for extra in ({'expected_project_path':'wrong'},{'expected_library_key':'b'*64},{'receipt_key':'b'*64},{'path':'arbitrary'}):self.assertEqual(post('/api/mesh-library-download',{**body,**extra})[0],400)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held);self.assertEqual({str(f):f.read_bytes() for f in p.root.rglob('*') if f.is_file()},files)
        p.mode='live';self.assertNotEqual(model_mesh_library.library(p,str(p.root))['library_key'],value['library_key'])
        with self.assertRaises(ProjectError):model_mesh_library.download(p,**body)

    def test_missing_corrupt_input_and_late_native_change_reject(self):
        p,asset,raw=self.fixture();row=p.model_overrides[asset]['mesh_imports'][0];path=p.root/'Authored/Models/Sources'/(row['glb_sha256']+'.glb');path.write_bytes(bytes(len(raw)))
        with self.assertRaises(ProjectError):model_mesh_library.library(p,str(p.root))
        path.write_bytes(raw);original=model_mesh_library.model_mesh_sources.catalog
        def mutate(*args):
            value=original(*args);p.mode='live';return value
        with patch.object(model_mesh_library.model_mesh_sources,'catalog',side_effect=mutate):
            with self.assertRaisesRegex(ProjectError,'changed during verification'):model_mesh_library.library(p,str(p.root))

    def test_empty_library_and_explicit_global_budget(self):
        p,asset,raw=self.fixture()
        with patch.object(model_mesh_library,'MAX_RECEIPTS',0):
            with self.assertRaisesRegex(ProjectError,'128 receipts'):model_mesh_library.library(p,str(p.root))
        with patch.object(model_mesh_library,'MAX_BYTES',len(raw)-1):
            with self.assertRaisesRegex(ProjectError,'64 MiB'):model_mesh_library.library(p,str(p.root))
        p.model_overrides={};self.assertEqual(model_mesh_library.library(p,str(p.root))['imports'],[])

if __name__=='__main__':unittest.main()

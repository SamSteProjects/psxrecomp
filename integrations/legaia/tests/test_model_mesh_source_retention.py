"""Original mesh inputs survive native authoring and fail closed on corruption."""
from copy import deepcopy
from hashlib import sha256
import base64,json,unittest,zipfile
from unittest.mock import patch
from sdk import model_mesh_append,model_mesh_batch,model_mesh_sources,model_face_removal
from sdk.project import ProjectService,ProjectError,digest
from sdk.build import build_project
from test_model_primitive_workflow import http_server
import test_model_mesh_append as fixtures

class MeshSourceTests(unittest.TestCase):
    def fixture(self):
        helper=fixtures.MeshAppendTests();self.addCleanup(helper.doCleanups)
        p,asset,donor=helper.fixture()
        self.enterContext(patch('sdk.model_mesh_batch.source_key',return_value='a'*64))
        self.enterContext(patch('sdk.model_face_removal.source_key',return_value='a'*64))
        return p,asset,donor

    def apply(self,p,asset,donor,content,**settings):
        source=model_mesh_append.source(p,asset,'a'*64)
        report=model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64,**settings)
        p.apply_model_mesh_append(asset,content,donor,source['effective_sha256'],'a'*64,report['review_key'],**settings)
        return report

    def test_review_retention_history_reopen_http_and_build(self):
        p,asset,donor=self.fixture();content=fixtures.glb(normals=[[0,1,0]]*4)
        source=model_mesh_append.source(p,asset,'a'*64);before=deepcopy(p._document());history=len(p.undo_stack)
        model_mesh_append.review(p,asset,content,donor,source['effective_sha256'],'a'*64)
        self.assertFalse((p.root/'Authored/Models/Sources').exists())
        report=self.apply(p,asset,donor,content,source_rotation=[90,0,0],source_offset=[120,50,-30])
        binding=p.model_overrides[asset];receipt=binding['mesh_imports'][0]
        self.assertEqual(receipt['glb_sha256'],sha256(content).hexdigest());self.assertEqual(receipt['recipe']['source_rotation'],[90,0,0])
        self.assertEqual(len(p.undo_stack),history+1)
        p.undo();self.assertEqual(p._document(),before);p.redo();p.save()
        with patch.object(ProjectService,'_model_source',side_effect=p._model_source):
            reopened=ProjectService.open(p.root);self.assertEqual(reopened.read_model_replacement(asset,reopened.model_overrides[asset]),p.read_model_replacement(asset,binding))
        state=deepcopy((p._document(),p.undo_stack,p.redo_stack))
        with http_server(p) as (_,post):
            body=dict(asset_id=asset,source_key='a'*64)
            status,catalog=post('/api/model-mesh-sources',body);self.assertEqual(status,200,catalog);self.assertEqual(catalog['imports'],[receipt])
            status,download=post('/api/model-mesh-source-download',{**body,'receipt_key':receipt['receipt_key']});self.assertEqual(status,200,download);self.assertEqual(base64.b64decode(download['content_base64']),content)
            for extra in ({'source_key':'b'*64},{'receipt_key':'b'*64},{'path':'arbitrary'}):
                self.assertEqual(post('/api/model-mesh-source-download',{**body,'receipt_key':receipt['receipt_key'],**extra})[0],400)
        self.assertEqual((p._document(),p.undo_stack,p.redo_stack),state)
        out=build_project(p)
        with zipfile.ZipFile(out['path']) as archive:self.assertFalse(any(name.endswith('.glb') for name in archive.namelist()))
        self.assertEqual(binding['asset_sha256'],report['proposed_sha256'])

    def test_multiple_mapped_sources_and_later_face_removal_preserve_receipts(self):
        p,asset,donor=self.fixture();self.apply(p,asset,donor,fixtures.glb(),new_group=True)
        source=model_mesh_append.source(p,asset,'a'*64);content=fixtures.glb(lambda d:d['meshes'][0]['primitives'].append(deepcopy(d['meshes'][0]['primitives'][0])))
        mappings=[dict(primitive_index=i,donor_face_id=donor,replace_group=False) for i in range(2)]
        args=(asset,content,mappings,source['effective_sha256'],'a'*64)
        report=model_mesh_batch.review(p,*args);model_mesh_batch.apply(p,*args,review_key=report['review_key'])
        receipts=deepcopy(p.model_overrides[asset]['mesh_imports']);self.assertEqual(len(receipts),2)
        source=model_face_removal.source(p,asset,'a'*64)
        selection=[dict(object_index=0,primitive_index=0)]
        report=model_face_removal.review(p,asset,selection,source['effective_sha256'],'a'*64)
        p.apply_model_face_removal(asset,selection,source['effective_sha256'],'a'*64,report['proposed_sha256'])
        self.assertEqual(p.model_overrides[asset]['mesh_imports'],receipts)
        p.read_model_replacement(asset,p.model_overrides[asset])

    def test_vector_allocation_and_native_shape_edit_preserve_source_spans(self):
        from sdk import model_vector_allocation
        p,asset,donor=self.fixture();self.apply(p,asset,donor,fixtures.glb())
        receipts=deepcopy(p.model_overrides[asset]['mesh_imports'])
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        requests=[dict(object_index=0,kind='vertices',vectors=[[321,123,-45]])]
        with patch('sdk.model_vector_allocation.source_key',return_value='a'*64):
            report=model_vector_allocation.review(p,asset,requests,sha256(current).hexdigest(),'a'*64)
            p.apply_model_vector_allocations(asset,requests,sha256(current).hexdigest(),'a'*64,report['proposed_sha256'])
        self.assertEqual(p.model_overrides[asset]['mesh_imports'],receipts)
        current=p.read_model_replacement(asset,p.model_overrides[asset])
        p.translate_model_object(asset,0,[1,-2,3],sha256(current).hexdigest())
        self.assertEqual(p.model_overrides[asset]['mesh_imports'],receipts)
        p.read_model_replacement(asset,p.model_overrides[asset])

    def test_missing_changed_source_and_resealed_recipe_reject_native_read(self):
        p,asset,donor=self.fixture();content=fixtures.glb();self.apply(p,asset,donor,content)
        binding=p.model_overrides[asset];receipt=binding['mesh_imports'][0]
        path=p.root/'Authored/Models/Sources'/(receipt['glb_sha256']+'.glb')
        path.write_bytes(content[:-1]+b'x')
        with self.assertRaises(ProjectError):p.read_model_replacement(asset,binding)
        path.unlink()
        with self.assertRaises(ProjectError):p.read_model_replacement(asset,binding)
        path.write_bytes(content)
        altered=deepcopy(binding);row=altered['mesh_imports'][0];row['recipe']['source_offset']=[100,0,0];row['receipt_key']=digest({k:v for k,v in row.items() if k!='receipt_key'})
        with self.assertRaises(ProjectError):p.read_model_replacement(asset,altered)
        altered=deepcopy(binding);altered['mesh_imports'][0]['first_operation']+=1
        with self.assertRaises(ProjectError):p.read_model_replacement(asset,altered)
        p.read_model_replacement(asset,binding)

if __name__=='__main__':unittest.main()

from copy import deepcopy
from hashlib import sha256
import unittest
from pathlib import Path
from unittest.mock import patch
from sdk.project import ProjectService,ProjectError
from sdk.scene_preview import source_key
from sdk.model_vertex_groups import review,review_key,binding
from sdk import model_vector_allocation
import test_model_primitive_workflow as fixtures
import test_model_vector_allocation_project as allocation_fixtures
from test_model_primitive_workflow import ASSET,http_server

class VertexGroupLibraryTests(unittest.TestCase):
    def fixture(self):
        h=fixtures.ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups);return h,h.project
    def create(self,p,asset,owner,members,name='Region'):
        original=p._model_source(asset,p.active_scene);current=p.read_model_replacement(asset,p.model_overrides[asset]) if asset in p.model_overrides else original
        p.command(dict(type='create_model_vertex_group',asset_id=asset,object_index=owner,indices=members,name=name,expected_sha256=sha256(current).hexdigest(),source_key=source_key(p)))
        return next(v for v in p.model_vertex_groups.values() if v['name']==name)

    def test_commands_recall_coordinate_edit_history_save_open_copy_and_reimport(self):
        h,p=self.fixture();files=h.snapshot()[1];row=self.create(p,ASSET,0,[2,0]);self.assertEqual(row['indices'],[0,2]);self.assertIsNone(row['allocation_key']);self.assertFalse(p.model_overrides);self.assertEqual(h.snapshot()[1],files)
        self.assertIn('Saved model vertex groups',p.unsaved_sections);before=deepcopy(p._document());report=review(p,row['id'],review_key(p,row),source_key(p));self.assertTrue(report['read_only']);self.assertEqual(p._document(),before)
        p.set_model_vector(ASSET,0,'vertices',0,[16,2,3],sha256(h.source).hexdigest());self.assertEqual(review(p,row['id'],review_key(p,row),source_key(p))['indices'],[0,2])
        p.command(dict(type='rename_model_vertex_group',group_id=row['id'],review_key=review_key(p,row),name='Wall edge'));renamed=deepcopy(p.model_vertex_groups[row['id']]);self.assertEqual(renamed['name'],'Wall edge');p.undo();self.assertEqual(p.model_vertex_groups[row['id']],row);p.redo()
        p.command(dict(type='delete_model_vertex_group',group_id=row['id'],review_key=review_key(p,renamed)));self.assertFalse(p.model_vertex_groups);p.undo();self.assertEqual(p.model_vertex_groups[row['id']],renamed)
        p.save();opened=ProjectService.open(p.root);self.assertEqual(opened.model_vertex_groups,p.model_vertex_groups);self.assertNotIn('Saved model vertex groups',p.unsaved_sections)
        from sdk.project_copy import review as review_copy,create_copy
        copy=create_copy(p,'Selection copy',review_copy(p)['review_key']);self.assertEqual(ProjectService.open(Path(copy['copied_project'])).model_vertex_groups,p.model_vertex_groups)
        metadata=deepcopy(p.imports[p.active_scene]);metadata['actors'][0]['name']='Changed evidence'
        with self.assertRaises(ProjectError):p.import_metadata(metadata,str(h.root/'fixture.bin'))

    def test_http_read_only_and_reject_forged_stale_duplicate_ownership(self):
        h,p=self.fixture();row=self.create(p,ASSET,0,[0,2]);before=deepcopy(p._document());key=source_key(p)
        with http_server(p) as (_,post):
            body=dict(group_id=row['id'],review_key=review_key(p,row),source_key=key)
            self.assertEqual(post('/api/model-vertex-group-review',body)[0],200)
            for change in ({'extra':0},{'review_key':'0'*64},{'source_key':'0'*64},{'group_id':None}):self.assertEqual(post('/api/model-vertex-group-review',dict(body,**change))[0],400)
        self.assertEqual(p._document(),before)
        for members in [[],[0,0],[99],[True],[-1]]:
            with self.assertRaises((ProjectError,ValueError)):self.create(p,ASSET,0,members,'Other')
            self.assertEqual(p._document(),before)
        with self.assertRaises(ProjectError):self.create(p,ASSET,0,[1],'region')
        malformed=deepcopy(row);malformed['source_sha256']='bad';p.model_vertex_groups[row['id']]=malformed;p.save()
        with self.assertRaises(ProjectError):ProjectService.open(p.root)

    def test_allocated_rows_keep_birth_fingerprint_and_reject_reallocation(self):
        h=allocation_fixtures.VectorAllocationProjectTests();self.addCleanup(h.doCleanups);p,asset=h.fixture()
        # Fixture pins the allocation service key independently of the scene key.
        with patch('sdk.model_vertex_groups.source_key',return_value='a'*64),patch('sdk.scene_preview.source_key',return_value='a'*64):
            source=model_vector_allocation.source(p,asset,'a'*64);requests=h.requests();candidate=model_vector_allocation.review(p,asset,requests,source['effective_sha256'],'a'*64);p.apply_model_vector_allocations(asset,requests,source['effective_sha256'],'a'*64,candidate['proposed_sha256'])
            count=source['objects'][0]['vertex_count'];current=model_vector_allocation.source(p,asset,'a'*64)
            p.command(dict(type='create_model_vertex_group',asset_id=asset,object_index=0,indices=[count],name='New row',expected_sha256=current['effective_sha256'],source_key='a'*64));row=next(iter(p.model_vertex_groups.values()));self.assertIsNotNone(row['allocation_key'])
            p.set_model_vector(asset,0,'vertices',count,[110,210,310],current['effective_sha256']);self.assertEqual(review(p,row['id'],review_key(p,row),'a'*64)['indices'],[count])
            current=model_vector_allocation.source(p,asset,'a'*64);next_review=model_vector_allocation.review(p,asset,requests,current['effective_sha256'],'a'*64);p.apply_model_vector_allocations(asset,requests,current['effective_sha256'],'a'*64,next_review['proposed_sha256'])
            with self.assertRaises(ProjectError):review(p,row['id'],review_key(p,row),'a'*64)

if __name__=='__main__':unittest.main()

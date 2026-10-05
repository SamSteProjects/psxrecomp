"""Movement source retains an immutable Retail baseline across Apply/history."""
from hashlib import sha256
import unittest
from importer.assets import decode_tmd
from sdk.scene_preview import source_key
from sdk import model_vector_allocation
import test_model_vector_allocation_project as allocation_fixtures
import test_model_primitive_workflow as fixtures
from test_model_primitive_workflow import ASSET, http_server

class RetailMovementTests(unittest.TestCase):
    def test_appended_rows_do_not_extend_retail_tables(self):
        h=allocation_fixtures.VectorAllocationProjectTests();self.addCleanup(h.doCleanups)
        p,asset=h.fixture();original=p._model_source(asset,p.active_scene)
        initial=model_vector_allocation.source(p,asset,'a'*64)
        requests=h.requests()
        report=model_vector_allocation.review(p,asset,requests,initial['effective_sha256'],'a'*64)
        p.apply_model_vector_allocations(asset,requests,initial['effective_sha256'],'a'*64,report['proposed_sha256'])
        current=model_vector_allocation.source(p,asset,'a'*64)
        self.assertEqual(current['retail_preview'],decode_tmd(original))
        self.assertEqual(current['retail_preview'],initial['retail_preview'])
        self.assertEqual(current['preview']['objects'][0]['vertex_count'],initial['preview']['objects'][0]['vertex_count']+2)
        self.assertEqual(current['objects'][0]['normal_count'],initial['objects'][0]['normal_count']+2)

    def test_retail_current_and_read_only_http_across_history(self):
        h=fixtures.ModelPrimitiveProjectWorkflow();h.setUp();self.addCleanup(h.doCleanups)
        p=h.project;retail=decode_tmd(h.source)
        values=retail['vertices'][1].copy();values[0]+=16
        p.set_model_vector(ASSET,0,'vertices',1,values,sha256(h.source).hexdigest())
        with http_server(p) as (_,post):
            for action in (None,'undo','redo'):
                if action:getattr(p,action)()
                before=h.snapshot()
                status,report=post('/api/model-vector-allocation-source',dict(asset_id=ASSET,source_key=source_key(p)))
                self.assertEqual(status,200)
                self.assertEqual(report['retail_preview'],retail)
                self.assertEqual(report['source_sha256'],sha256(h.source).hexdigest())
                self.assertEqual(report['preview'],decode_tmd(h.effective()))
                self.assertEqual(report['effective_sha256'],sha256(h.effective()).hexdigest())
                self.assertEqual(report['preview']['vertices'][1],retail['vertices'][1] if action=='undo' else values)
                self.assertEqual(h.snapshot(),before)
                self.assertFalse(report['project_changed'])

if __name__=='__main__':unittest.main()

import os, tempfile, unittest
from copy import deepcopy
from test_animation_glb_workflow import http_server
import test_animation_glb_workflow as fixtures
from sdk.animation_range_review import reverse_range
from sdk.scene_preview import source_key

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class ReverseReview(unittest.TestCase):
    def test_source_bound_readonly_http_review(self):
        with tempfile.TemporaryDirectory() as directory:
            p=fixtures.AnimationGlbWorkflow().project(directory);owner='scene://town01/actors/man-p1/0011'
            held=deepcopy((p._document(),p.imports,p.undo_stack,p.redo_stack))
            request=dict(entity_id=owner,start=0,end=4,object_index=0,expected_source_key=source_key(p))
            with http_server(p) as (_,post):
                status,report=post('/api/animation-range-reverse-review',request)
                self.assertEqual(status,200,report);self.assertFalse(report['project_changed']);self.assertEqual(len(report['proposed']),5)
                frame=p.animation_frame_values(owner,4)['effective'][0]
                self.assertEqual(report['proposed'][0]['translation'],frame['translation']);self.assertEqual(report['proposed'][0]['rotation_psx'],frame['rotation_psx'])
                for change in [dict(expected_source_key='0'*64),dict(start=True),dict(end=0),dict(object_index=True),dict(extra=1)]:
                    status,bad=post('/api/animation-range-reverse-review',dict(request,**change));self.assertNotEqual(status,200,bad)
            self.assertEqual((p._document(),p.imports,p.undo_stack,p.redo_stack),held)

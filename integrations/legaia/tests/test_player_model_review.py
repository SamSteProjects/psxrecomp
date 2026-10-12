import os,tempfile,base64,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.player_battle import resources
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerModelReviewTests(unittest.TestCase):
    def test_http_native_review_noop_changes_and_stale_refusals(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];held=deepcopy((p._document(),p.undo_stack));ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p));r=resources(p,**ctx)
            with http_server(p) as (_,post):
                for m in r['catalog']['models']:
                    args=dict(ctx,asset_id=m['semantic_id'],catalog_source_key=r['catalog']['source_key'],equipped=[0]*5);status,e=post('/api/player-model-glb-export',args);self.assertEqual(status,200,e)
                    status,v=post('/api/player-model-glb-review',dict(args,binding=e['binding'],glb_base64=e['glb_base64']));self.assertEqual(status,200,v);self.assertFalse(v['projection']['changes']);self.assertEqual(v['projection']['source_sha256'],v['projection']['proposed_sha256'])
                    doc,binary=_read_glb(base64.b64decode(e['glb_base64']));doc['nodes'][0]['translation']=[10,0,0];content=base64.b64encode(_write_glb(doc,binary)).decode();request=dict(args,binding=e['binding'],glb_base64=content);status,v=post('/api/player-model-glb-review',request);self.assertEqual(status,200,v);self.assertTrue(v['projection']['changes']);self.assertEqual(v['layer'],'proposed');self.assertEqual(v['persistence'],'not_applied')
                for change in [dict(expected_source_key='0'*64),dict(catalog_source_key='0'*64),dict(asset_id='foreign'),dict(equipped=[255]*5),dict(glb_base64='bad'),dict(extra=True)]:self.assertEqual(post('/api/player-model-glb-review',dict(request,**change))[0],400)
            self.assertEqual((p._document(),p.undo_stack),held)

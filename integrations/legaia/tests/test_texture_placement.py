"""Static placement search and source-bound, read-only native planning."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64, os, tempfile, unittest
from unittest.mock import patch
from types import SimpleNamespace
from sdk.texture_placement import find_placement, suggest, upload_map
from sdk.scene_preview import source_key
from sdk.project import ProjectService, ProjectError
from importer.texture_png import _encode_png
from importer.texture_image_conversion import convert_png
from sdk.texture_slots import _footprint, native_upload_rectangles
import test_texture_slots_workflow as workflow
from test_model_primitive_workflow import http_server

class PlacementSearch(unittest.TestCase):
    def test_exact_static_exclusion_image_palette_and_no_fit(self):
        self.assertEqual(native_upload_rectangles((960,456,256,1)),[(960,456,64,1),(0,456,192,1)])
        self.assertEqual(native_upload_rectangles((1023,511,2,2)),[(1023,511,1,1),(1023,0,1,1),(0,511,1,1),(0,0,1,1)])
        result=find_placement(4,8,16,[(0,0,10,8),(0,511,16,1)])
        self.assertEqual(result['placement'],dict(image_x=10,image_y=0,clut_x=16,clut_y=511))
        self.assertEqual(find_placement(1024,512,0,[])['placement'],dict(image_x=0,image_y=0,clut_x=0,clut_y=0))
        self.assertEqual(find_placement(1024,512,16,[])['status'],'no_fit')
        self.assertEqual(find_placement(1,1,0,[(0,0,1024,512)])['status'],'no_fit')
        # A palette that would overlap the image is skipped in favor of an aligned peer.
        self.assertEqual(find_placement(8,1,16,[(0,0,1024,511)])['placement'],dict(image_x=0,image_y=511,clut_x=16,clut_y=511))
        with patch('sdk.texture_placement.MAX_PAIR_CHECKS',0):
            result=find_placement(8,1,16,[]);self.assertEqual(result['status'],'search_budget_exhausted');self.assertFalse(result['search_complete'])
        for rectangle in [(1020,0,8,1),(0,-1,1,1),(0,0,True,1)]:
            with self.assertRaises(ProjectError):find_placement(4,8,16,[rectangle])

class PlacementWorkflow(unittest.TestCase):
    def setup_project(self):
        return workflow.TextureSlotsWorkflow.setup_project(self)
    def test_wrapped_boot_tail_blocks_authored_slot_review(self):
        project,context,_,_,_=self.setup_project()
        upload=SimpleNamespace(x=960,y=456,width_words=256,height=1)
        png=_encode_png(8,8,bytes([255,0,0,255]*64))
        candidate,_=convert_png(png,dict(bpp=16,image_x=0,image_y=456,clut_x=0,clut_y=0,stp_mode='opaque'))
        with patch.object(context._catalog,'boot_uploads',[(upload,{})]):
            report=_footprint(project,context,candidate)
        self.assertTrue(any(row['kind']=='boot-upload' and row['rectangle']==dict(x=0,y=456,width_words=192,height=1) and row['overlap_words']==8 for row in report['rows']))
    def test_http_plan_then_separate_conversion_review_preserves_project(self):
        project,context,_,_,ids=self.setup_project();png=_encode_png(8,8,bytes([255,0,0,255]*64));key=source_key(project);before=deepcopy(project._document())
        with http_server(project) as (_,post):
            body=dict(asset_id=ids[0],source_key=key,png_base64=base64.b64encode(png).decode(),bpp=4)
            status,result=post('/api/texture-placement',body);self.assertEqual(status,200,result);self.assertEqual(result['status'],'found')
            status,mapped=post('/api/texture-upload-map',dict(asset_id=ids[0],source_key=key));self.assertEqual(status,200,mapped)
            self.assertEqual(mapped['occupancy_sha256'],result['occupancy_sha256']);self.assertEqual(len(mapped['rectangles']),result['known_rectangle_count'])
            status,_=post('/api/texture-upload-map',dict(asset_id=ids[0],source_key='0'*64));self.assertEqual(status,400)
            status,_=post('/api/texture-upload-map',dict(asset_id=ids[0],source_key=key,extra=True));self.assertEqual(status,400)
            self.assertEqual(result['png_sha256'],sha256(png).hexdigest());self.assertFalse(result['runtime_residency_verified']);self.assertTrue(result['read_only'])
            candidate,_=convert_png(png,dict(bpp=4,**result['placement'],stp_mode='opaque'))
            self.assertEqual(_footprint(project,context,candidate)['potential_overlap_count'],0)
            status,_=post('/api/texture-placement',{**body,'source_key':'0'*64});self.assertEqual(status,400)
            status,_=post('/api/texture-placement',{**body,'extra':True});self.assertEqual(status,400)
        self.assertEqual(project._document(),before)

    @unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
    def test_native_current_coverage_and_fresh_project_preserved(self):
        from importer.pipeline import import_scene
        from sdk.resources import refresh_resource_catalog
        with tempfile.TemporaryDirectory() as raw:
            p=ProjectService(Path(raw));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'vell'),os.environ['LEGAIA_DISC_BIN']);catalog=refresh_resource_catalog(p);anchor=next(row['id'] for row in catalog['records'] if row['kind']=='texture' and row['id'].startswith('texture://vell/'))
            png=_encode_png(8,8,bytes([255,0,0,255]*64));before=deepcopy(p._document());result=suggest(p,anchor,source_key(p),png,4)
            mapped=upload_map(p,anchor,source_key(p));self.assertEqual(mapped['occupancy_sha256'],result['occupancy_sha256'])
            self.assertTrue(any(row['kind']=='boot-upload' and row['rectangle']==dict(x=0,y=456,width_words=192,height=1) for row in mapped['rectangles']))
            self.assertIn(result['status'],('found','no_fit'));self.assertGreater(result['known_rectangle_count'],0)
            if result['status']=='found':
                candidate,_=convert_png(png,dict(bpp=4,**result['placement'],stp_mode='opaque'));self.assertEqual(_footprint(p,p._texture_context(anchor),candidate)['potential_overlap_count'],0)
            self.assertEqual(p._document(),before)

"""Native authored scene membership, coordinate layers and pre-read refusal."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import base64
import struct
import tempfile
from unittest import TestCase
from unittest.mock import patch

from importer.core import ImportError
from importer.worldmap_placements import decode_worldmap_placements
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_current_placements import compose,inspect
from sdk.worldmap_placement_allocation import review
from test_project_workflow import synthetic_scene
from test_worldmap_placement_allocation import fixture,request
from test_model_primitive_workflow import http_server


def setup(project):
    raw,floor=fixture();doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;project.import_metadata(doc)
    provenance=dict(scene='map01',source_disc_sha256='b'*64,source_map_sha256=sha256(raw).hexdigest(),source_floor_lut_sha256='c'*64)
    context=(raw,provenance,{},0,floor,None,raw,[])
    seeds=decode_worldmap_placements(raw,floor,scene='map01')['placements']
    records={f"{s['object_record_index']:04d}":dict(source_record_sha256=s['source_record_sha256'],placements=[p for p in seeds if p['object_record_index']==s['object_record_index']]) for s in seeds}
    context=(raw,provenance,records,0,floor,None,raw,seeds)
    geometry=dict(scene='map01',source_record=dict(disc_sha256='b'*64,map_sha256=sha256(raw).hexdigest(),floor_lut_sha256='c'*64),
        scene_graph=dict(entities=[dict(entity_id='scene://map01/worldmap/ground',placement_scope='source_ground',asset_id='ground')]+
            [dict(s,asset_id='asset://map01/worldmap/models/0001',renderable=True) for s in seeds],
            assets=[dict(asset_id='ground',preview=dict(triangles=[[0,1,2]])),
                dict(asset_id='asset://map01/worldmap/models/0001',preview=dict(triangles=[[0,1,2]]))],
            metrics=dict(entity_count=3,drawn_triangle_count=3),coverage=dict(candidate_count=2,resolved_count=2,rendered_count=2),limitations=[]))
    return raw,floor,context,geometry


class CurrentWorldPlacementTests(TestCase):
    def test_current_and_proposed_graph_preserve_retail_and_distinct_authored_identity(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));raw,floor,native,geometry=setup(p);held=deepcopy(geometry)
            with patch('sdk.worldmap_placement_allocation.context',return_value=native),patch('sdk.worldmap_current_placements.context',return_value=native):
                r=review(p,'map01',state_key(p),[request()]);p.command(dict(type='allocate_worldmap_placements',scene='map01',source_key=state_key(p),requests=[request()],review_key=r['review_key']))
                before=deepcopy(p._document());history=deepcopy((p.undo_stack,p.redo_stack))
                composed=deepcopy(geometry);meta=compose(p,composed);author=composed['scene_graph']['entities'][-1]
                self.assertEqual(author['entity_id'],'scene://map01/worldmap/authored-placements/00000000-0000-4000-8000-000000000001')
                self.assertEqual(author['native_entity_id'],'scene://map01/worldmap/placements/00c8');self.assertIsNone(author['retail_source_position'])
                seed=decode_worldmap_placements(base64.b64decode(r['proposed_map_base64']),floor,scene='map01')['placements'][-1]
                self.assertEqual(author['source_position'],seed['source_position']);self.assertEqual(author['source_to_world'],seed['source_to_world'])
                self.assertEqual(composed['scene_graph']['metrics'],dict(entity_count=4,drawn_triangle_count=4))
                self.assertEqual(meta['exported_map_sha256'],r['proposed_map_sha256']);self.assertEqual(geometry,held)
                proposal=review(p,'map01',state_key(p),[request(5,201,2)])
                with patch('sdk.worldmap_geometry.inspect',return_value=deepcopy(geometry)):
                    view=inspect(p,'map01',state_key(p),dict(requests=[request(5,201,2)],review_key=proposal['review_key']))
                self.assertEqual(view['representation'],'proposed-source');self.assertEqual(len(view['scene_graph']['entities']),5)
                self.assertTrue(view['authored_geometry'])
                self.assertEqual(p._document(),before);self.assertEqual((p.undo_stack,p.redo_stack),history)

    def test_foreign_source_missing_model_stale_and_http_fields_fail_before_claiming_scene(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));raw,floor,native,geometry=setup(p)
            with patch('sdk.worldmap_placement_allocation.context',return_value=native),patch('sdk.worldmap_current_placements.context',return_value=native):
                r=review(p,'map01',state_key(p),[request()]);p.command(dict(type='allocate_worldmap_placements',scene='map01',source_key=state_key(p),requests=[request()],review_key=r['review_key']))
                wrong=deepcopy(geometry);wrong['source_record']['map_sha256']='0'*64
                with self.assertRaises(ProjectError):compose(p,wrong)
                wrong=deepcopy(geometry);wrong['scene_graph']['assets'].pop()
                with self.assertRaises(ProjectError):compose(p,wrong)
                with patch('sdk.worldmap_geometry.inspect',side_effect=AssertionError('stale scene must not inspect geometry')):
                    with self.assertRaises(ProjectError):inspect(p,'map01','0'*64)
                    with self.assertRaises(ProjectError):inspect(p,'map01',state_key(p),dict(requests=[request(5,201,2)],review_key='0'*64))
                with http_server(p) as (_,post):
                    self.assertEqual(post('/api/worldmap-placement-scene',dict(scene='map01',source_key=state_key(p),extra=True))[0],400)
                    self.assertEqual(post('/api/worldmap-placement-scene',dict(scene='map01',source_key='0'*64))[0],400)

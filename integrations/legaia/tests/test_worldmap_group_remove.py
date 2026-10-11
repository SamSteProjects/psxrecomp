"""Group removal preserves descendants and source bytes with one history entry."""
from copy import deepcopy
from pathlib import Path
import base64, tempfile
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_placement_remove import review
from sdk.worldmap_placement_allocation_binding import COMPONENT, owner
from test_worldmap_decoration_group import group_fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class WorldDecorationGroupRemovalTests(TestCase):
    def test_v1_v2_chain_survivor_and_last_owner_http_history(self):
        for model in (False, True):
            for count in (2, 3):
                with self.subTest(model=model,count=count), tempfile.TemporaryDirectory() as root:
                    raw,floor,provenance,rows,current,binding=group_fixture(model)
                    p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc)
                    p.overrides[owner('map01')]={COMPONENT:binding};p.save()
                    held=deepcopy(p._document());history=deepcopy(p.undo_stack)
                    context=(raw,provenance,{},48,floor,None,raw,[])
                    with patch('sdk.worldmap_placement_allocation.context',return_value=context),patch('sdk.worldmap_placement_remove.context',return_value=context):
                        key=state_key(p);ids=sorted(r['placement_id'] for r in rows[:count]);receipt=review(p,'map01',key,ids)
                        self.assertEqual(receipt['schema_version'],'legaia.worldmap-decoration-removal-review.v2')
                        expected=bytearray(current)
                        for row in rows[:count]:
                            at=row['record_index']*32;cell=0x8000+row['target_cell']*2
                            expected[at:at+32]=raw[at:at+32];expected[cell:cell+2]=raw[cell:cell+2]
                        self.assertEqual(base64.b64decode(receipt['proposed_map_base64']),bytes(expected))
                        self.assertEqual(p._document(),held);self.assertEqual(p.undo_stack,history)
                        if count==2:
                            survivor=receipt['audit']['remaining_allocations'][0]
                            self.assertEqual(survivor['placement_id'],rows[2]['placement_id'])
                            self.assertEqual(survivor['donor_cell'],rows[0]['donor_cell'])
                            self.assertEqual(survivor['model_pool_index'],2 if model else 1)
                        else:self.assertIsNone(receipt['binding'])
                        command=dict(type='remove_worldmap_authored_placements',scene='map01',source_key=key,placement_ids=ids,review_key=receipt['review_key'])
                        with http_server(p) as (_,post):
                            self.assertEqual(post('/api/worldmap-decoration-removal-review',dict(scene='map01',source_key=key,placement_ids=ids))[0],200)
                            self.assertEqual(post('/api/worldmap-decoration-removal-review',dict(scene='map01',source_key=key,placement_ids=ids[0]))[0],400)
                            self.assertEqual(post('/api/command',{**command,'review_key':'0'*64})[0],400)
                            self.assertEqual(post('/api/command',command)[0],200)
                            self.assertEqual(post('/api/command',command)[0],400)
                        applied=deepcopy(p._document());self.assertEqual(len(p.undo_stack),len(history)+1)
                        p.save();self.assertEqual(ProjectService.open(Path(root))._document(),applied)
                        p.undo();self.assertEqual(p._document(),held);p.redo();self.assertEqual(p._document(),applied);p.undo();self.assertEqual(p.undo_stack,history)
                        for bad in ([],ids[::-1],[ids[0],ids[0]],['foreign'],[True]):
                            with self.assertRaises(ProjectError):review(p,'map01',state_key(p),bad)
                        self.assertEqual(p._document(),held)

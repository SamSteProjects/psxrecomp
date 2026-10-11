from copy import deepcopy
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.worldmap_authoring import state_key
from sdk.build import authored_state_key
from sdk.worldmap_selection_sets import review, review_key, validate, AUTHORED_SCHEMA
from test_worldmap_decoration_group import group_fixture
from test_project_workflow import synthetic_scene
from test_model_primitive_workflow import http_server


class AuthoredWorldSelectionTests(TestCase):
    def test_http_metadata_only_history_persistence_and_owner_continuity(self):
        _,_,provenance,requests,_,_=group_fixture()
        allocations=[dict(placement_id=r['placement_id'],record_index=r['record_index']) for r in requests]
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));doc=synthetic_scene();doc['source']['disc_identity']='sha256:'+'b'*64;p.import_metadata(doc);p.save()
            ids=sorted(r['placement_id'] for r in requests[:2]);key=state_key(p);native=authored_state_key(p);held=deepcopy(p._document())
            with patch('sdk.worldmap_selection_sets._context',return_value=(None,provenance,None,None,allocations)):
                command=dict(type='create_worldmap_authored_selection_set',scene='map01',source_key=key,placement_ids=ids[::-1],name='Trees')
                with http_server(p) as (_,post):
                    self.assertEqual(post('/api/command',{**command,'record_ids':['0009']})[0],400)
                    self.assertEqual(post('/api/command',command)[0],200)
                    self.assertEqual(post('/api/command',command)[0],400)
                row=next(iter(p.worldmap_selection_sets.values()));self.assertEqual(row['schema_version'],AUTHORED_SCHEMA);self.assertEqual(row['placement_ids'],ids)
                self.assertEqual(authored_state_key(p),native);self.assertEqual(state_key(p),key)
                applied=deepcopy(p._document());p.save();self.assertEqual(ProjectService.open(Path(root))._document(),applied)
                p.undo();self.assertEqual(p._document(),held);p.redo();self.assertEqual(p._document(),applied)
                receipt=review(p,row['id'],review_key(p,row),key);self.assertEqual(receipt['selection'],row)
                moved=deepcopy(allocations)
                for a in moved:a.update(target_cell=16000,model_pool_index=2,native_seed=dict(source_position=dict(x=1,y=2,z=3)))
                with patch('sdk.worldmap_selection_sets._context',return_value=(None,provenance,None,None,moved)):
                    self.assertEqual(review(p,row['id'],review_key(p,row),key)['selection'],row)
                for changed in (allocations[1:], [{**a,'record_index':300} for a in allocations]):
                    with patch('sdk.worldmap_selection_sets._context',return_value=(None,provenance,None,None,changed)),self.assertRaises(ProjectError):review(p,row['id'],review_key(p,row),key)
                with self.assertRaises(ProjectError):review(p,row['id'],'0'*64,key)
                with self.assertRaises(ProjectError):review(p,row['id'],review_key(p,row),'0'*64)
                with http_server(p) as (_,post):
                    self.assertEqual(post('/api/worldmap-selection-review',dict(selection_set_id=row['id'],review_key=review_key(p,row),source_key=key,extra=True))[0],400)
                    self.assertEqual(post('/api/worldmap-selection-review',dict(selection_set_id=row['id'],review_key=review_key(p,row),source_key=key))[0],200)
                p.command(dict(type='update_worldmap_authored_selection_set',selection_set_id=row['id'],review_key=review_key(p,row),source_key=key,placement_ids=[requests[2]['placement_id']]))
                latest=deepcopy(p.worldmap_selection_sets[row['id']]);self.assertEqual(latest['placement_ids'],[requests[2]['placement_id']])
                with self.assertRaises(ProjectError):p.command(dict(type='update_worldmap_selection_set',selection_set_id=row['id'],review_key=review_key(p,latest),source_key=key,record_ids=['0009']))
                p.command(dict(type='rename_worldmap_selection_set',selection_set_id=row['id'],review_key=review_key(p,latest),name='Renamed'))
                latest=p.worldmap_selection_sets[row['id']];p.command(dict(type='delete_worldmap_selection_set',selection_set_id=row['id'],review_key=review_key(p,latest)))
                self.assertFalse(p.worldmap_selection_sets);p.undo();self.assertEqual(p.worldmap_selection_sets[row['id']],latest)

    def test_exact_saved_domains_and_immutable_provenance(self):
        _,_,provenance,requests,_,_=group_fixture();identifier='worldmap-selection://00000000-0000-4000-8000-000000000001'
        placement=requests[0]['placement_id'];row=dict(id=identifier,name='Trees',scene='map01',source_record=provenance,
            placement_ids=[placement],bindings={placement:dict(record_index=4,entity_id='scene://map01/worldmap/authored-placements/'+placement.rsplit('/',1)[1])},schema_version=AUTHORED_SCHEMA)
        validate(None,identifier,row)
        maximum=deepcopy(row);maximum['placement_ids']=[f'placement://authored/00000000-0000-4000-8000-{i:012x}' for i in range(32)]
        maximum['bindings']={id:dict(record_index=4+i,entity_id='scene://map01/worldmap/authored-placements/'+id.rsplit('/',1)[1]) for i,id in enumerate(maximum['placement_ids'])}
        validate(None,identifier,maximum)
        too_many=deepcopy(maximum);too_many['placement_ids'].append('placement://authored/00000000-0000-4000-8000-000000000020')
        with self.assertRaises(ProjectError):validate(None,identifier,too_many)
        for mutate in (lambda v:v.update(extra=True),lambda v:v.update(schema_version='unknown'),lambda v:v['placement_ids'].append(placement),
                lambda v:v['bindings'][placement].update(record_index=True),lambda v:v['bindings'][placement].update(entity_id='foreign'),
                lambda v:v['source_record'].update(source_map_sha256='bad'),lambda v:v.update(record_ids=['0004'])):
            bad=deepcopy(row);mutate(bad)
            with self.assertRaises(ProjectError):validate(None,identifier,bad)

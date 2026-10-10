from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from sdk.project import AssetDatabase, ProjectError
from sdk.worldmap_asset_index import inspect, references

H='a'*64
class WorldmapAssetIndexTests(unittest.TestCase):
    def setUp(self):
        self.project=SimpleNamespace(root=Path('fixture'),assets=AssetDatabase(),active_scene='scene://field',imports={},overrides={})
        self.values=dict(offset=dict(x=10,y=-20,z=30),yaw_units=64)
    def context(self,view,scene):
        members=[dict(entity_id=f'scene://{scene}/worldmap/placements/{i:04x}',source_cell=i,object_record_index=1,source_record_sha256=H) for i in (3,4)]
        row=dict(record_id='0001',object_record_index=1,source_record_sha256=H,source_cell_count=2,placements=members,writable=True,retail_values=self.values,current_values=self.values,authored_values=None)
        return b'raw',dict(scene=scene,source_disc_sha256=H,source_map_sha256=H,source_floor_lut_sha256=H),{'0001':row},0,[],None,b'current',[]
    def run_index(self,callback=None):
        with patch('sdk.worldmap_asset_index.source_key',return_value=H),patch('sdk.worldmap_asset_index.context',side_effect=callback or self.context):return inspect(self.project,H)
    def test_global_ownership_and_detachment(self):
        held=deepcopy(vars(self.project));value=self.run_index();self.assertEqual(value['coverage'],dict(kingdom_count=3,asset_count=12,reference_count=9,native_record_count=3,qualified_seed_count=6));self.assertTrue(all(r['scene_id'] is None for r in value['assets']));self.assertEqual(self.project.active_scene,held['active_scene']);self.assertEqual(self.project.overrides,held['overrides']);self.assertEqual({e['target_id'] for e in value['references']},{r['id'] for r in value['assets']}-set(value['roots']));value['assets'][0]['name']='changed';self.assertEqual(self.values['offset']['x'],10)
    def test_stale_and_unknown_key_refuse_before_read(self):
        with patch('sdk.worldmap_asset_index.source_key',return_value=H),patch('sdk.worldmap_asset_index.context') as read:
            for key in (None,0,'0'*64,'short'):
                with self.assertRaises(ProjectError):inspect(self.project,key)
            read.assert_not_called()
    def test_ownership_and_layer_refusal(self):
        def bad(field,value):
            def callback(view,scene):
                result=list(self.context(view,scene));result[2]['0001'][field]=value;return tuple(result)
            return callback
        for callback in (bad('source_cell_count',3),bad('current_values',dict(offset=dict(x=11,y=-20,z=30),yaw_units=64)),bad('placements',[dict(entity_id='scene://map01/actors/0001',source_cell=3,object_record_index=1,source_record_sha256=H)])):
            with self.assertRaises(ProjectError):self.run_index(callback)
    def test_incomplete_ownership_remains_explicit(self):
        def partial(view,scene):
            result=list(self.context(view,scene));result[2]['0001'].update(writable=False,source_cell_count=3);return tuple(result)
        result=self.run_index(partial);self.assertTrue(all(not r['complete_ownership'] for r in result['assets'] if r['resource_role']=='native_source_record'))
    def test_changed_source_during_read_refuses_result(self):
        with patch('sdk.worldmap_asset_index.source_key',side_effect=[H,H,'b'*64]),patch('sdk.worldmap_asset_index.context',side_effect=self.context):
            with self.assertRaises(ProjectError):inspect(self.project,H)
    def test_reference_neighborhoods_retain_exact_full_graph(self):
        held=deepcopy(vars(self.project))
        with patch('sdk.worldmap_asset_index.source_key',return_value=H),patch('sdk.worldmap_asset_index.context',side_effect=self.context):
            for scene in ('map01','map02','map03'):
                for identifier in (f'worldmap://{scene}/placements',f'worldmap://{scene}/placements/records/0001',f'scene://{scene}/worldmap/placements/0003'):
                    result=references(self.project,identifier,H);graph=result['global_worldmap_index']
                    self.assertEqual(result['incoming'],[e for e in graph['references'] if e['target_id']==identifier])
                    self.assertEqual(result['outgoing'],[e for e in graph['references'] if e['source_id']==identifier])
                    self.assertEqual(graph['coverage']['asset_count'],12)
                    self.assertTrue(result['read_only']);self.assertEqual(result['asset_id'],identifier)
        self.assertEqual(self.project.overrides,held['overrides']);self.assertEqual(self.project.active_scene,held['active_scene'])
    def test_reference_identity_and_final_source_refusal(self):
        with patch('sdk.worldmap_asset_index.context') as read:
            for identifier in (None,5,'scene://field/actors/0001','worldmap://map04/placements','worldmap://map01/placements/records/0001/extra'):
                with self.assertRaises(ProjectError):references(self.project,identifier,H)
            read.assert_not_called()
        with patch('sdk.worldmap_asset_index.source_key',return_value=H),patch('sdk.worldmap_asset_index.context',side_effect=self.context):
            with self.assertRaises(ProjectError):references(self.project,'worldmap://map01/placements/records/0999',H)
        with patch('sdk.worldmap_asset_index.source_key',side_effect=[H]*4+['b'*64]),patch('sdk.worldmap_asset_index.context',side_effect=self.context):
            with self.assertRaises(ProjectError):references(self.project,'worldmap://map01/placements',H)
if __name__=='__main__':unittest.main()

from copy import deepcopy
import unittest
from unittest.mock import patch
from sdk.project import ProjectError
from sdk.worldmap_reference_trace import assemble, inspect, edge_id
import test_worldmap_asset_index as fixtures
H=fixtures.H


class GlobalTraceTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.WorldmapAssetIndexTests();self.fixture.setUp()
        self.graph=self.fixture.run_index()

    def test_owned_paths_reverse_owners_and_detachment(self):
        held=deepcopy(self.graph)
        for scene in ('map01','map02','map03'):
            root=f'worldmap://{scene}/placements';seed=f'scene://{scene}/worldmap/placements/0003'
            forward=assemble(self.graph,root,'outgoing',2)
            self.assertEqual(len(forward['rows']),3)
            self.assertEqual([len(r['edge_ids']) for r in forward['rows']],[1,2,2])
            self.assertEqual(forward['expanded_ids'],[root,root+'/records/0001'])
            reverse=assemble(self.graph,seed,'incoming',2)
            self.assertEqual(reverse['rows'][-1]['node_ids'],[seed,root+'/records/0001',root])
            shallow=assemble(self.graph,root,'outgoing',1)
            self.assertEqual(len(shallow['rows']),1);self.assertEqual(shallow['rows'][0]['stop'],'depth_limit')
            self.assertEqual(len({edge_id(e) for e in self.graph['references']}),len(self.graph['references']))
        forward['global_worldmap_index']['assets'][0]['name']='changed'
        self.assertEqual(self.graph,held)

    def test_controls_and_source_changes_refuse(self):
        with patch('sdk.worldmap_reference_trace.references') as discovery:
            for direction,depth,layer in [('outgoing',True,'derived'),('bad',2,'derived'),('incoming',5,'derived'),('outgoing',2,'authored')]:
                with self.assertRaises(ProjectError):inspect(self.fixture.project,self.graph['roots'][0],direction,depth,layer,H)
            discovery.assert_not_called()
        with patch('sdk.worldmap_reference_trace.references',return_value={'global_worldmap_index':self.graph}),patch('sdk.worldmap_reference_trace.source_key',return_value='b'*64):
            with self.assertRaises(ProjectError):inspect(self.fixture.project,self.graph['roots'][0],'outgoing',2,'derived',H)

    def test_row_and_expansion_limits_keep_complete_graph(self):
        graph=deepcopy(self.graph);root=graph['roots'][0]
        # A broad qualified source graph exercises traversal independently of retail parsing.
        for i in range(200):
            identifier=f'worldmap://map01/placements/records/{i+10:04d}'
            graph['assets'].append({'id':identifier})
            graph['references'].append(dict(source_id=root,target_id=identifier,kind='owns_native_source_record',layer='derived',source_record_sha256=H))
        report=assemble(graph,root,'outgoing',4)
        self.assertEqual(len(report['rows']),128);self.assertEqual(len(report['expanded_ids']),32)
        self.assertGreater(report['limits']['omitted_adjacent_edges'],0)
        self.assertTrue(any(r['stop']=='node_limit' for r in report['rows']))
        self.assertEqual(report['global_worldmap_index'],graph)


if __name__=='__main__':unittest.main()

from copy import deepcopy
import unittest
from unittest.mock import patch
from sdk.project import ProjectError
from sdk.asset_references import assemble_project,source_key
from sdk.asset_reference_trace import assemble_trace,inspect
import test_project_asset_references as fixtures
from test_model_primitive_workflow import http_server

class TraceTests(unittest.TestCase):
 def fixture(self):
  h=fixtures.ProjectAssetReferences();h.setUp();self.addCleanup(h.doCleanups);return h
 def test_source_graph_direction_layers_and_immutability(self):
  h=self.fixture();root=h.p.selected;before=deepcopy(h.p._document());graph=assemble_project(h.p,h.catalogs,root,h.materials,_full_graph=True)
  report=assemble_trace(graph,'outgoing',3,'all');self.assertTrue(any(len(row['edge_ids'])==2 for row in report['rows']));self.assertTrue(all(row['node_ids'][0]==root for row in report['rows']));self.assertEqual(h.p._document(),before)
  reverse=assemble_trace(graph,'incoming',4,'all');self.assertTrue(reverse['rows']);self.assertTrue(all(e['layer']=='imported' for row in assemble_trace(graph,'outgoing',4,'imported')['rows'] for report in [next(r for r in reverse['reports'] if r['asset_id']==root)] for e in report['outgoing'] if e['id'] in row['edge_ids']))
  copied=deepcopy(graph);report['reports'][0]['nodes'][0]['label']='changed';self.assertEqual(graph,copied)
 def test_cycles_unavailable_depth_and_budgets(self):
  h=self.fixture();graph=assemble_project(h.p,h.catalogs,h.p.selected,h.materials,_full_graph=True);root=graph['asset_id'];node=deepcopy(graph['nodes'][0]);node.update(id='asset://cycle',available=True);graph['nodes'].append(node);template=deepcopy(graph['edges'][0]);template.update(id='0'*64,source_id=root,target_id=node['id']);graph['edges'].append(template);back=deepcopy(template);back.update(id='1'*64,source_id=node['id'],target_id=root);graph['edges'].append(back)
  rows=assemble_trace(graph,'outgoing',4,'all')['rows'];self.assertTrue(any(row['stop']=='already_seen' for row in rows));self.assertTrue(any(row['stop']=='depth_limit' for row in assemble_trace(graph,'outgoing',1,'all')['rows']))
  node['available']=False;self.assertTrue(any(row['stop']=='unavailable' for row in assemble_trace(graph,'outgoing',4,'all')['rows']))
  for i in range(150):
   target=deepcopy(node);target.update(id='asset://wide/'+str(i),available=True);graph['nodes'].append(target);edge=deepcopy(template);edge.update(id=f'{i+2:064x}',target_id=target['id']);graph['edges'].append(edge)
  trace=assemble_trace(graph,'outgoing',4,'all');self.assertEqual(len(trace['rows']),128);self.assertLessEqual(len(trace['reports']),32);self.assertGreater(trace['limits']['omitted_adjacent_edges'],0);self.assertTrue(any(row['stop']=='node_limit' for row in trace['rows']))
 def test_stale_controls_and_exact_http(self):
  h=self.fixture();key=source_key(h.p)
  for direction,depth,layer in [('bad',2,'all'),('outgoing',True,'all'),('outgoing',5,'all'),('outgoing',2,'live')]:
   with self.assertRaises(ProjectError),patch('sdk.asset_reference_trace.inspect_project') as discovery:inspect(h.p,h.p.selected,direction,depth,layer,key)
   discovery.assert_not_called()
  with self.assertRaises(ProjectError),patch('sdk.asset_reference_trace.inspect_project') as discovery:inspect(h.p,h.p.selected,'outgoing',2,'all','0'*64)
  discovery.assert_not_called();graph=assemble_project(h.p,h.catalogs,h.p.selected,h.materials,_full_graph=True)
  with patch('sdk.asset_reference_trace.inspect_project',return_value=graph):
   with http_server(h.p) as (server,post):
    body=dict(asset_id=h.p.selected,direction='outgoing',depth=2,layer='all',expected_source_key=key);self.assertEqual(post('/api/asset-reference-trace',body)[0],200)
    for change in ({'extra':0},{'depth':True},{'expected_source_key':'0'*64}):self.assertEqual(post('/api/asset-reference-trace',dict(body,**change))[0],400)

if __name__=='__main__':unittest.main()

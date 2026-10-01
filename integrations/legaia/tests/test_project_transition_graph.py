from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from sdk.resources import project_transition_graph,project_transition_state_key
from sdk.project import ProjectError
from importer.core import ImportError
from integrations.legaia.tests.test_importer_script_catalog import catalog,forbidden_fields

class ProjectTransitions(unittest.TestCase):
    def project(self):
        return SimpleNamespace(root=Path('synthetic'),disc_path='fixture.bin',active_scene='scene://fixture',imports={'scene://fixture':{'scene':{'name':'fixture'}},'scene://town02':{'scene':{'name':'town02'}}},overrides={})
    def load(self,path,name):
        c=catalog(b'\x3f\0\0\x06town02\x01\x82\x03')
        if name!='fixture':
            # Distinct source identities for a second imported scene.
            c['scene']=name
            for row in c['assets']:
                for key in ('semantic_id','actor_semantic_id','owner_semantic_id'):
                    if isinstance(row.get(key),str):row[key]=row[key].replace('fixture',name)
        return c
    def run_graph(self,p,loader=None):
        with patch('sdk.resources._disc_context',return_value=nullcontext()),patch('sdk.resources._verify'),patch('importer.script_catalog.load_script_asset_catalog',side_effect=loader or self.load):
            return project_transition_graph(p)
    def test_merged_sources_self_edges_no_writes_and_detached(self):
        p=self.project();before=deepcopy(p.__dict__);result=self.run_graph(p)
        self.assertEqual(len(result['edges']),2)
        self.assertEqual(len(result['nodes']),2)
        self.assertEqual({n['id']:n['roles'] for n in result['nodes']}['scene://town02'],['destination','source'])
        self.assertTrue(all(e['reachability']=='not_evaluated' for e in result['edges']))
        self.assertFalse(forbidden_fields(result));self.assertEqual(p.__dict__,before)
        self.assertEqual(result['source_key'],project_transition_state_key(p))
        result['edges'][0]['reference'].clear();self.assertEqual(p.__dict__,before)
    def test_unavailable_source_retained_and_stale_rejected(self):
        p=self.project()
        def missing(path,name):
            if name=='town02':raise ImportError('unsupported carrier')
            return self.load(path,name)
        result=self.run_graph(p,missing)
        self.assertEqual(result['scenes'][1]['status'],'unavailable')
        self.assertTrue(next(n for n in result['nodes'] if n['id']=='scene://town02')['imported'])
        def stale(path,name):
            p.overrides['scene://fixture']={'changed':True}
            return self.load(path,name)
        with self.assertRaisesRegex(ProjectError,'changed'):self.run_graph(p,stale)
        p.imports={}
        with self.assertRaises(ProjectError):self.run_graph(p)

if __name__=='__main__':unittest.main()

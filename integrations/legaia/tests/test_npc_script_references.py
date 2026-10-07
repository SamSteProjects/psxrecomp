"""NPC source navigation does not claim generated or runtime script identity."""
from copy import deepcopy
from unittest.mock import patch
import unittest
import test_asset_references as fixtures

from sdk.project import ProjectError
from sdk.asset_references import assemble, assemble_project


class NpcScriptReferences(unittest.TestCase):
    def setUp(self):
        fixtures.AssetReferences.setUp(self)

    def test_donor_navigation_and_source_rejections(self):
        self.catalog['records'] = [dict(id='script://fixture/actors/man-p1/0001',
            semantic_id='script://fixture/actors/man-p1/0001', script_id='script://fixture/actors/man-p1/0001',
            kind='script', asset_kind='script', actor_semantic_id=self.actor, owner_semantic_id=self.actor,
            partition=1, reference_commit='d6e64c68ede25813d35db20980da82a1a025549b', status='partial',
            source_record=dict(partition=1,record_index=1,byte_offset=100,byte_length=50,
                byte_coordinate_space='decoded_lzs_descriptor',record_alias_count=1,sha256='b'*64))]
        owner='authored-actor://fixture';other='authored-actor://second'
        for identifier in (owner,other):
            self.p.actor_drafts[identifier]=dict(scene_id=self.p.active_scene,name=identifier,donor_entity_id=self.actor)
        before=deepcopy((self.p._document(),self.p.undo_stack,self.p.active_scene))
        with patch.object(self.p,'model_references',return_value=[]):
            result=assemble(self.p,self.catalog,owner)
            edge=next(e for e in result['outgoing'] if e['kind']=='draft_script_donor')
            self.assertEqual(edge['layer'],'authored');self.assertEqual(edge['npc_script_donor_evidence']['source_record_sha256'],'b'*64)
            inverse=assemble(self.p,self.catalog,edge['target_id'])
            self.assertEqual({e['source_id'] for e in inverse['incoming'] if e['kind']=='draft_script_donor'},{owner,other})
            project=assemble_project(self.p,{self.p.active_scene:self.catalog},owner)
            self.assertIn('draft_script_donor',{e['kind'] for e in project['outgoing']})
            for mutate in [lambda r:r.update(owner_semantic_id='scene://wrong'),lambda r:r['source_record'].update(sha256='bad'),lambda r:r.update(reference_commit='0'*40)]:
                bad=deepcopy(self.catalog);mutate(bad['records'][0])
                with self.assertRaises(ProjectError):assemble(self.p,bad,owner)
            bad=deepcopy(self.catalog);bad['records'].append(deepcopy(bad['records'][0]))
            with self.assertRaises(ProjectError):assemble(self.p,bad,owner)
            unavailable=deepcopy(self.catalog);unavailable['records'][0]['status']='unavailable'
            missing=assemble(self.p,unavailable,owner)
            self.assertNotIn('draft_script_donor',{e['kind'] for e in missing['outgoing']})
            self.assertEqual(missing['coverage']['unresolved_reference_count'],2)
        self.assertEqual(before,(self.p._document(),self.p.undo_stack,self.p.active_scene))

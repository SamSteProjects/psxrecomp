"""Project routing checks; archive relocation has separate byte-level tests."""
from pathlib import Path
from copy import deepcopy
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from sdk.project import ProjectService, ProjectError
from sdk.draft_build import prepare_draft_archive


class MultiSceneDrafts(unittest.TestCase):
    def setUp(self):
        # Routing fixtures substitute native archive bytes and MAN rebuilds.
        self.enterContext(patch('sdk.draft_build._archive',return_value=SimpleNamespace(header_offset=0)))

    def test_project_export_does_not_require_or_invent_a_draft(self):
        project=ProjectService(Path('.'))
        project.imports={'scene://a':{}}
        with self.assertRaisesRegex(ProjectError,'authored scene edits'):
            prepare_draft_archive(project)
        project.overrides={'scene://a/actors/1':{'Transform':{'position':{'x':704}}}}
        def prepare(view,identity,*,defer_rebuild,scene_id):
            self.assertIsNone(identity)
            self.assertTrue(defer_rebuild)
            self.assertEqual(scene_id,'scene://a')
            self.assertFalse(view.actor_drafts)
            return b'archive',{'_rebuild_request':{'entry_index':0},'source_disc_sha256':'same'}
        with patch('sdk.draft_build._prepare_draft_scene',side_effect=prepare), \
             patch('sdk.draft_build.rebuild_man_entries',return_value=(b'new',{})):
            result,audit=prepare_draft_archive(project)
        self.assertEqual(result,b'new')
        self.assertIsNone(audit['selected_draft_id'])
        self.assertEqual(audit['drafts'],{})

    def test_edit_only_scene_is_included_and_concurrent_change_rejects(self):
        project=ProjectService(Path('.'))
        project.imports={'scene://a':{},'scene://b':{}}
        project.actor_drafts={'a':{'scene_id':'scene://a'}}
        project.overrides={'scene://b/actors/1':{'Transform':{'position':{'x':704}}}}
        seen=[]
        def prepare(view,identity,*,defer_rebuild,scene_id):
            seen.append((scene_id,identity,deepcopy(view.overrides)))
            if scene_id=='scene://b':
                self.assertIsNone(identity)
                self.assertFalse(view.actor_drafts)
                self.assertEqual(view.overrides,project.overrides)
            return b'archive',{'_rebuild_request':{'entry_index':len(seen)},'source_disc_sha256':'same'}
        with patch('sdk.draft_build._prepare_draft_scene',side_effect=prepare), \
             patch('sdk.draft_build.rebuild_man_entries',return_value=(b'new',{})):
            _,audit=prepare_draft_archive(project,'a')
            self.assertEqual(set(audit['scenes']),{'scene://a','scene://b'})
            self.assertEqual([item[:2] for item in seen],[('scene://a','a'),('scene://b',None)])
        def mutate(*args,**kwargs):
            project.overrides['scene://b/actors/1']['Transform']['position']['x']=768
            return b'new',{}
        with patch('sdk.draft_build._prepare_draft_scene',side_effect=prepare), \
             patch('sdk.draft_build.rebuild_man_entries',side_effect=mutate):
            with self.assertRaisesRegex(ProjectError,'inputs changed'):
                prepare_draft_archive(project,'a')

    def test_routes_each_scene_and_rejects_unassigned_edits(self):
        project=ProjectService(Path('.'))
        project.imports={'scene://a':{},'scene://b':{}}
        project.actor_drafts={'a':{'scene_id':'scene://a'},'b':{'scene_id':'scene://b'}}
        project.overrides={'scene://a/actors/1':{'Transform':{}},'scene://b/scripts/2':{'Dialogue':{}}}
        original=deepcopy(project.overrides)
        seen=[]
        def prepare(view,identity,*,defer_rebuild,scene_id):
            scene=view.actor_drafts[identity]['scene_id']
            self.assertTrue(defer_rebuild)
            self.assertTrue(all(key.startswith(scene+'/') for key in view.overrides))
            self.assertEqual(len(view.actor_drafts),1)
            seen.append(scene)
            return b'archive',{'_rebuild_request':{'entry_index':len(seen)},
                               'source_disc_sha256':'same','result_prot_sha256':'old','container':None}
        with patch('sdk.draft_build._prepare_draft_scene',side_effect=prepare), \
             patch('sdk.draft_build.rebuild_man_entries',return_value=(b'new',{})) as rebuild:
            result,audit=prepare_draft_archive(project,'b')
            self.assertEqual(seen,['scene://a','scene://b'])
            self.assertEqual(result,b'new')
            self.assertEqual(project.overrides,original)
            self.assertTrue(all(value['stage']=='prepared_scene_man' and 'result_prot_sha256' not in value
                                for value in audit['scenes'].values()))
            project.overrides['scene://unrelated/actor']={}
            with self.assertRaisesRegex(ProjectError,'outside'):
                prepare_draft_archive(project,'a')
            self.assertEqual(rebuild.call_count,1)


if __name__=='__main__':
    unittest.main()

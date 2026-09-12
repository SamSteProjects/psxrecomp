"""Project-wide authored discovery stays independent of the active scene/cache."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from integrations.legaia.tests.test_project_workflow import synthetic_scene
from sdk.project import ProjectService


class AuthoredAssetCatalog(unittest.TestCase):
    def test_draft_usage_keeps_retail_donor_when_original_appearance_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory))
            scene=synthetic_scene()
            donor=scene['actors'][0]
            other=deepcopy(donor)
            other['semantic_id']='scene://fixture/actors/man-p1/0002'
            other['model_reference']['asset_semantic_id']='asset://fixture/model/1'
            scene['actors'].append(other)
            scene['assets']['models'].append({'semantic_id':'asset://fixture/model/1','source_record':{'fixture':True}})
            project.import_metadata(scene)
            project.command({'type':'create_actor_draft','donor_entity_id':donor['semantic_id'],
                             'position':{'x':128,'z':256},'name':'New resident'})
            identifier=next(iter(project.actor_drafts))
            record=next(row for row in project.authored_assets() if row['id']==identifier)
            self.assertTrue(record['draft'])
            self.assertEqual(record['donor_entity_id'],donor['semantic_id'])
            self.assertEqual(record['name'],'New resident')
            record['authored']['position']['x']=999
            self.assertEqual(project.actor_drafts[identifier]['position']['x'],128)
            with patch.object(project,'appearance_source_actor',return_value=other):
                references=project.model_references()
            draft=next(row for row in references if row['source_id']==identifier)
            self.assertEqual(draft['target_id'],donor['model_reference']['asset_semantic_id'])
            self.assertEqual(draft['effective_donor_id'],donor['semantic_id'])
            self.assertFalse(draft['imported'])
            self.assertTrue(draft['effective'])
            self.assertEqual(draft['runtime_binding'],'not_asserted')
            project.undo()
            self.assertFalse(any(row['id']==identifier for row in project.authored_assets()))
            self.assertFalse(any(row['source_id']==identifier for row in project.model_references()))
            project.redo()
            restored=ProjectService.open(project.save())
            self.assertEqual(restored.model_references(),project.model_references())
            self.assertEqual(restored.authored_assets(),project.authored_assets())

    def test_animation_only_edits_are_searchable_and_isolated(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            scene = synthetic_scene()
            project.import_metadata(scene)
            actor = scene['actors'][0]['semantic_id']
            # Catalog projection consumes validated authored state; encoding is
            # covered by the animation authoring tests.
            project.overrides[actor] = {'AnimationChannels': {'edits': [
                {'frame_index': 3, 'object_index': 1, 'translation': {'x': 100}}]}}
            record = next(row for row in project.authored_assets() if row['id'] == actor)
            self.assertEqual(record['changes'], ['Animation: 1 edited channel'])
            record['authored']['AnimationChannels']['edits'].clear()
            self.assertEqual(len(project.overrides[actor]['AnimationChannels']['edits']), 1)

    def test_cross_scene_history_persistence_and_snapshot_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            first = synthetic_scene()
            second = json.loads(json.dumps(first).replace('fixture', 'second'))
            project.import_metadata(first)
            actor = first['actors'][0]['semantic_id']
            project.command({'type': 'set_transform', 'entity_id': actor, 'position': {'x': 128}})
            project.command({'type': 'create_actor_template', 'entity_id': actor, 'name': 'Courtyard'})
            with patch.object(project, '_texture_context', return_value=Mock()):
                project.set_texture_replacement('texture://fixture/1/raw/0', b'private fixture')
            project.import_metadata(second)
            before = deepcopy(project._document())
            records = project.state()['authored_assets']
            self.assertEqual({row['kind'] for row in records}, {'actor', 'texture', 'template'})
            self.assertTrue(all(row['scene_id'] == 'scene://fixture' for row in records))
            self.assertEqual(len({row['id'] for row in records}), 3)
            self.assertFalse(project.assets.resource_catalogs)
            records[0]['authored'].clear()
            self.assertEqual(project._document(), before)
            restored = ProjectService.open(project.save())
            self.assertEqual(restored.authored_assets(), project.authored_assets())
            restored.command({'type': 'clear_texture_replacement', 'asset_id': 'texture://fixture/1/raw/0'})
            self.assertEqual(len(restored.authored_assets()), 2)
            restored.undo()
            self.assertEqual(restored.authored_assets(), project.authored_assets())


if __name__ == '__main__':
    unittest.main()

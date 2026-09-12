"""Candidate inspection must not silently apply unrelated authored components."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.server import EditorServer
from sdk.project import ProjectError


class ActorCandidateServiceTests(unittest.TestCase):
    def test_position_only_forwarding_and_no_project_mutation(self):
        project = SimpleNamespace(
            disc_path='verified-source.bin', active_scene='scene-id',
            imports={'scene-id': {'scene': {'name':'town01'}, 'actors':[
                {'semantic_id':'actor-id','source_record':{'record_index':11}}]}},
            overrides={'actor-id': {'Transform': {'position':{'x':3008,'y':128}},
                                    'ActorAppearance': {'donor_entity_id':'other'}}},
            undo_stack=[{'sentinel':True}])
        service = SimpleNamespace(project=project)
        before = deepcopy(project.__dict__)
        with patch('importer.actor_candidate_inspection.inspect_actor_candidate',return_value={}) as inspect:
            report = EditorServer.actor_candidate_inspection(service,'actor-id')
            inspect.assert_called_once_with('verified-source.bin','town01',11,position={'x':3008})
        self.assertEqual(report['included_overrides'],{'Transform':{'position':{'x':3008}}})
        self.assertEqual(report['excluded_transform_axes'],['y'])
        self.assertEqual(report['excluded_override_components'],['ActorAppearance'])
        self.assertEqual(project.__dict__,before)
        project.overrides={}
        with patch('importer.actor_candidate_inspection.inspect_actor_candidate',return_value={}) as inspect:
            report=EditorServer.actor_candidate_inspection(service,'actor-id')
            inspect.assert_called_once_with('verified-source.bin','town01',11,position=None)
        self.assertFalse(report['includes_project_overrides'])
        with self.assertRaises(ProjectError):
            EditorServer.actor_candidate_inspection(service,'missing')


if __name__ == '__main__':
    unittest.main()

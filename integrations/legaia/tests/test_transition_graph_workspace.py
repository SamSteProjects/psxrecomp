"""Explorer integration gaps: project freshness, registration and parallel refs."""
from contextlib import ExitStack, nullcontext
from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from importer.core import ImportError
from importer.dialogue_authoring import DialogueAuthoringContext
from importer.script_catalog import _catalog
from importer.transition_authoring import TransitionAuthoringContext
from sdk.project import ProjectError, ProjectService
from sdk.resources import (project_transition_graph, project_transition_state_key,
                           scene_transition_graph, scene_transition_state_key)
from integrations.legaia.tests.test_importer_dialogue_authoring import fixture, literals
from integrations.legaia.tests.test_importer_script_catalog import forbidden_fields
from integrations.legaia.tests.test_project_workflow import synthetic_scene
from integrations.legaia.tests.test_transition_assets import warp


def parallel_source():
    """Two genuinely decoded source owners referencing the same destination."""
    _, original = fixture(warp())
    region = 0x2B + 12
    section = int.from_bytes(original[0x28:0x2B], 'little')
    p2 = bytes(4) + warp(entry=(128, 127, 231), extended=7)
    man = bytearray(original[:region + section] + p2 + original[region + section:])
    man[0x34:0x37] = section.to_bytes(3, 'little')
    man[0x28:0x2B] = (section + len(p2)).to_bytes(3, 'little')
    man = bytes(man)
    context = TransitionAuthoringContext(DialogueAuthoringContext(
        'fixture', man, literals(man), {'synthetic': True}))
    return context, _catalog(man, 'fixture', {'synthetic': True}, {'town02'})


def discovery(loader, context=None):
    stack = ExitStack()
    stack.enter_context(patch('sdk.resources._disc_context', return_value=nullcontext()))
    stack.enter_context(patch('sdk.resources._verify'))
    stack.enter_context(patch('sdk.resources.source_key', return_value='a' * 64))
    stack.enter_context(patch('importer.script_catalog.load_script_asset_catalog', side_effect=loader))
    if context is not None:
        stack.enter_context(patch('importer.transition_authoring.load_transition_authoring_context',
                                  return_value=context))
    return stack


class TransitionGraphWorkspaceTests(unittest.TestCase):
    def test_authored_entry_changes_project_key_and_scene_annotation_key_without_source_replacement(self):
        context, source = parallel_source()
        source_before = deepcopy(source)
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.import_metadata(synthetic_scene())
            project.disc_path = 'synthetic'
            with discovery(lambda path, name: deepcopy(source), context):
                initial = project_transition_graph(project)
                initial_scene = scene_transition_graph(project)
                edge = next(row for row in initial['edges'] if row['partition'] == 1)
                transition_id = edge['entry_layers']['transition_id']
                values = {'entry_x_encoded': 128, 'direction_encoded': 231}
                with patch.object(project, '_transition_context', return_value=context):
                    project.command(dict(type='set_transition_entry', entity_id=edge['owner_id'],
                                         transition_id=transition_id, values=values))
                authored = project_transition_graph(project)
                authored_scene = scene_transition_graph(project)
                self.assertNotEqual(authored['source_key'], initial['source_key'])
                self.assertEqual(authored['source_key'], project_transition_state_key(project))
                self.assertEqual(authored_scene['source_key'], initial_scene['source_key'])
                self.assertNotEqual(authored_scene['transition_state_key'], initial_scene['transition_state_key'])
                self.assertEqual(authored_scene['transition_state_key'], scene_transition_state_key(project))
                before_edges = {row['id']: row for row in initial['edges']}
                after_edges = {row['id']: row for row in authored['edges']}
                self.assertEqual(set(before_edges), set(after_edges))
                for identifier, before in before_edges.items():
                    after = after_edges[identifier]
                    self.assertEqual(after['reference'], before['reference'])
                    self.assertEqual(after['source_record'], before['source_record'])
                    self.assertEqual(after['entry_layers']['imported'], before['entry_layers']['imported'])
                    self.assertEqual(after['reachability'], 'not_evaluated')
                changed = after_edges[edge['id']]
                self.assertEqual(changed['entry_layers']['authored'], values)
                self.assertEqual(changed['entry_layers']['effective'],
                                 dict(entry_x_encoded=128, entry_z_encoded=130, direction_encoded=231))
                self.assertEqual(changed['entry_layers']['validation'], 'reverified_on_build')
                other = next(row for row in authored['edges'] if row['partition'] == 2)
                self.assertEqual(other, before_edges[other['id']])
                authored['edges'][0]['entry_layers']['authored'].clear()
                self.assertEqual(project.overrides[edge['owner_id']]['Transitions']['entries'][transition_id], values)
                project.command(dict(type='clear_transition_entry', entity_id=edge['owner_id'],
                                     transition_id=transition_id))
                cleared = project_transition_graph(project)
                self.assertEqual(cleared['source_key'], initial['source_key'])
                self.assertEqual(cleared['edges'], initial['edges'])
                self.assertFalse(forbidden_fields(cleared))
        self.assertEqual(source, source_before)

    def test_registering_destination_changes_navigation_identity_without_losing_unavailable_source(self):
        _, source = parallel_source()
        project = SimpleNamespace(root=Path('synthetic'), disc_path='fixture.bin',
                                  active_scene='scene://fixture', overrides={},
                                  imports={'scene://fixture': {'scene': {'name': 'fixture'}}})
        def unavailable_destination(path, name):
            if name == 'town02':
                raise ImportError('unsupported destination script carrier')
            return deepcopy(source)
        with discovery(unavailable_destination):
            before = project_transition_graph(project)
            destination = next(row for row in before['nodes'] if row['id'] == 'scene://town02')
            self.assertFalse(destination['imported'])
            project.imports['scene://town02'] = {'scene': {'name': 'town02'}}
            registered = project_transition_graph(project)
            self.assertNotEqual(registered['source_key'], before['source_key'])
            self.assertEqual(registered['scene_ids'], ['scene://fixture', 'scene://town02'])
            destination = next(row for row in registered['nodes'] if row['id'] == 'scene://town02')
            self.assertTrue(destination['imported'])
            self.assertEqual(destination['roles'], ['destination'])
            self.assertEqual(registered['scenes'][1], dict(scene_id='scene://town02', scene_name='town02',
                status='unavailable', reason='unsupported destination script carrier'))
            self.assertEqual(registered['edges'], before['edges'])
            self.assertEqual(registered['coverage'], before['coverage'])
            self.assertTrue(all(row['reachability'] == 'not_evaluated' for row in registered['edges']))

    def test_parallel_edges_keep_owner_pc_identity_independent_of_catalog_and_import_order(self):
        _, source = parallel_source()
        project = SimpleNamespace(root=Path('synthetic'), disc_path='fixture.bin',
                                  active_scene='scene://fixture', overrides={}, imports={
                                      'scene://town02': {'scene': {'name': 'town02'}},
                                      'scene://fixture': {'scene': {'name': 'fixture'}}})
        _, unavailable_man = fixture(b'\x2a')
        destination = _catalog(unavailable_man, 'town02', {'synthetic': True}, {'town02'})
        def load(path, name):
            return deepcopy(source if name == 'fixture' else destination)
        with discovery(load):
            first = project_transition_graph(project)
        self.assertEqual(len(first['edges']), 2)
        self.assertEqual({(row['source'], row['target']) for row in first['edges']},
                         {('scene://fixture', 'scene://town02')})
        by_id = {row['id']: row for row in first['edges']}
        self.assertEqual(set(by_id), {'transition://fixture/actors/man-p1/0001/0005',
                                     'transition://fixture/scripts/man-p2/0000/0004'})
        self.assertEqual({row['partition'] for row in first['edges']}, {1, 2})
        for edge in first['edges']:
            self.assertEqual(edge['entry_layers']['transition_id'],
                             edge['script_id'] + f"/transition/{edge['reference']['pc']:04x}")
            self.assertEqual(edge['reference']['byte_offset'],
                             edge['source_record']['byte_offset'] + edge['reference']['pc'])
        source['assets'].reverse()
        project.imports = dict(reversed(list(project.imports.items())))
        with discovery(load):
            second = project_transition_graph(project)
        self.assertEqual(second['source_key'], first['source_key'])
        self.assertEqual(second['nodes'], first['nodes'])
        self.assertEqual(second['scenes'], first['scenes'])
        self.assertEqual({row['id']: row for row in second['edges']}, by_id)
        # Duplicate source identity is corruption; parallel references must not be deduplicated by endpoints.
        duplicate = deepcopy(source)
        duplicate['assets'].append(deepcopy(next(row for row in source['assets']
                                                if row['asset_kind'] == 'script' and row['transitions'])))
        with discovery(lambda path, name: duplicate if name == 'fixture' else destination):
            with self.assertRaisesRegex(ProjectError, 'ambiguous'):
                project_transition_graph(project)


if __name__ == '__main__':
    unittest.main()

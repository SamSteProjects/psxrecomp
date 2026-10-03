"""Retail growth preparation must reject known native overflow before packing."""
from copy import deepcopy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from importer.core import ImportError
from importer.man_layout import read_man_layout
from importer.man_source import read_man_source
from importer.pipeline import _disc_context, _bounded_scene_range, import_scene
from sdk.draft_build import prepare_draft_archive
from sdk.project import ProjectService


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class GrowthActorCapacityTests(unittest.TestCase):
    def test_compressed_and_streaming_overflow_before_archive_repack_without_mutation(self):
        disc = os.environ['LEGAIA_DISC_BIN']
        for scene in ('town01', 'dolk2'):
            with self.subTest(scene=scene), tempfile.TemporaryDirectory() as directory:
                project = ProjectService(Path(directory))
                document = import_scene(disc, scene)
                project.import_metadata(document, disc)
                with _disc_context(disc) as (_, _, mapping, archive):
                    start, end = _bounded_scene_range(archive, mapping, scene)
                    source = read_man_source(archive, start, end, scene).payload
                count = read_man_layout(source)['partition_counts'][1]
                donor = next(actor for actor in document['actors']
                             if actor['source_record']['record_index'] == 1)
                for index in range(144 - count):
                    project.command(dict(type='create_actor_draft', donor_entity_id=donor['semantic_id'],
                                         position={'x': 64, 'z': 64}, name=f'Capacity probe {index}'))
                project.save()
                before = deepcopy((project._document(), project.imports,
                                   project.undo_stack, project.redo_stack, project.selected))
                files = {str(p.relative_to(project.root)): p.read_bytes()
                         for p in project.root.rglob('*') if p.is_file()}
                selected = next(iter(project.actor_drafts)) if scene == 'town01' else None
                with patch('sdk.draft_build.rebuild_man_entry') as one, \
                        patch('sdk.draft_build.rebuild_man_entries') as many:
                    with self.assertRaisesRegex(ImportError, 'at least 144 nodes'):
                        prepare_draft_archive(project, selected)
                one.assert_not_called()
                many.assert_not_called()
                self.assertEqual((project._document(), project.imports,
                                  project.undo_stack, project.redo_stack, project.selected), before)
                self.assertEqual({str(p.relative_to(project.root)): p.read_bytes()
                                  for p in project.root.rglob('*') if p.is_file()}, files)

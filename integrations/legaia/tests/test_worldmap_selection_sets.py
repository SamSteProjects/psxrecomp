from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.build import authored_state_key
from sdk.worldmap_selection_sets import review, review_key
from test_project_workflow import synthetic_scene
import test_worldmap_asset_index as fixtures


class WorldSelectionTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.p=ProjectService(Path(self.directory.name));self.p.import_metadata(synthetic_scene())
        self.fixture=fixtures.WorldmapAssetIndexTests();self.fixture.setUp()
        self.source=patch('sdk.worldmap_selection_sets.context',side_effect=self.fixture.context);self.source.start();self.addCleanup(self.source.stop)
        self.key=patch('sdk.worldmap_selection_sets.state_key',return_value=fixtures.H);self.key.start();self.addCleanup(self.key.stop)

    def create(self,name='Working group'):
        self.p.command(dict(type='create_worldmap_selection_set',scene='map01',source_key=fixtures.H,record_ids=['0001'],name=name))
        return next(iter(self.p.worldmap_selection_sets.values()))

    def test_metadata_persistence_history_and_native_identity(self):
        before=deepcopy((self.p.imports,self.p.overrides));native=authored_state_key(self.p);row=self.create()
        self.assertEqual(authored_state_key(self.p),native);self.assertEqual((self.p.imports,self.p.overrides),before)
        self.assertIn('Saved world selections',self.p.unsaved_sections)
        self.p.undo();self.assertFalse(self.p.worldmap_selection_sets);self.p.redo()
        self.assertEqual(review(self.p,row['id'],review_key(self.p,row),fixtures.H)['selection'],row)
        reopened=ProjectService.open(self.p.save());self.assertEqual(reopened.worldmap_selection_sets,self.p.worldmap_selection_sets)
        self.assertEqual(authored_state_key(reopened),native)
        self.p.command(dict(type='rename_worldmap_selection_set',selection_set_id=row['id'],review_key=review_key(self.p,row),name='Renamed'))
        latest=self.p.worldmap_selection_sets[row['id']];self.assertEqual(latest['name'],'Renamed')
        self.p.command(dict(type='delete_worldmap_selection_set',selection_set_id=row['id'],review_key=review_key(self.p,latest)))
        self.assertFalse(self.p.worldmap_selection_sets);self.p.undo();self.assertEqual(self.p.worldmap_selection_sets[row['id']],latest)

    def test_stale_duplicate_and_partial_sources_refuse(self):
        row=self.create();held=deepcopy(self.p._document())
        with self.assertRaises(ProjectError):self.create('working GROUP')
        with self.assertRaises(ProjectError):review(self.p,row['id'],'0'*64,fixtures.H)
        with self.assertRaises(ProjectError):self.p.command(dict(type='create_worldmap_selection_set',scene='map01',source_key='0'*64,record_ids=['0001'],name='Stale'))
        def partial(view,scene):
            result=list(self.fixture.context(view,scene));result[2]['0001']['writable']=False;return tuple(result)
        with patch('sdk.worldmap_selection_sets.context',side_effect=partial):
            with self.assertRaises(ProjectError):review(self.p,row['id'],review_key(self.p,row),fixtures.H)
        self.assertEqual(self.p._document(),held)

    def test_current_transform_changes_do_not_rebind_saved_members(self):
        row=self.create()
        def moved(view,scene):
            result=list(self.fixture.context(view,scene));result[2]['0001']['current_values']=dict(offset=dict(x=42,y=23,z=12),yaw_units=512);return tuple(result)
        with patch('sdk.worldmap_selection_sets.context',side_effect=moved):self.assertEqual(review(self.p,row['id'],review_key(self.p,row),fixtures.H)['selection'],row)
        def changed(view,scene):
            result=list(self.fixture.context(view,scene));result[2]['0001']['source_record_sha256']='b'*64;return tuple(result)
        with patch('sdk.worldmap_selection_sets.context',side_effect=changed):
            with self.assertRaises(ProjectError):review(self.p,row['id'],review_key(self.p,row),fixtures.H)


if __name__=='__main__':unittest.main()

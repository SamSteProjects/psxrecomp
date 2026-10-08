"""Browsing another Retail scene preserves all saved and unsaved Project inputs."""
from copy import deepcopy
from pathlib import Path
import os,tempfile,unittest
from sdk.project import ProjectService,ProjectError
from sdk.project_copy import source_key
from sdk.server import EditorServer
from sdk.catalog_scene_preview import preview
from importer.pipeline import import_scene

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class CatalogScenePreview(unittest.TestCase):
    def test_isolated_retail_scene_and_freshness(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));disc=os.environ['LEGAIA_DISC_BIN'];p.import_metadata(import_scene(disc,'taiku2'),disc)
            p.command(dict(type='create_actor_draft',donor_entity_id='scene://taiku2/actors/man-p1/0002',name='Keep current draft',position=dict(x=128,z=256)))
            p.save();before=deepcopy((p._document(),p.undo_stack,p.redo_stack,p.imports,p.assets.records))
            server=EditorServer(('127.0.0.1',0),p,runtime_port=65533)
            def loader(view,asset,*args,**kwargs):return server.model_preview(asset,*args,project_view=view,**kwargs)
            try:
                with self.assertRaises(ProjectError):preview(p,disc,'taiku','0'*64,loader)
                result=preview(p,disc,'taiku',source_key(p),loader)
                self.assertEqual(result['scene_id'],'scene://taiku');self.assertFalse(result['project_imported'])
                graph=result['preview'];self.assertEqual(graph['metrics']['draft_count'],0)
                self.assertEqual(graph['metrics']['total_entity_count'],290)
                self.assertEqual(graph['metrics']['total_renderable_count'],290)
                self.assertIsNone(graph['environment_authoring'])
                self.assertFalse(any(e['entity_id'].startswith('authored-actor://') for e in graph['entities']))
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack,p.imports,p.assets.records),before)
                self.assertEqual(ProjectService.open(p.root)._document(),before[0])
                p.mode='live'
                with self.assertRaises(ProjectError):preview(p,disc,'taiku',source_key(p),loader)
            finally:server.server_close()

if __name__=='__main__':unittest.main()

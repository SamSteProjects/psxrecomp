"""Active-scene model membership and shared provenance never depend on import order."""
from copy import deepcopy
from pathlib import Path
import tempfile,unittest
from sdk.project import ProjectService
from test_project_workflow import synthetic_scene

class ActiveSceneAssets(unittest.TestCase):
    def test_shared_variant_and_unrelated_models_follow_active_import(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));shared='asset://legaia/shared-model/0000'
            for name in ['fixture','other']:
                document=synthetic_scene();scene='scene://'+name
                document['scene']=dict(semantic_id=scene,name=name)
                document['actors'][0]['semantic_id']=scene+'/actors/man-p1/0001'
                document['actors'][0]['model_reference']['asset_semantic_id']=shared
                model=document['assets']['models'][0];model['semantic_id']=shared;model['source_record']['scene_binding']=name
                own=deepcopy(model);own['semantic_id']='asset://'+name+'/models/0001'
                document['assets']['models'].append(own);p.import_metadata(document)
            before=deepcopy((p.imports,p.assets.records,p.undo_stack,p.redo_stack));p.save()
            for scene in ['scene://fixture','scene://other','scene://fixture']:
                p.active_scene=scene;state=p.state();name=scene[8:]
                self.assertEqual({a['id'] for a in state['active_scene_assets']},{shared,'asset://'+name+'/models/0001'})
                self.assertTrue(all(a['scene_id']==scene for a in state['active_scene_assets']))
                variant=next(a for a in state['active_scene_assets'] if a['id']==shared)
                self.assertEqual(variant['source_record']['scene_binding'],name)
                self.assertEqual(len(state['assets']),3)
                variant['source_record']['scene_binding']='mutated'
                self.assertEqual((p.imports,p.assets.records,p.undo_stack,p.redo_stack),before)
            p.save();reopened=ProjectService.open(p.root)
            self.assertEqual(reopened.state()['active_scene_assets'],p.state()['active_scene_assets'])
            self.assertEqual(reopened.assets.records,p.assets.records)

if __name__=='__main__':unittest.main()

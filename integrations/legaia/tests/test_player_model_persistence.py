import os,tempfile,base64,unittest
from pathlib import Path
from copy import deepcopy
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.player_battle import resources
from sdk.player_model_authoring import export,review,apply,current
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc is private')
class PlayerModelPersistenceTests(unittest.TestCase):
    def test_apply_chain_history_save_open_and_input_tamper(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();retail_doc=deepcopy(p._document());catalog=resources(p,str(p.root),source_key(p))['catalog'];asset=catalog['models'][0]['semantic_id']
            def ctx():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,catalog_source_key=catalog['source_key'],equipped=[0]*5)
            first=None
            for delta in (10,1):
                c=ctx();e=export(p,**c);doc,binary=_read_glb(base64.b64decode(e['glb_base64']));doc['nodes'][0]['translation']=[delta,0,0];payload=base64.b64encode(_write_glb(doc,binary)).decode();r=review(p,**c,binding=e['binding'],glb_base64=payload)
                held=deepcopy((p._document(),p.undo_stack))
                with self.assertRaises(ProjectError):apply(p,**c,binding=e['binding'],glb_base64=payload,review_key='0'*64)
                self.assertEqual((p._document(),p.undo_stack),held);apply(p,**c,binding=e['binding'],glb_base64=payload,review_key=r['review_key']);self.assertTrue(p.dirty)
                if first is None:first=deepcopy(p.player_model_overrides)
            self.assertEqual(len(p.undo_stack),2);after=deepcopy(p.player_model_overrides);current(p,**ctx());p.undo();self.assertEqual(p.player_model_overrides,first);p.undo();self.assertEqual(p._document(),retail_doc);p.redo();p.redo();self.assertEqual(p.player_model_overrides,after)
            from sdk.build import build_project,BuildError
            with self.assertRaisesRegex(BuildError,'verified imported scene'):build_project(p)
            p.save();opened=ProjectService.open(p.root);self.assertEqual(opened.player_model_overrides,after);self.assertFalse(opened.dirty)
            c=dict(expected_project_path=str(opened.root),expected_source_key=source_key(opened),asset_id=asset,catalog_source_key=catalog['source_key'],equipped=[0]*5);value=current(opened,**c);self.assertEqual(value['effective_file_sha256'],after[asset]['current_sha256'])
            source=after[asset]['inputs'][0];path=opened.root/'Authored'/'PLAYER'/'Inputs'/(source['sha256']+'.glb');raw=path.read_bytes();path.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
            with self.assertRaises(ProjectError):current(opened,**c)

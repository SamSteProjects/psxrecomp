import base64,json,os,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from importer.me_archive import entries
from importer.player_battle import decode_part
from importer.player_art_authoring import owner
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.player_battle import resources as models
from sdk.player_model_authoring import current
from sdk.player_art_store import context,validate
from sdk.player_art_authoring import inspect
from test_model_primitive_workflow import http_server
from test_importer_export import parse_glb
from test_animation_clip_export import values

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Private retail disc required')
class PlayerArtCurrentExportTests(unittest.TestCase):
    def test_fresh_current_motion_exports_and_stale_guards(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();mr=models(p,str(p.root),source_key(p));raw,ar,_=context(p);stream=ar['streams'][0];source=stream['source_record'];slot=raw[source['slot_offset']:source['slot_offset']+0x10800];row=entries(slot)[stream['stream_index']];channels=decode_part(row['decoded'][2:11]);channels['translation'][0]^=1
            binding=owner(slot,ar,stream['archive_asset_id'],stream['semantic_id'],[dict(frame_index=0,part_index=0,**channels)]);p.player_art_overrides=validate(p,{stream['semantic_id']:binding});p.save();p=ProjectService.open(p.root)
            key=source_key(p);mr=models(p,str(p.root),key);model=mr['catalog']['models'][0];ctx=dict(expected_project_path=str(p.root),expected_source_key=key,asset_id=model['semantic_id'],catalog_source_key=mr['catalog']['source_key'],equipped=[0]*5);current_hash=current(p,**ctx)['effective_file_sha256'];held=deepcopy((p._document(),p.undo_stack,p.redo_stack));cases=[]
            from sdk.player_art_animation import resources
            art_report=resources(p,str(p.root),key)
            with http_server(p) as (_,post):
                for layer in ('retail','current'):
                    args=dict(ctx,art_source_key=ar['source_key'],stream_id=stream['semantic_id'],art_record_id=None,layer=layer,expected_current_sha256=current_hash if layer=='current' else None,frame_index=0,part_index=0);inspection=inspect(p,**args)
                    for mode in ('pose','clip'):
                        export_args=dict(args,expected_current_slot_sha256=inspection['current_slot_sha256'],mode=mode,pose_frame_index=0 if mode=='pose' else None,fps=None if mode=='pose' else 23.5);status,result=post('/api/player-art-current-export',export_args);self.assertEqual(status,200,result);doc,binary=parse_glb(base64.b64decode(result['glb_base64']));self.assertEqual(doc['extras']['source_record']['motion']['owners'],{stream['semantic_id']:binding});self.assertIn('current-motion',result['filename'])
                        if mode=='clip':
                            animation=doc['animations'][0];channel=next(c for c in animation['channels'] if c['target']['path']=='translation' and inspection['base_playback']['base_inspection']['assembly']['animation_part_indices'][c['target']['node']]==0);track=values(doc,binary,animation['samplers'][channel['sampler']]['output']);self.assertEqual(track[0],(channels['translation'][0],-channels['translation'][1],channels['translation'][2]))
                        cases.append(dict(inspection=inspection,export=result,art_report=art_report,model_report=mr,model=model,selection=dict(stream_id=stream['semantic_id'],art_record_id=None,layer=layer,expected_current_sha256=args['expected_current_sha256'],equipped=[0]*5,mode=mode,frame_index=export_args['pose_frame_index'],fps=export_args['fps'])))
                    for change in [dict(expected_current_slot_sha256='stale'),dict(pose_frame_index=0),dict(fps=True),dict(extra=True)]:self.assertEqual(post('/api/player-art-current-export',{**export_args,**change})[0],400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            target=os.getenv('PLAYER_ART_CURRENT_EXPORT_CASES')
            if target:Path(target).write_text(json.dumps(dict(cases=cases)),encoding='utf-8')

if __name__=='__main__':unittest.main()

import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from importer.me_archive import entries
from importer.player_battle import decode_part
from importer.player_art_authoring import owner,compose
from sdk.project import ProjectService
from sdk.project_assets import source_key
from sdk.player_art_store import context,validate
from sdk.player_art_glb import prepare_input,retain_inputs
from sdk.player_art_authoring import inspect,review,proposed_pose
from sdk.player_art_animation import resources
from sdk.player_battle import resources as models


@unittest.skipUnless(os.getenv('PLAYER_ART_CURRENT_EXPORT_CASES') and os.getenv('LEGAIA_DISC_BIN'),'Private source fixtures required')
class ImportedOwnerFixtures(unittest.TestCase):
    def test_independent_import_baselines_and_later_numeric_review(self):
        source=json.loads(Path(os.environ['PLAYER_ART_CURRENT_EXPORT_CASES']).read_text(encoding='utf-8'))['cases']
        clip=next(c for c in source if c['selection']['mode']=='clip' and c['selection']['layer']=='retail')
        stream=clip['inspection']['base_playback']['stream'];content=base64.b64decode(clip['export']['glb_base64']);cases=[]
        for edited_baseline in (False,True):
            with tempfile.TemporaryDirectory() as root:
                p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();raw,catalog,_=context(p)
                at=stream['source_record']['slot_offset'];original=raw[at:at+0x10800];baseline={}
                if edited_baseline:
                    neighbor=next(s for s in catalog['streams'] if s['archive_asset_id']==stream['archive_asset_id'] and s['semantic_id']!=stream['semantic_id'])
                    for chosen,change in [(stream,2),(neighbor,1)]:
                        channels=decode_part(entries(original)[chosen['stream_index']]['decoded'][2:11]);channels['translation'][0]^=change
                        baseline[chosen['semantic_id']]=owner(original,catalog,chosen['archive_asset_id'],chosen['semantic_id'],[dict(frame_index=0,part_index=0,**channels)])
                current=compose(original,catalog,stream['archive_asset_id'],baseline)
                candidate,analysis,evidence=prepare_input(p,original,catalog,stream['archive_asset_id'],stream['semantic_id'],current,baseline,content,equipped=[0]*5,fps=23.5)
                retail=entries(original)[stream['stream_index']]['decoded'];decoded=entries(candidate)[stream['stream_index']]['decoded'];rows=[]
                for frame in range(stream['frame_count']):
                    for part in range(stream['part_count']):
                        offset=2+(frame*stream['part_count']+part)*9
                        if decoded[offset:offset+9]!=retail[offset:offset+9]:rows.append(dict(frame_index=frame,part_index=part,**decode_part(decoded[offset:offset+9])))
                binding=owner(original,catalog,stream['archive_asset_id'],stream['semantic_id'],rows);binding['glb_import']=evidence
                retain_inputs(p,evidence,current,content);values=deepcopy(baseline);values[stream['semantic_id']]=binding;p.player_art_overrides=validate(p,values);p.save()
                mr=models(p,str(p.root),source_key(p));ar=resources(p,str(p.root),source_key(p));model=mr['catalog']['models'][stream['player_index']]
                ctx=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=model['semantic_id'],catalog_source_key=mr['catalog']['source_key'],equipped=[0]*5,art_source_key=ar['catalog']['source_key'],stream_id=stream['semantic_id'],art_record_id=None,layer='retail',expected_current_sha256=None,frame_index=0,part_index=0)
                held=deepcopy((p._document(),p.undo_stack,p.redo_stack));i=inspect(p,**ctx);channels=deepcopy(i['channels']);channels['translation'][0]^=4
                args=dict(ctx,expected_current_slot_sha256=i['current_slot_sha256'],**channels);r=review(p,**args);pose=proposed_pose(p,review_key=r['review_key'],**args)
                self.assertEqual(r['ownership_after']['glb_import'],evidence);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
                cases.append(dict(model_report=mr,art_report=ar,model=model,selection={k:ctx[k] for k in ('equipped','stream_id','art_record_id','layer','expected_current_sha256')},inspection=i,review=r,pose=pose,edited_baseline=edited_baseline))
        path=os.getenv('PLAYER_ART_IMPORTED_OWNER_CASES')
        if path:
            out=Path(path);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(cases=cases,gameplay_verified=False)),encoding='utf-8')
        self.assertEqual(len(cases),2);print('Two fresh imported Current/numeric Review/pose fixtures: Retail and edited selected/neighbor baselines, exact preserved receipts and no mutation passed',flush=True)


if __name__=='__main__':unittest.main()

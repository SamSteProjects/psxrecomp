import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
from importer.player_art_authoring import owner
from sdk.project import ProjectService,ProjectError
from sdk.project_assets import source_key
from sdk.player_art_glb import prepare_input,retain_inputs,_path,export_input
from sdk.player_art_store import context,validate
from sdk.player_art_animation import resources
from sdk.player_battle import resources as models
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.getenv('PLAYER_ART_CURRENT_EXPORT_CASES') and os.getenv('LEGAIA_DISC_BIN'),'Private source fixtures required')
class ArtInputRecoveryTests(unittest.TestCase):
    def test_registration_download_numeric_history_and_refusals(self):
        cases=json.loads(Path(os.environ['PLAYER_ART_CURRENT_EXPORT_CASES']).read_text(encoding='utf-8'))['cases']
        case=next(c for c in cases if c['selection']['mode']=='clip' and c['selection']['layer']=='retail')
        stream=case['inspection']['base_playback']['stream'];content=base64.b64decode(case['export']['glb_base64'])
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
            raw,catalog,_=context(p);at=stream['source_record']['slot_offset'];original=raw[at:at+0x10800]
            _,analysis,evidence=prepare_input(p,original,catalog,stream['archive_asset_id'],stream['semantic_id'],original,{},content,
                equipped=case['inspection']['base_playback']['base_inspection']['assembly']['equipped'],fps=23.5)
            value=owner(original,catalog,stream['archive_asset_id'],stream['semantic_id'],analysis['edits']);value['glb_import']=evidence
            retain_inputs(p,evidence,original,content);p.player_art_overrides=validate(p,{stream['semantic_id']:value})
            p.undo_stack.append(dict(target='player_art_overrides',before={},after=deepcopy(p.player_art_overrides),label='PLAYER Art GLB'));p.save()
            held=deepcopy((p._document(),p.undo_stack,p.redo_stack));key=source_key(p)
            report=resources(p,str(p.root),key);self.assertEqual(len(report['retained_art_inputs']),1);record=report['retained_art_inputs'][0]
            args=dict(expected_project_path=str(p.root),expected_source_key=key,asset_id=record['semantic_id'])
            with http_server(p) as (_,post):
                status,download=post('/api/player-art-input-export',args);self.assertEqual(status,200,download)
                self.assertEqual(base64.b64decode(download['glb_base64']),content);self.assertEqual(download['record'],record)
                self.assertIn('player-art-input-',download['filename'])
                for bad in [dict(args,extra=True),dict(args,expected_source_key='0'*64),dict(args,asset_id='absent'),dict(args,expected_project_path='wrong')]:
                    status,error=post('/api/player-art-input-export',bad);self.assertEqual(status,400,error)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            proof=os.getenv('PLAYER_ART_INPUT_CASES')
            if proof:
                path=Path(proof);path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps(dict(art_report=report,model_report=models(p,str(p.root),key),export=download,gameplay_verified=False)),encoding='utf-8')
            # Changed final numeric channels retain the same historical bytes/ID.
            rows=deepcopy(value['edits']);rows[0]['translation'][0]^=2
            later=owner(original,catalog,stream['archive_asset_id'],stream['semantic_id'],rows);later['glb_import']=deepcopy(evidence)
            p.player_art_overrides=validate(p,{stream['semantic_id']:later})
            with self.assertRaises(ProjectError):export_input(p,**args)
            updated=resources(p,str(p.root),source_key(p))['retained_art_inputs'][0]
            self.assertEqual(updated['semantic_id'],record['semantic_id']);self.assertNotEqual(updated['current_body_sha256'],record['current_body_sha256'])
            recovered=export_input(p,**dict(args,expected_source_key=source_key(p)));self.assertEqual(base64.b64decode(recovered['glb_base64']),content)
            p.save();p=ProjectService.open(p.root)
            self.assertEqual(resources(p,str(p.root),source_key(p))['retained_art_inputs'][0],updated)
            path=_path(p,evidence['glb_sha256'],'glb');path.write_bytes(content[:-1]+bytes([content[-1]^1]))
            with self.assertRaises(ProjectError):resources(p,str(p.root),source_key(p))
            with self.assertRaises(ProjectError):export_input(p,**dict(args,expected_source_key=source_key(p)))
            path.write_bytes(content);p.player_art_overrides={}
            self.assertEqual(resources(p,str(p.root),source_key(p))['retained_art_inputs'],[])
            with self.assertRaises(ProjectError):export_input(p,**dict(args,expected_source_key=source_key(p)))
            self.assertEqual(sha256(path.read_bytes()).hexdigest(),evidence['glb_sha256'])
            print('Art input registry/recovery: exact HTTP bytes, stale/extra/absent identity refusals, later numeric Current independence, Save/Open and damaged/unregistered input refusal passed',flush=True)


if __name__=='__main__':unittest.main()

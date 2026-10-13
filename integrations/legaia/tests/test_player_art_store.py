import json
import os
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
import zipfile
from importer.pipeline import _disc_context, import_scene
from importer.player_art_authoring import owner
from importer.player_battle import decode_part
from importer.me_archive import entries
from sdk.project import ProjectService, ProjectError
from sdk.project_assets import source_key
from sdk.build import authored_state_key, build_project
from sdk.player_art_store import context, validate, composed_slots, prepare


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Private retail disc required')
class PlayerArtStoreTests(unittest.TestCase):
    def test_history_persistence_source_and_complete_package_readback(self):
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
            raw,catalog,profile=context(p);self.assertEqual(profile['allocation'],'not_supported')
            selected=[next(s for s in catalog['streams'] if s['player_index']==player and s['archive_role']==role and s['stream_index']==index) for player,role,index in [(0,'main',0),(0,'main',1),(1,'base',0)]]
            values={};baseline_key=source_key(p);baseline_build=authored_state_key(p);before=deepcopy(p._document())
            for stream in selected:
                at=stream['source_record']['slot_offset'];slot=raw[at:at+0x10800];decoded=entries(slot)[stream['stream_index']]['decoded'];channels=decode_part(decoded[2:11]);channels['translation'][0]^=1
                values[stream['semantic_id']]=owner(slot,catalog,stream['archive_asset_id'],stream['semantic_id'],[dict(frame_index=0,part_index=0,**channels)])
            p.player_art_overrides=validate(p,values);p.undo_stack.append(dict(target='player_art_overrides',before={},after=deepcopy(values),label='PLAYER Art Channels'));p.redo_stack.clear()
            after=deepcopy(p._document());self.assertNotEqual(source_key(p),baseline_key);self.assertNotEqual(authored_state_key(p),baseline_build)
            p.undo();self.assertEqual(p._document(),before);self.assertEqual(source_key(p),baseline_key)
            p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
            bad=deepcopy(values);bad[selected[0]['semantic_id']]['decoded_sha256']='0'*64
            held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):validate(p,bad)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            saved_file=p.root/'project.legaia.json';saved_bytes=saved_file.read_bytes();tampered=json.loads(saved_bytes);tampered['player_art_overrides']=bad
            try:
                saved_file.write_text(json.dumps(tampered),encoding='utf-8')
                with self.assertRaises(ProjectError):ProjectService.open(p.root)
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            finally:saved_file.write_bytes(saved_bytes)
            with _disc_context(p.disc_path) as (_,disc,_,archive):overlays,changes=prepare(p,archive,disc)
            self.assertEqual((len(overlays),len(changes)),(3,3));expected=bytearray(raw)
            slots=composed_slots(raw,catalog,values)
            for stream in selected:
                source=stream['source_record'];at=source['byte_offset'];size=source['byte_length'];local=at-source['slot_offset']
                expected[at:at+size]=slots[stream['archive_asset_id']][local:local+size]
            p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p)
            audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));owned=[o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_player_art_me_body'];self.assertEqual(len(owned),3)
            reconstructed=bytearray(raw)
            with zipfile.ZipFile(built['path']) as package:
                for overlay in owned:
                    payload=package.read(overlay['file']);self.assertEqual(payload,(Path(built['package_directory'])/overlay['file']).read_bytes());self.assertEqual(sha256(payload).hexdigest(),overlay['sha256']);source=overlay['source_record'];at=source['byte_offset'];size=source['byte_length'];self.assertEqual(sha256(raw[at:at+size]).hexdigest(),overlay['expected_sha256']);reconstructed[at:at+size]=payload
            self.assertEqual(reconstructed,expected)
            for archive in catalog['archives']:
                at=archive['slot_index']*0x10800;original=entries(raw[at:at+0x10800]);current=entries(bytes(reconstructed[at:at+0x10800]))
                for old,new in zip(original,current):
                    for field in ['size_word','byte_offset','byte_length']:self.assertEqual(new[field],old[field])
                    stream=next(s for s in catalog['streams'] if s['archive_asset_id']==archive['semantic_id'] and s['stream_index']==old['entry_index']);wanted=bytearray(old['decoded'])
                    if stream['semantic_id'] in values:wanted[2]^=1
                    self.assertEqual(new['decoded'],bytes(wanted))
            proof_dir=os.getenv('PLAYER_ART_STORE_PROOF_DIR')
            if proof_dir:
                out=Path(proof_dir);out.mkdir(parents=True,exist_ok=True);artifact=Path(built['path']).read_bytes();self.assertEqual(sha256(artifact).hexdigest(),built['sha256']);(out/'package.zip').write_bytes(artifact);(out/'store-proof.json').write_text(json.dumps(dict(owners=3,history=True,save_open=True,source_and_build_keys=True,complete_prot894_readback=True,all_stream_counts_and_neighbors=True,atomic_tampered_open_refusal=True,directory_zip_exact=True,package_sha256=built['sha256'],gameplay_verified=False),indent=2),encoding='utf-8')
            print('Three art owners: history/source/Open and complete PROT894 directory/ZIP readback passed',flush=True)


if __name__=='__main__':unittest.main()

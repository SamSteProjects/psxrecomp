import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from sdk.project import ProjectService, ProjectError, digest
from sdk.project_assets import source_key
from sdk.monster_texture_restoration import inspect, review, proposed_preview, apply


class MonsterTextureRestorationBoundaryTests(unittest.TestCase):
    def test_complete_pool_neighbors_exact_owner_removal_and_atomic_refusals(self):
        pool=bytes.fromhex('1f00')*240+bytes(16384); original=bytearray(0x4c)+bytearray(pool)
        struct.pack_into('<I',original,8,0x4c);original=bytes(original);current=bytearray(original)
        current[0x20]=19;current[0x4c+2]^=1;current[0x4c+481]=0x10;current=bytes(current)
        source=dict(byte_offset=0x4c,byte_length=len(pool),containing_size=len(original),
            containing_sha256=sha256(original).hexdigest(),sha256=sha256(pool).hexdigest(),
            compressed_bytes_consumed=999,compressed_stream_offset=0)
        record=dict(semantic_id='texture',source_record=source,width=128)
        owner=dict(edits=['literal'],png_import=dict(png_sha256='a'*64,stp_sha256='b'*64))
        p=SimpleNamespace(root=Path('literal-texture-project'),mode='edit',monster_palette_overrides={'texture':owner,'other':{'keep':1}},
            monster_model_overrides={'model':{'keep':2}},monster_motion_overrides={'motion':{'keep':3}},
            monster_record_overrides={'record':{'keep':4}},undo_stack=[],redo_stack=['redo'])
        candidate=current[:0x4c]+pool
        def snapshot(project,asset):return ({'source_key':'catalog'},record,original,current if 'texture' in project.monster_palette_overrides else candidate,b'x'*999,999)
        context=dict(expected_project_path=str(p.root),expected_source_key='source',asset_id='texture',palette_index=0)
        capacity=dict(original_encoded_size=999,new_encoded_size=900,decoded_size=len(original))
        with patch('sdk.monster_texture_restoration.snapshot',side_effect=snapshot),patch('sdk.monster_texture_restoration._fresh'),patch('sdk.monster_texture_restoration.validate',side_effect=lambda p,v:deepcopy(v)),patch('sdk.monster_texture_restoration.serialize_lzs_decoded',return_value=(b'',capacity)) as serializer:
            held=deepcopy(p.__dict__);observed=inspect(p,**context)
            args=dict(context,expected_current_block_sha256=observed['current_block_sha256'],expected_current_pool_sha256=observed['current_pool_sha256'],expected_owner_sha256=observed['owner_sha256'])
            value=review(p,**args);self.assertEqual(p.__dict__,held)
            self.assertEqual(base64.b64decode(value['candidate_block_base64']),candidate)
            self.assertEqual(base64.b64decode(value['candidate_pool_base64']),pool)
            self.assertEqual(candidate[:0x4c],current[:0x4c]);self.assertEqual(value['projection']['byte_change_count'],2)
            self.assertEqual(len(serializer.call_args.args[0]),999)
            for change in (dict(review_key='0'*64),dict(review_key=value['review_key'],expected_current_block_sha256='0'*64),dict(review_key=value['review_key'],expected_owner_sha256='0'*64)):
                with self.assertRaises(ProjectError):apply(p,**dict(args,**change))
                self.assertEqual(p.__dict__,held)
            result=apply(p,review_key=value['review_key'],**args);self.assertEqual(result['history_steps'],1)
            self.assertEqual(p.monster_palette_overrides,{'other':{'keep':1}})
            for name in ('monster_model_overrides','monster_motion_overrides','monster_record_overrides'):self.assertEqual(getattr(p,name),held[name])
            self.assertEqual(p.undo_stack[0]['before']['texture'],owner);self.assertEqual(p.redo_stack,[])
            with self.assertRaises(ProjectError):review(p,**args)
        p.monster_palette_overrides={'texture':owner}
        with patch('sdk.monster_texture_restoration.snapshot',return_value=({'source_key':'catalog'},record,original,original,b'x'*999,999)),patch('sdk.monster_texture_restoration._fresh'):
            observed=inspect(p,**context)
            with self.assertRaises(ProjectError):review(p,**dict(context,expected_current_block_sha256=observed['current_block_sha256'],expected_current_pool_sha256=observed['current_pool_sha256'],expected_owner_sha256=observed['owner_sha256']))


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail source is private')
class MonsterTextureRestorationWorkflowTests(unittest.TestCase):
    def prepare_project(self,root):
        from sdk.monster_archive import resources
        from sdk.monster_palettes import inspect as palette_inspect,review as palette_review,apply as palette_apply
        from sdk.monster_png import download,review as png_review,apply as png_apply
        from importer.texture_png import decode_png,_encode_png
        p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
        fresh=dict(expected_project_path=str(p.root),expected_source_key=source_key(p))
        catalog=resources(p,**fresh)['catalog'];asset='texture://legaia/monster-archive/0063/pool'
        context=dict(fresh,asset_id=asset,palette_index=0);i=palette_inspect(p,**context)
        args=dict(context,expected_current_sha256=i['current_pool_sha256']);downloaded=download(p,**args)
        image=decode_png(base64.b64decode(downloaded['png_base64']));rgba=bytearray(image['rgba']);rgba[:4]=bytes([0,255,0,255]);png=_encode_png(image['width'],image['height'],bytes(rgba))
        mask=decode_png(base64.b64decode(downloaded['stp_base64']));mask_rgba=bytearray(mask['rgba']);mask_rgba[:4]=bytes([255,255,255,255]);stp=_encode_png(mask['width'],mask['height'],bytes(mask_rgba))
        body=dict(args,png_base64=base64.b64encode(png).decode(),stp_base64=base64.b64encode(stp).decode(),palette_mode='rebuild');r=png_review(p,**body);png_apply(p,review_key=r['review_key'],**body)
        for identifier,palette in ((asset,14),('texture://legaia/monster-archive/0062/pool',0)):
            context=dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=identifier,palette_index=palette);i=palette_inspect(p,**context)
            body=dict(context,entry_index=3,word=i['preview']['words'][3]^1,expected_current_sha256=i['current_pool_sha256']);r=palette_review(p,**body);palette_apply(p,review_key=r['review_key'],**body)
        return p,catalog

    def test_png_later_numeric_all_owners_recovery_history_open_and_package(self):
        from sdk.monster_model_authoring import export as model_export,review as model_review,apply as model_apply
        from sdk.monster_motion_authoring import inspect as motion_inspect,review as motion_review,apply as motion_apply
        from sdk.monster_record_authoring import inspect as record_inspect,review as record_review,apply as record_apply
        from sdk.monster_palettes import snapshot
        from sdk.monster_png import path,records
        from sdk.build import build_project
        from importer.pipeline import import_scene
        from importer.core import decompress_lzs
        from test_monster_model_authoring import shifted_glb
        with tempfile.TemporaryDirectory() as root:
            p,catalog=self.prepare_project(root);asset='texture://legaia/monster-archive/0063/pool';model='asset://legaia/models/monster-archive/0063'
            def fresh():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p))
            def context():return dict(fresh(),asset_id=model,catalog_source_key=catalog['source_key'])
            exported=model_export(p,**context());body=dict(context(),binding=exported['binding'],glb_base64=base64.b64encode(shifted_glb(base64.b64decode(exported['glb_base64']))).decode());r=model_review(p,**body);model_apply(p,review_key=r['review_key'],**body)
            clip=next(c for c in catalog['animations'] if c['model_asset_id']==model and c['preview_supported'])
            i=motion_inspect(p,**context(),animation_id=clip['semantic_id'],frame_index=0,part_index=0);t=i['channels']['translation'].copy();t[0]+=1
            body=dict(context(),animation_id=clip['semantic_id'],frame_index=0,part_index=0,translation=t,rotation_psx=i['channels']['rotation_psx'],expected_current_block_sha256=i['current_block_sha256']);r=motion_review(p,**body);motion_apply(p,review_key=r['review_key'],**body)
            i=record_inspect(p,**context());name=i['fields'][0]['name'] if 'name' in i['fields'][0] else i['fields'][0]['field'];values={name:i['current_values'][name]+1}
            body=dict(context(),expected_current_block_sha256=i['current_block_sha256'],values=values);r=record_review(p,**body);record_apply(p,review_key=r['review_key'],**body)
            p.save();p=ProjectService.open(p.root)
            def rcontext():return dict(fresh(),asset_id=asset,palette_index=0)
            observed=inspect(p,**rcontext());args=dict(rcontext(),expected_current_block_sha256=observed['current_block_sha256'],expected_current_pool_sha256=observed['current_pool_sha256'],expected_owner_sha256=observed['owner_sha256']);r=review(p,**args);comparison=proposed_preview(p,review_key=r['review_key'],**args)
            held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            for change in (dict(review_key='0'*64),dict(review_key=r['review_key'],expected_current_pool_sha256='0'*64),dict(review_key=r['review_key'],expected_owner_sha256='0'*64)):
                with self.assertRaises(ProjectError):apply(p,**dict(args,**change))
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            i=record_inspect(p,**context());body=dict(context(),expected_current_block_sha256=i['current_block_sha256'],values={name:i['current_values'][name]+1});n=record_review(p,**body);record_apply(p,review_key=n['review_key'],**body)
            stale=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):apply(p,review_key=r['review_key'],**args)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),stale)
            observed=inspect(p,**rcontext());args=dict(rcontext(),expected_current_block_sha256=observed['current_block_sha256'],expected_current_pool_sha256=observed['current_pool_sha256'],expected_owner_sha256=observed['owner_sha256']);r=review(p,**args);comparison=proposed_preview(p,review_key=r['review_key'],**args)
            before=deepcopy(p._document());others={name:deepcopy(getattr(p,name)) for name in ('monster_model_overrides','monster_motion_overrides','monster_record_overrides')};other_texture=deepcopy(p.monster_palette_overrides['texture://legaia/monster-archive/0062/pool'])
            original,current=snapshot(p,asset)[2:4];at=observed['record']['source_record']['byte_offset'];candidate=base64.b64decode(r['candidate_block_base64']);self.assertEqual(candidate[:at],current[:at]);self.assertEqual(candidate[at:],original[at:]);self.assertNotEqual(candidate[:0x4c],original[:0x4c])
            owner=p.monster_palette_overrides[asset];receipt=owner['png_import'];retained={path(p,receipt[k+'_sha256'],suffix):path(p,receipt[k+'_sha256'],suffix).read_bytes() for k,suffix in [('png','png'),('stp','png'),('baseline','pool')]};image=owner['image_override'];retained[path(p,image['sha256'],'idx')]=path(p,image['sha256'],'idx').read_bytes();self.assertEqual(len(records(p,catalog)),2)
            history=len(p.undo_stack);result=apply(p,review_key=r['review_key'],**args);self.assertEqual(len(p.undo_stack),history+1);self.assertNotIn(asset,p.monster_palette_overrides);self.assertEqual(p.monster_palette_overrides['texture://legaia/monster-archive/0062/pool'],other_texture)
            for name,value in others.items():self.assertEqual(getattr(p,name),value)
            self.assertEqual(records(p,catalog),[])
            for target,data in retained.items():self.assertEqual(target.read_bytes(),data)
            self.assertEqual(snapshot(p,asset)[3],candidate);after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before);self.assertEqual(len(records(p,catalog)),2);p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
            with self.assertRaises(ProjectError):review(p,**args)
            p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));overlay=next(o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_slot' and o['source_record']['monster_id']==63)
            with zipfile.ZipFile(built['path']) as package:
                payload=package.read(overlay['file']);self.assertEqual(decompress_lzs(payload,len(original))[0],candidate);self.assertEqual(payload,(Path(built['package_directory'])/overlay['file']).read_bytes())
            output=os.getenv('LEGAIA_MONSTER_TEXTURE_RESTORATION_CASES')
            if output:Path(output).write_text(json.dumps(dict(report=dict(project_path=observed['project_path'],project_source_key=observed['project_source_key'],catalog=catalog),record=dict(id=asset,data=observed['record']),inspection=observed,review=r,comparison=comparison,result=result,whole_pool_exact=True,neighbors_header_model_motion_record_exact=True,other_texture_preserved=True,recovery_bytes_preserved=True,active_inputs_removed=True,history=True,save_open=True,package_readback=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')

    def test_wide_numeric_pool_review_preview_is_read_only(self):
        from sdk.monster_archive import resources
        from sdk.monster_palettes import inspect as palette_inspect, review as palette_review, apply as palette_apply
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save();asset='texture://legaia/monster-archive/0001/pool'
            def context():return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),asset_id=asset,palette_index=0)
            catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog'];i=palette_inspect(p,**context());args=dict(context(),entry_index=3,word=i['preview']['words'][3]^1,expected_current_sha256=i['current_pool_sha256']);r=palette_review(p,**args);palette_apply(p,review_key=r['review_key'],**args)
            held=deepcopy((p._document(),p.undo_stack,p.redo_stack));i=inspect(p,**context());args=dict(context(),expected_current_block_sha256=i['current_block_sha256'],expected_current_pool_sha256=i['current_pool_sha256'],expected_owner_sha256=i['owner_sha256']);r=review(p,**args);comparison=proposed_preview(p,review_key=r['review_key'],**args)
            self.assertEqual(i['record']['width'],256);self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            output=os.getenv('LEGAIA_MONSTER_TEXTURE_RESTORATION_CASES')
            if output:Path(output).with_name('wide-cases.json').write_text(json.dumps(dict(report=dict(project_path=i['project_path'],project_source_key=i['project_source_key'],catalog=catalog),record=dict(id=asset,data=i['record']),inspection=i,review=r,comparison=comparison)),encoding='utf-8')

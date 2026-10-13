"""Whole-model restoration: ownership, opaque motion, retained inputs and delivery."""
import base64, json, os, tempfile, unittest, zipfile
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from sdk.project import ProjectService, ProjectError
from sdk.project_assets import source_key
from sdk.monster_model_restoration import review, apply, proposed_preview
from importer.serialization import compress_lzs

MODEL = 'asset://legaia/models/monster-archive/0063'
TEXTURE = 'texture://legaia/monster-archive/0063/pool'


def context(project, catalog, model=MODEL):
    return dict(expected_project_path=str(project.root), expected_source_key=source_key(project),
                asset_id=model, catalog_source_key=catalog['source_key'])


def author_coauthors(project):
    """Retained two-input model chain, GLB motion + later numeric, PNG and header."""
    from sdk.monster_archive import resources
    from sdk.monster_model_authoring import export as model_export, review as model_review, apply as model_apply
    from sdk.monster_motion_authoring import inspect as motion_inspect, review as motion_review, apply as motion_apply
    from sdk.monster_motion_glb import review as glb_review, apply as glb_apply
    from sdk.monster_palettes import inspect as palette_inspect
    from sdk.monster_png import download as png_download, review as png_review, apply as png_apply
    from sdk.monster_record_authoring import inspect as record_inspect, review as record_review, apply as record_apply
    from importer.texture_png import decode_png, _encode_png
    from test_monster_model_authoring import shifted_glb
    project.disc_path = os.environ['LEGAIA_DISC_BIN']; project.save()
    catalog = resources(project, expected_project_path=str(project.root), expected_source_key=source_key(project))['catalog']
    for model in (MODEL, MODEL, 'asset://legaia/models/monster-archive/0062'):
        exported = model_export(project, **context(project,catalog,model))
        content = shifted_glb(base64.b64decode(exported['glb_base64']))
        args = dict(context(project,catalog,model), binding=exported['binding'], glb_base64=base64.b64encode(content).decode())
        value = model_review(project, **args); model_apply(project, review_key=value['review_key'], **args)
    clips = [c for c in catalog['animations'] if c['model_asset_id']==MODEL and c['preview_supported']]
    selected = next(c for c in clips if c['entry_index']==0)
    other = next(c for c in clips if c['entry_index']!=0)
    observed = motion_inspect(project, **context(project,catalog), animation_id=selected['semantic_id'], frame_index=0, part_index=0)
    content = Path(os.environ['LEGAIA_MONSTER_EDITED_GLB']).read_bytes()
    args = dict(context(project,catalog), animation_id=selected['semantic_id'], expected_current_block_sha256=observed['current_block_sha256'],
                glb_base64=base64.b64encode(content).decode(),fps=24,animation_index=None,object_node_indices=None)
    value = glb_review(project,**args); glb_apply(project,review_key=value['review_key'],**args)
    receipt = deepcopy(project.monster_motion_overrides[selected['semantic_id']]['glb_import'])
    for clip,index in ((selected,1),(other,0)):
        observed=motion_inspect(project,**context(project,catalog),animation_id=clip['semantic_id'],frame_index=index,part_index=0)
        translation=observed['channels']['translation'].copy();translation[0]+=2
        args=dict(context(project,catalog),animation_id=clip['semantic_id'],frame_index=index,part_index=0,
                  expected_current_block_sha256=observed['current_block_sha256'],translation=translation,rotation_psx=observed['channels']['rotation_psx'])
        value=motion_review(project,**args);motion_apply(project,review_key=value['review_key'],**args)
    assert project.monster_motion_overrides[selected['semantic_id']]['glb_import']==receipt
    observed=palette_inspect(project,expected_project_path=str(project.root),expected_source_key=source_key(project),asset_id=TEXTURE,palette_index=0)
    args=dict(expected_project_path=str(project.root),expected_source_key=source_key(project),asset_id=TEXTURE,palette_index=0,expected_current_sha256=observed['current_pool_sha256'])
    downloaded=png_download(project,**args);pixels=decode_png(base64.b64decode(downloaded['png_base64']));rgba=bytearray(pixels['rgba']);rgba[:4]=bytes([0,255,0,255])
    args.update(png_base64=base64.b64encode(_encode_png(pixels['width'],pixels['height'],bytes(rgba))).decode(),palette_mode='rebuild')
    value=png_review(project,**args);png_apply(project,review_key=value['review_key'],**args)
    observed=record_inspect(project,**context(project,catalog))
    args=dict(context(project,catalog),expected_current_block_sha256=observed['current_block_sha256'],values={'stored_stats.hp':observed['current_values']['stored_stats.hp']+1,'stored_rewards.gold':observed['current_values']['stored_rewards.gold']+1})
    value=record_review(project,**args);record_apply(project,review_key=value['review_key'],**args)
    project.save()
    return catalog


class MonsterModelRestorationBoundaryTests(unittest.TestCase):
    def test_literal_overlapping_motion_recomposition_owner_removal_and_atomic_refusal(self):
        original=b''.join(sha256(str(i).encode()).digest() for i in range(10));owned=bytearray(original[76:276]);owned[32]^=1;owned[81]^=2;owned=bytes(owned)
        current=bytearray(original);current[76:276]=owned;current[10]^=3;current[215]^=4;current=bytes(current)
        packed=compress_lzs(original);source=dict(byte_offset=76,byte_length=200,disc={'sha256':'a'*64},compressed_stream_offset=0)
        record=dict(semantic_id='model',monster_id=63,source_record=source)
        edits=[dict(byte_offset=i,before_byte=a,after_byte=b) for i,(a,b) in enumerate(zip(original[76:276],owned)) if a!=b]
        owner=dict(inputs=[{'glb_sha256':'a'*64,'glb_byte_length':28}],edits=edits);other={'untouched':True}
        project=SimpleNamespace(root=Path('literal-project'),monster_model_overrides={'model':owner,'other':other},monster_motion_overrides={'action':{'source_record':{'monster_id':63}}},undo_stack=[],redo_stack=['redo'])
        catalog={'animations':[dict(semantic_id='action',monster_id=63,source_record=dict(byte_offset=200,byte_length=20))]}
        args=dict(expected_project_path=str(project.root),expected_source_key='source',asset_id='model',catalog_source_key='catalog',expected_current_block_sha256=sha256(current).hexdigest())
        calls=[]
        def motion(original,catalog,monster,values,candidate,project):
            calls.append(candidate);return candidate[:200]+current[200:220]+candidate[220:]
        with patch('sdk.monster_model_restoration.snapshot',return_value=(record,None,original,current,packed,len(packed))),patch('sdk.monster_model_restoration.effective',return_value=owned),patch('sdk.monster_model_restoration.model_baseline',return_value=original[:76]+owned+original[276:]),patch('sdk.monster_model_restoration.decode_catalog',return_value=catalog),patch('sdk.monster_model_restoration.compose_motion',side_effect=motion),patch('sdk.monster_model_restoration.validate',side_effect=lambda p,v:deepcopy(v)),patch('sdk.monster_model_restoration._fresh'):
            held=deepcopy(project.__dict__);value=review(project,**args);self.assertEqual(project.__dict__,held)
            candidate=base64.b64decode(value['candidate_block_base64']);expected=bytearray(current)
            for row in edits:expected[76+row['byte_offset']]=row['before_byte']
            self.assertEqual(candidate,bytes(expected));self.assertNotEqual(calls[0][200:220],candidate[200:220]);self.assertEqual(candidate[:0x4c],current[:0x4c]);self.assertEqual(candidate[200:220],current[200:220]);self.assertEqual(value['projection']['byte_change_count'],2)
            for changed in ({'review_key':'0'*64},{'review_key':value['review_key'],'expected_current_block_sha256':'0'*64}):
                with self.assertRaises(ProjectError):apply(project,**dict(args,**changed))
                self.assertEqual(project.__dict__,held)
            with patch('sdk.monster_model_restoration.compose_motion',side_effect=lambda o,c,m,v,b,project:b):
                with self.assertRaises(ProjectError):review(project,**args)
                self.assertEqual(project.__dict__,held)
            from importer.serialization import LzsCapacityError
            with patch('sdk.monster_model_restoration.serialize_lzs_decoded',side_effect=LzsCapacityError('Original consumed span cannot hold candidate')):
                with self.assertRaises(ProjectError):review(project,**args)
                self.assertEqual(project.__dict__,held)
            result=apply(project,review_key=value['review_key'],**args);self.assertEqual(result['history_steps'],1);self.assertEqual(project.monster_model_overrides,{'other':other});self.assertEqual(project.undo_stack[0]['before']['model'],owner);self.assertEqual(project.redo_stack,[])
            with self.assertRaises(ProjectError):review(project,**args)
        project.monster_model_overrides={'model':owner}
        with patch('sdk.monster_model_restoration.snapshot',return_value=(record,None,original,original,packed,len(packed))),patch('sdk.monster_model_restoration.effective',return_value=original[76:276]),patch('sdk.monster_model_restoration.model_baseline',return_value=original):
            with self.assertRaises(ProjectError):review(project,**dict(args,expected_current_block_sha256=sha256(original).hexdigest()))


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN') and os.getenv('LEGAIA_MONSTER_EDITED_GLB'),'Private source and edited monster motion GLB are required')
class MonsterModelRestorationWorkflowTests(unittest.TestCase):
    def test_saved_chain_motion_png_header_other_owner_history_and_native_delivery(self):
        from sdk.monster_archive import current_preview
        from sdk.monster_model_authoring import snapshot
        from sdk.monster_model_inputs import records
        from sdk.build import build_project
        from importer.pipeline import import_scene
        from importer.core import decompress_lzs
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));catalog=author_coauthors(p);p=ProjectService.open(p.root)
            inspected=current_preview(p,**context(p,catalog));args=dict(context(p,catalog),expected_current_block_sha256=inspected['current_block_sha256'])
            held=deepcopy((p._document(),p.undo_stack,p.redo_stack));value=review(p,**args);comparison=proposed_preview(p,review_key=value['review_key'],**args)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            for changed in ({'review_key':'0'*64},{'review_key':value['review_key'],'expected_current_block_sha256':'0'*64},{'review_key':value['review_key'],'catalog_source_key':'foreign'}):
                with self.assertRaises(ProjectError):apply(p,**dict(args,**changed))
                self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            # A new valid Current header edit makes a held Review stale atomically.
            from sdk.monster_record_authoring import inspect as ri,review as rr,apply as ra
            header=ri(p,**context(p,catalog));hargs=dict(context(p,catalog),expected_current_block_sha256=header['current_block_sha256'],values={'stored_rewards.gold':header['current_values']['stored_rewards.gold']+1});hv=rr(p,**hargs);ra(p,review_key=hv['review_key'],**hargs)
            stale=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):apply(p,review_key=value['review_key'],**args)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),stale)
            inspected=current_preview(p,**context(p,catalog));args=dict(context(p,catalog),expected_current_block_sha256=inspected['current_block_sha256']);value=review(p,**args);comparison=proposed_preview(p,review_key=value['review_key'],**args)
            record,texture,original,current,raw,used=snapshot(p,**context(p,catalog));candidate=base64.b64decode(value['candidate_block_base64']);model_at=record['source_record']['byte_offset'];owner=deepcopy(p.monster_model_overrides[MODEL]);expected=bytearray(current)
            for row in owner['edits']:expected[model_at+row['byte_offset']]=row['before_byte']
            self.assertEqual(candidate,bytes(expected));self.assertEqual(candidate[:0x4c],current[:0x4c]);self.assertNotEqual(candidate[:0x4c],original[:0x4c]);self.assertEqual(candidate[texture['source_record']['byte_offset']:],current[texture['source_record']['byte_offset']:])
            for clip in catalog['animations']:
                if clip['monster_id']==63:
                    at=clip['source_record']['byte_offset'];stop=at+clip['source_record']['byte_length'];self.assertEqual(candidate[at:stop],current[at:stop])
            at=model_at;end=at+record['source_record']['byte_length'];self.assertNotEqual(candidate[at:end],original[at:end],'Current action bytes lie inside the opaque model window and must survive restoration')
            retained={f:f.read_bytes() for f in (p.root/'Authored').rglob('*') if f.is_file()};before=deepcopy(p._document());motions=deepcopy(p.monster_motion_overrides);palettes=deepcopy(p.monster_palette_overrides);headers=deepcopy(p.monster_record_overrides);other=deepcopy(p.monster_model_overrides['asset://legaia/models/monster-archive/0062']);membership=records(p,catalog);self.assertEqual(len([r for r in membership if r['model_asset_id']==MODEL]),2)
            history=len(p.undo_stack);result=apply(p,review_key=value['review_key'],**args);self.assertEqual(len(p.undo_stack),history+1);self.assertEqual(result['history_steps'],1);self.assertNotIn(MODEL,p.monster_model_overrides);self.assertEqual(p.monster_model_overrides['asset://legaia/models/monster-archive/0062'],other);self.assertEqual((p.monster_motion_overrides,p.monster_palette_overrides,p.monster_record_overrides),(motions,palettes,headers));self.assertEqual(records(p,catalog),[r for r in membership if r['model_asset_id']!=MODEL]);self.assertEqual(snapshot(p,**context(p,catalog))[3],candidate)
            for path,data in retained.items():self.assertEqual(path.read_bytes(),data)
            after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),before);self.assertEqual(records(p,catalog),membership);p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root);self.assertEqual(p._document(),after)
            with self.assertRaises(ProjectError):review(p,**dict(context(p,catalog),expected_current_block_sha256=sha256(candidate).hexdigest()))
            p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p);audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'));overlays=[o for o in audit['overlays'] if o.get('source_kind')=='fixed_span_monster_slot'];self.assertEqual(len(overlays),2)
            directory=Path(built['package_directory'])
            with zipfile.ZipFile(built['path']) as package:
                directory_files={f.relative_to(directory).as_posix():f.read_bytes() for f in directory.rglob('*') if f.is_file()};self.assertEqual(set(directory_files),set(package.namelist()))
                for name,data in directory_files.items():self.assertEqual(package.read(name),data)
                for overlay in overlays:
                    payload=package.read(overlay['file'])
                    identifier=overlay['source_record']['monster_id'];native=snapshot(p,**context(p,catalog,f'asset://legaia/models/monster-archive/{identifier:04d}'))
                    self.assertEqual(decompress_lzs(payload,len(native[2]))[0],native[3]);self.assertEqual(len(payload),native[5])
                    if identifier==63:self.assertEqual(native[3],candidate);self.assertEqual(len(payload),used)
            for path,data in retained.items():self.assertEqual(path.read_bytes(),data)
            if os.getenv('LEGAIA_MONSTER_MODEL_RESTORATION_CASES'):
                Path(os.environ['LEGAIA_MONSTER_MODEL_RESTORATION_CASES']).write_text(json.dumps(dict(inspection=inspected,review=value,comparison=comparison,catalog=catalog,reverse_ledger_exact=True,header_pool_all_motion_neighbors_preserved=True,other_model_owner_preserved=True,retained_two_glb_chain=True,retained_motion_glb_plus_numeric=True,png_header_coauthors=True,historical_files_exact=True,active_membership_removed=True,one_history=True,undo_redo=True,save_open=True,whole_directory_zip_exact=True,native_package_readback=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')

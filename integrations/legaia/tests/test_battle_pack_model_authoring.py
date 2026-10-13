"""Original pack spans and independent literal GLB-to-native vertex projection."""
import os, struct, unittest
from copy import deepcopy
from hashlib import sha256
from importer.pipeline import _disc_context
from importer.battle_character_catalog import decode_catalog
from importer import battle_pack_model_authoring as native
from importer.core import ImportError
from importer.model_primitives import _qualified_model
from test_monster_model_authoring import shifted_glb


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Retail disc is private')
class BattlePackModelAuthoringTests(unittest.TestCase):
    def test_all_five_exact_roundtrips_literal_edits_and_protected_neighbors(self):
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (_, disc, _, archive):
            raw = archive.read_entry(archive.entry(1204))
        catalog = decode_catalog(raw, disc)
        held = deepcopy(catalog)
        for record in catalog['models']:
            source = record['source_record']; at = source['byte_offset']; end = at+source['byte_length']
            original = raw[at:end]
            glb, binding = native.export(raw, record, catalog)
            same, receipt = native.convert(raw, record, catalog, binding, glb)
            self.assertEqual(same, original)
            self.assertEqual(receipt['changes'], [])
            edited = shifted_glb(glb)
            candidate, plan = native.convert(raw, record, catalog, binding, edited)
            expected = bytearray(original)
            _, vectors = _qualified_model(original)
            for start, _, _, kind, count in vectors:
                if kind != 'vertex': continue
                for n in range(count):
                    offset = start+n*8
                    struct.pack_into('<h', expected, offset, struct.unpack_from('<h', expected, offset)[0]+1)
            self.assertEqual(candidate, bytes(expected))
            self.assertEqual(plan['candidate_tmd_sha256'], sha256(expected).hexdigest())
            composed = raw[:at]+candidate+raw[end:]
            self.assertEqual(composed[:at], raw[:at]); self.assertEqual(composed[end:], raw[end:])
            current_glb, current_binding = native.export(raw, record, catalog, candidate)
            self.assertEqual(native.convert(raw, record, catalog, current_binding, current_glb, candidate)[0], candidate)
            with self.assertRaises(ImportError):
                native.convert(raw, record, catalog, binding, edited, candidate)
            altered = deepcopy(binding); altered['current_tmd_sha256'] = '0'*64
            with self.assertRaises(ImportError): native.convert(raw, record, catalog, altered, edited)
            foreign = deepcopy(record); foreign['source_record']['byte_offset'] += 4
            with self.assertRaises(ImportError): native.export(raw, foreign, catalog)
            with self.assertRaises(ImportError): native.export(raw[:-1], record, catalog)
        self.assertEqual(catalog, held)


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Retail disc is private')
class BattlePackModelWorkflowTests(unittest.TestCase):
    def test_http_exact_fields_noop_and_stale_refuse_without_retained_files(self):
        import tempfile
        from pathlib import Path
        from sdk.project import ProjectService
        from sdk.project_assets import source_key
        from sdk.battle_character_resources import resources
        from test_model_primitive_workflow import http_server
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
            source=dict(expected_project_path=str(p.root),expected_source_key=source_key(p))
            catalog=resources(p,**source)['catalog']
            context=dict(source,asset_id=catalog['models'][0]['semantic_id'],catalog_source_key=catalog['source_key'])
            held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with http_server(p) as (_,post):
                status,current=post('/api/battle-pack-model-current',context);self.assertEqual(status,200,current)
                status,exported=post('/api/battle-pack-model-glb-export',context);self.assertEqual(status,200,exported)
                args=dict(context,binding=exported['binding'],glb_base64=exported['glb_base64'],
                          expected_current_entry_sha256=exported['current_entry_sha256'])
                status,reviewed=post('/api/battle-pack-model-glb-review',args);self.assertEqual(status,200,reviewed)
                self.assertEqual(reviewed['projection']['changes'],[])
                self.assertEqual(post('/api/battle-pack-model-glb-apply',dict(args,review_key=reviewed['review_key']))[0],400)
                for changed in ({'extra':True},{'expected_source_key':'0'*64},{'expected_current_entry_sha256':'0'*64},
                                {'expected_current_entry_sha256':True},{'asset_id':'foreign'},{'glb_base64':'not-base64'}):
                    self.assertEqual(post('/api/battle-pack-model-glb-review',dict(args,**changed))[0],400)
                self.assertEqual(post('/api/battle-pack-model-current',dict(context,frame_index=0))[0],400)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            self.assertFalse((p.root/'Authored'/'BattlePackModels').exists())

    def test_retained_replay_history_other_model_neighbors_and_package(self):
        import base64,json,tempfile,zipfile
        from pathlib import Path
        from sdk.project import ProjectService,ProjectError
        from sdk.project_assets import source_key
        from sdk.battle_character_resources import resources
        from sdk import battle_pack_model_authoring as service
        from sdk.battle_pack_models import path,compose
        from sdk.build import build_project
        from importer.pipeline import import_scene
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.disc_path=os.environ['LEGAIA_DISC_BIN'];p.save()
            original_document=deepcopy(p._document())
            self.assertNotIn('battle_pack_model_overrides',original_document)
            catalog=resources(p,expected_project_path=str(p.root),expected_source_key=source_key(p))['catalog']
            def ctx(index=0):
                return dict(expected_project_path=str(p.root),expected_source_key=source_key(p),
                    asset_id=catalog['models'][index]['semantic_id'],catalog_source_key=catalog['source_key'])
            def prepare(index=0):
                exported=service.export(p,**ctx(index));edited=shifted_glb(base64.b64decode(exported['glb_base64']))
                args=dict(ctx(index),binding=exported['binding'],glb_base64=base64.b64encode(edited).decode(),
                          expected_current_entry_sha256=exported['current_entry_sha256'])
                return args,service.review(p,**args)
            args,plan=prepare();held=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            with self.assertRaises(ProjectError):service.apply(p,review_key='0'*64,**args)
            self.assertEqual((p._document(),p.undo_stack,p.redo_stack),held)
            service.apply(p,review_key=plan['review_key'],**args);self.assertEqual(len(p.undo_stack),1)
            self.assertIn('Battle pack native models',p.unsaved_sections)
            after=deepcopy(p._document());p.undo();self.assertEqual(p._document(),original_document)
            p.redo();self.assertEqual(p._document(),after);p.save();p=ProjectService.open(p.root)
            self.assertEqual(p._document(),after)
            with self.assertRaises(ProjectError):service.apply(p,review_key=plan['review_key'],**args)
            first=service.current(p,**ctx());second_args,second_plan=prepare()
            service.apply(p,review_key=second_plan['review_key'],**second_args)
            self.assertEqual(len(p.battle_pack_model_overrides[ctx()['asset_id']]['inputs']),2)
            other_args,other_plan=prepare(3);service.apply(p,review_key=other_plan['review_key'],**other_args)
            other=deepcopy(p.battle_pack_model_overrides[ctx(3)['asset_id']])
            current=service.current(p,**ctx());exported=service.export(p,**ctx())
            review_args,reviewed=prepare()
            self.assertEqual(exported['current_tmd_base64'],current['current_tmd_base64'])
            owner=p.battle_pack_model_overrides[ctx()['asset_id']]
            glb=owner['inputs'][0];target=path(p,glb['glb_sha256'],'glb');good=target.read_bytes()
            target.write_bytes(good[:-1]+bytes([good[-1]^1]));held=deepcopy((p._document(),p.undo_stack))
            with self.assertRaises(ProjectError):service.current(p,**ctx())
            self.assertEqual((p._document(),p.undo_stack),held);target.write_bytes(good)
            retained={f:f.read_bytes() for f in (p.root/'Authored'/'BattlePackModels').glob('*')}
            p.import_metadata(import_scene(p.disc_path,'town01'));p.save();built=build_project(p)
            audit=json.loads(Path(built['audit']).read_text(encoding='utf-8'))
            overlays=[r for r in audit['overlays'] if r.get('source_kind')=='fixed_span_battle_pack_model']
            self.assertEqual(len(overlays),2)
            with _disc_context(p.disc_path) as (_,disc,_,archive):raw=archive.read_entry(archive.entry(1204))
            final=compose(p,raw,catalog)
            with zipfile.ZipFile(built['path']) as package:
                directory=Path(built['package_directory'])
                for file in directory.rglob('*'):
                    if file.is_file():self.assertEqual(package.read(file.relative_to(directory).as_posix()),file.read_bytes())
                for overlay in overlays:
                    source=overlay['source_record'];at=source['byte_offset'];size=source['byte_length']
                    self.assertEqual(package.read(overlay['file']),final[at:at+size])
            self.assertEqual(p.battle_pack_model_overrides[ctx(3)['asset_id']],other)
            for file,content in retained.items():self.assertEqual(file.read_bytes(),content)
            self.assertEqual(ProjectService.open(p.root)._document(),p._document())
            if os.getenv('LEGAIA_PACK_MODEL_CASES'):
                Path(os.environ['LEGAIA_PACK_MODEL_CASES']).write_text(json.dumps(dict(
                    report=dict(project_path=current['project_path'],project_source_key=current['project_source_key'],catalog=catalog),
                    record=dict(id=ctx()['asset_id'],type='model',data=catalog['models'][0]),
                    current=current,export=exported,review=reviewed,input_glb_base64=review_args['glb_base64'],
                    history=True,save_open=True,complete_retained_replay=True,other_model_preserved=True,
                    package_readback=True,package_sha256=built['sha256'],gameplay_verified=False)),encoding='utf-8')


if __name__ == '__main__': unittest.main()

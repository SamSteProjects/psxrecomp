from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from sdk.project import ProjectService,ProjectError,digest
from sdk.model_glb_sources import retain,read_source,source_path,validate_collection,apply
from importer.assets import decode_tmd
from importer.model_glb import export_model_glb
from test_model_glb import synthetic

class ModelSources(unittest.TestCase):
    def fixture(self):
        source=synthetic(((0x22,),));glb,profile=export_model_glb(source,decode_tmd(source))
        binding=dict(schema_version='legaia.model-glb-binding.v1',asset_id='asset://town01/models/scene-tmd/0000',scene_id='scene://town01',source_sha256=sha256(source).hexdigest(),effective_sha256=sha256(source).hexdigest(),project_source_key='a'*64,profile=profile,external_object_nodes=[0])
        return source,glb,binding

    def test_exact_input_mapping_persists_and_file_tampering_rejects(self):
        source,raw,binding=self.fixture()
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));records,row=retain(p,{},raw,binding,sha256(source).hexdigest(),'b'*64)
            self.assertEqual(row['binding'],binding);self.assertEqual(read_source(p,row),raw)
            p.model_sources=records;p.save();opened=ProjectService.open(p.root)
            self.assertEqual(opened.model_sources,records);self.assertEqual(read_source(opened,row),raw)
            source_path(p,row).write_bytes(b'X'*len(raw))
            with self.assertRaises(ProjectError):p.save()
            with self.assertRaises(ProjectError):ProjectService.open(p.root)

    def test_receipt_digest_mapping_and_collection_bounds(self):
        source,raw,binding=self.fixture()
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));records,row=retain(p,{},raw,binding,sha256(source).hexdigest(),'b'*64)
            for change in (lambda r:r.update(extra=True),lambda r:r.update(candidate_sha256='c'*64),lambda r:r['binding'].update(external_object_nodes=[True])):
                changed=deepcopy(row);change(changed)
                with self.assertRaises(ProjectError):validate_collection({changed['receipt_key']:changed})
            many={}
            for i in range(33):
                value=deepcopy(row);value['review_key']=f'{i:064x}';value['receipt_key']=digest({k:v for k,v in value.items() if k!='receipt_key'});many[value['receipt_key']]=value
            with self.assertRaises(ProjectError):validate_collection(many)

    def test_grouped_undo_redo_and_failed_publication_restore_sources_history(self):
        source,raw,binding=self.fixture()
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));report=dict(proposed_sha256=sha256(source).hexdigest(),review_key='b'*64)
            def command(*args):p.undo_stack.append(dict(target='model_overrides',before={},after={}))
            with patch('sdk.scene_preview.source_key',return_value='a'*64),patch.object(p,'set_model_replacement',side_effect=command):
                row=apply(p,binding['asset_id'],source,raw,binding,report)
            after=deepcopy(p.model_sources);self.assertEqual(len(p.undo_stack),1);p.undo();self.assertEqual(p.model_sources,{})
            p.redo();self.assertEqual(p.model_sources,after);self.assertEqual(read_source(p,row),raw)
            before=deepcopy((p.model_overrides,p.model_sources,p.undo_stack,p.redo_stack))
            def fail(*args):p.undo_stack.append({});p.model_sources={};raise ProjectError('native publication failed')
            with patch('sdk.scene_preview.source_key',return_value='a'*64),patch.object(p,'set_model_replacement',side_effect=fail),self.assertRaises(ProjectError):
                apply(p,binding['asset_id'],source,raw,binding,dict(report,review_key='c'*64))
            self.assertEqual((p.model_overrides,p.model_sources,p.undo_stack,p.redo_stack),before)

class ModelSourceRemoval(unittest.TestCase):
    fixture = ModelSources.fixture
    def test_reviewed_metadata_removal_shared_blob_and_history(self):
        from sdk.model_glb_sources import review_removal
        source,raw,binding=self.fixture()
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.active_scene=binding['scene_id']
            p.model_sources,row=retain(p,{},raw,binding,sha256(source).hexdigest(),'b'*64)
            p.model_sources,second=retain(p,p.model_sources,raw,binding,sha256(source).hexdigest(),'c'*64)
            native=deepcopy(p.model_overrides);records=deepcopy(p.model_sources)
            with patch('sdk.scene_preview.source_key',return_value='a'*64),patch.object(p,'_model_source',return_value=source):
                request=dict(asset_id=binding['asset_id'],expected_source_key='a'*64,receipt_key=row['receipt_key'])
                review=review_removal(p,**request);self.assertEqual(review['shared_blob_receipts'],2);self.assertEqual(review['registered_bytes_released'],0)
                p.command(dict(request,type='remove_model_source',review_key=review['review_key']))
                self.assertEqual(p.model_overrides,native);self.assertEqual(len(p.model_sources),1);self.assertEqual(len(p.undo_stack),1)
                self.assertEqual(read_source(p,row),raw);p.undo();self.assertEqual(p.model_sources,records);p.redo();self.assertEqual(len(p.model_sources),1)
                request['receipt_key']=second['receipt_key'];review=review_removal(p,**request);self.assertEqual(review['registered_bytes_released'],len(raw))
                p.command(dict(request,type='remove_model_source',review_key=review['review_key']));self.assertEqual(p.model_sources,{})
                self.assertEqual(read_source(p,row),raw);p.active_scene=None;p.save();self.assertEqual(ProjectService.open(p.root).model_sources,{})

    def test_stale_project_collection_and_forged_review_fail_without_publication(self):
        from sdk.model_glb_sources import review_removal
        source,raw,binding=self.fixture()
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.active_scene=binding['scene_id'];p.model_sources,row=retain(p,{},raw,binding,sha256(source).hexdigest(),'b'*64)
            with patch('sdk.scene_preview.source_key',return_value='a'*64),patch.object(p,'_model_source',return_value=source):
                request=dict(asset_id=binding['asset_id'],expected_source_key='a'*64,receipt_key=row['receipt_key']);review=review_removal(p,**request)
                before=deepcopy((p.model_sources,p.undo_stack,p.redo_stack))
                with self.assertRaises(ProjectError):p.command(dict(request,type='remove_model_source',review_key='0'*64))
                p.name='Changed project'
                with self.assertRaises(ProjectError):p.command(dict(request,type='remove_model_source',review_key=review['review_key']))
                self.assertEqual((p.model_sources,p.undo_stack,p.redo_stack),before)
                p.mode='live'
                with self.assertRaises(ProjectError):review_removal(p,**request)

class ModelSourceLibrary(unittest.TestCase):
    fixture=ModelSources.fixture
    def test_cross_scene_recovery_removal_history_and_native_staleness(self):
        import base64
        from sdk.model_glb_sources import library,library_download,library_removal_review
        source,raw,binding=self.fixture()
        with TemporaryDirectory() as directory:
            p=ProjectService(Path(directory))
            p.model_sources,row=retain(p,{},raw,binding,sha256(source).hexdigest(),'b'*64)
            other=dict(binding,asset_id='asset://town0c/models/scene-tmd/0001',scene_id='scene://town0c')
            p.model_sources,second=retain(p,p.model_sources,raw,other,sha256(source).hexdigest(),'c'*64)
            value=library(p,str(p.root));self.assertEqual(value['receipt_count'],2);self.assertEqual(value['distinct_glb_count'],1);self.assertEqual(value['registered_byte_length'],len(raw))
            p.active_scene='scene://different';self.assertEqual(library(p,str(p.root))['library_key'],value['library_key'])
            request=dict(receipt_key=second['receipt_key'],expected_project_path=str(p.root),expected_library_key=value['library_key'])
            self.assertEqual(base64.b64decode(library_download(p,**request)['glb_base64']),raw)
            report=library_removal_review(p,**request);self.assertEqual(report['registered_bytes_released'],0)
            p.model_overrides={'changed':{}}
            with self.assertRaises(ProjectError):p.command(dict(request,type='remove_project_model_source',review_key=report['review_key']))
            p.model_overrides={};before=deepcopy(p.model_sources)
            p.command(dict(request,type='remove_project_model_source',review_key=report['review_key']))
            self.assertEqual(len(p.undo_stack),1);self.assertEqual(p.model_overrides,{});self.assertEqual(read_source(p,second),raw)
            p.undo();self.assertEqual(p.model_sources,before);p.redo();self.assertEqual(len(p.model_sources),1)
            with self.assertRaises(ProjectError):library_download(p,**request)
            p.mode='live';live=library(p,str(p.root));self.assertEqual(live['receipt_count'],1)
            with self.assertRaises(ProjectError):library_removal_review(p,receipt_key=row['receipt_key'],expected_project_path=str(p.root),expected_library_key=live['library_key'])
            source_path(p,row).write_bytes(raw[:-1])
            with self.assertRaises(ProjectError):library(p,str(p.root))

if __name__=='__main__':unittest.main()

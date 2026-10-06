"""Bounded exact-input retention; receipts never authorize native replay."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from sdk.animation_sources import retain,read_source,validate_collection,source_path,apply
from sdk.project import ProjectError,digest,ProjectService
from test_animation_glb import document,encode


class AnimationSources(unittest.TestCase):
    def fixture(self):
        doc,payload=document([[([0,0,0],[0,0,0])]]*2)
        raw=encode(doc,payload);scene='scene://town01';target=scene+'/actors/man-p1/0011'
        binding=dict(schema_version='legaia.animation-glb-binding.v1',scene_id=scene,entity_id=target)
        args=dict(kind='imported',target_id=target,binding=binding,animation_index=None,
                  source_frame_indices=None,candidate_sha256='a'*64,review_key='b'*64)
        return raw,args

    def test_exact_input_deduplication_and_binding_choice_receipt(self):
        raw,args=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            project=SimpleNamespace(root=Path(directory))
            records,receipt=retain(project,{},raw,**args)
            self.assertEqual(read_source(project,receipt),raw)
            again,_=retain(project,records,raw,**args);self.assertEqual(again,records)
            args['animation_index']=0
            changed,second=retain(project,records,raw,**args)
            self.assertEqual(len(changed),2);self.assertNotEqual(receipt['receipt_key'],second['receipt_key'])
            self.assertEqual(source_path(project,receipt),source_path(project,second))

    def test_missing_corrupt_and_changed_size_inputs_reject(self):
        raw,args=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            project=SimpleNamespace(root=Path(directory));_,receipt=retain(project,{},raw,**args)
            path=source_path(project,receipt)
            path.write_bytes(bytes(len(raw)))
            with self.assertRaisesRegex(ProjectError,'hash'):read_source(project,receipt)
            path.write_bytes(raw[:-1])
            with self.assertRaisesRegex(ProjectError,'size'):read_source(project,receipt)
            path.unlink()
            with self.assertRaisesRegex(ProjectError,'missing'):read_source(project,receipt)

    def test_changed_receipt_and_cross_target_binding_reject_before_write(self):
        raw,args=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            project=SimpleNamespace(root=Path(directory));records,receipt=retain(project,{},raw,**args)
            for field,value in [('binding',{}),('animation_index',True),('byte_length',10**400),('target_id','../escape')]:
                bad=deepcopy(receipt);bad[field]=value;bad['receipt_key']=digest({k:v for k,v in bad.items() if k!='receipt_key'})
                with self.assertRaises(ProjectError):validate_collection({bad['receipt_key']:bad})
            bad=deepcopy(receipt);bad['review_key']='c'*64
            with self.assertRaisesRegex(ProjectError,'receipt changed'):validate_collection({bad['receipt_key']:bad})
            self.assertEqual(read_source(project,receipt),raw)

    def test_retained_uuid_requires_exact_binding_and_bounded_mapping(self):
        raw,args=self.fixture();target='11111111-1111-4111-8111-111111111111'
        args.update(kind='retained',target_id=target,source_frame_indices=[1,0,1],
                    binding=dict(schema_version='legaia.animation-record-glb-binding.v1',scene_id='scene://town01',record_id=target))
        with tempfile.TemporaryDirectory() as directory:
            project=SimpleNamespace(root=Path(directory));records,receipt=retain(project,{},raw,**args)
            self.assertEqual(read_source(project,receipt),raw)
            for frames in [[],[True],[-1],[65536],[0]*4097]:
                args['source_frame_indices']=frames
                with self.assertRaises(ProjectError):retain(project,records,raw,**args)

    def test_receipt_count_and_distinct_byte_budgets(self):
        raw,args=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            project=SimpleNamespace(root=Path(directory));_,receipt=retain(project,{},raw,**args)
            records={}
            for i in range(33):
                row=deepcopy(receipt);row['review_key']=f'{i:064x}'
                row['receipt_key']=digest({k:v for k,v in row.items() if k!='receipt_key'})
                records[row['receipt_key']]=row
            with self.assertRaisesRegex(ProjectError,'32'):validate_collection(records)
            records={}
            for i in range(3):
                row=deepcopy(receipt);row['glb_sha256']=f'{i:064x}';row['byte_length']=32*1024*1024
                row['receipt_key']=digest({k:v for k,v in row.items() if k!='receipt_key'})
                records[row['receipt_key']]=row
            with self.assertRaisesRegex(ProjectError,'64 MiB'):validate_collection(records)

    def test_late_native_failure_restores_registered_metadata_and_history(self):
        raw,args=self.fixture();args['binding']['project_source_key']='a'*64
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));project.overrides={'existing':{'value':1}}
            project.redo_stack=[{'existing':True}]
            before=deepcopy((project.overrides,project.animation_sources,project.undo_stack,project.redo_stack))
            def fail(command):
                project.overrides.clear();project.undo_stack.append({'partial':True});project.redo_stack.clear()
                raise ProjectError('late native failure')
            project.command=fail
            with patch('sdk.scene_preview.source_key',return_value='a'*64):
                with self.assertRaisesRegex(ProjectError,'late native failure'):apply(project,{},raw,**args)
            self.assertEqual((project.overrides,project.animation_sources,project.undo_stack,project.redo_stack),before)


    def test_removal_frees_current_budget_and_preserves_native_and_undo(self):
        from sdk.animation_sources import review_removal
        raw,args=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));project.active_scene='scene://town01'
            records,row=retain(project,{},raw,**args);project.animation_sources=records
            project.overrides={'native':{'unchanged':True}};native=deepcopy(project.overrides)
            request=dict(scene_id=project.active_scene,target_id=args['target_id'],kind='imported',expected_source_key='a'*64)
            with patch('sdk.scene_preview.source_key',return_value='a'*64):
                report=review_removal(project,row['receipt_key'],**request)
                self.assertEqual(report['registered_bytes_released'],len(raw))
                project.command(dict(request,type='remove_animation_source',receipt_key=row['receipt_key'],review_key=report['review_key']))
                self.assertEqual(project.animation_sources,{});self.assertEqual(project.overrides,native)
                self.assertEqual(len(project.undo_stack),1);self.assertEqual(read_source(project,row),raw)
                project.undo();self.assertEqual(project.animation_sources,records)
                project.redo();self.assertEqual(project.animation_sources,{})
                source_path(project,row).unlink()
                before=deepcopy((project.animation_sources,project.undo_stack,project.redo_stack))
                with self.assertRaises(ProjectError):project.undo()
                self.assertEqual((project.animation_sources,project.undo_stack,project.redo_stack),before)
                self.assertEqual(project.overrides,native)

    def test_removal_review_rejects_native_collection_context_mode_and_absent_changes(self):
        from sdk.animation_sources import review_removal
        raw,args=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));project.active_scene='scene://town01'
            records,row=retain(project,{},raw,**args);project.animation_sources=records
            request=dict(scene_id=project.active_scene,target_id=args['target_id'],kind='imported',expected_source_key='a'*64)
            with patch('sdk.scene_preview.source_key',return_value='a'*64):
                report=review_removal(project,row['receipt_key'],**request)
                command=dict(request,type='remove_animation_source',receipt_key=row['receipt_key'],review_key=report['review_key'])
                project.overrides={'native':{'changed':True}}
                with self.assertRaisesRegex(ProjectError,'review removal'):project.command(command)
                project.overrides={}
                args['animation_index']=0
                project.animation_sources,second=retain(project,records,raw,**args)
                with self.assertRaisesRegex(ProjectError,'review removal'):project.command(command)
                shared=review_removal(project,row['receipt_key'],**request)
                self.assertEqual(shared['registered_bytes_released'],0);self.assertEqual(shared['shared_blob_receipts'],2)
                project.mode='live'
                with self.assertRaisesRegex(ProjectError,'Edit mode'):review_removal(project,row['receipt_key'],**request)
                project.mode='edit'
                with self.assertRaises(ProjectError):review_removal(project,'f'*64,**request)
                with self.assertRaises(ProjectError):review_removal(project,row['receipt_key'],**dict(request,target_id='other'))
                with self.assertRaises(ProjectError):review_removal(project,row['receipt_key'],**dict(request,expected_source_key='b'*64))
                self.assertEqual(project.undo_stack,[])


    def test_project_library_recovers_and_removes_without_active_scene(self):
        from sdk.animation_sources import library,library_download,library_removal_review
        import base64
        raw,args=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));records,row=retain(p,{},raw,**args);p.animation_sources=records
            p.active_scene=None
            value=library(p,str(p.root));self.assertEqual(value['imports'],[row]);self.assertEqual(value['registered_byte_length'],len(raw))
            request=dict(receipt_key=row['receipt_key'],expected_project_path=str(p.root),expected_library_key=value['library_key'])
            result=library_download(p,**request);self.assertEqual(base64.b64decode(result['glb_base64']),raw)
            review=library_removal_review(p,**request);p.command(dict(request,type='remove_project_animation_source',review_key=review['review_key']))
            self.assertEqual(p.animation_sources,{});self.assertEqual(p.overrides,{})
            p.undo();self.assertEqual(p.animation_sources,records);p.redo();self.assertEqual(p.animation_sources,{})
            p.save();opened=ProjectService.open(p.root);self.assertEqual(opened.animation_sources,{})
            self.assertEqual(read_source(p,row),raw)

    def test_project_library_stale_root_native_receipts_mode_and_missing_files_reject(self):
        from sdk.animation_sources import library,library_download,library_removal_review
        raw,args=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));records,row=retain(p,{},raw,**args);p.animation_sources=records
            value=library(p,str(p.root));request=dict(receipt_key=row['receipt_key'],expected_project_path=str(p.root),expected_library_key=value['library_key'])
            review=library_removal_review(p,**request);command=dict(request,type='remove_project_animation_source',review_key=review['review_key'])
            for change in ['native','receipts','mode']:
                p.overrides={};p.animation_sources=deepcopy(records);p.mode='edit'
                if change=='native':p.overrides={'changed':True}
                elif change=='receipts':p.animation_sources={}
                else:p.mode='live'
                with self.assertRaises(ProjectError):p.command(command)
                with self.assertRaises(ProjectError):library_download(p,**request)
                self.assertEqual(p.undo_stack,[])
            p.mode='edit';p.overrides={};p.animation_sources=records
            with self.assertRaises(ProjectError):library(p,str(p.root)+'-other')
            source_path(p,row).unlink()
            with self.assertRaises(ProjectError):library(p,str(p.root))
            with self.assertRaises(ProjectError):p.command(command)
            self.assertEqual(p.animation_sources,records);self.assertEqual(p.undo_stack,[])


class AnimationSourceComparison(unittest.TestCase):
    fixture=AnimationSources.fixture
    def test_imported_shared_clip_comparison_does_not_follow_actor_assignment(self):
        from contextlib import nullcontext
        from hashlib import sha256
        from test_animation_glb import record
        from test_animation_allocation import bank
        from sdk.animation_sources import library,compare_native
        source=record([[([0,0,0],[0,0,0])]]*2);source_hash=sha256(source).hexdigest();raw,args=self.fixture()
        args['binding'].update(animation_id='animation://town01/scene-anm/0000',asset_id='asset://town01/models/scene-tmd/0000',source_record_sha256=source_hash);args['candidate_sha256']=source_hash
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.disc_path=Path('private-retail.bin');p.imports={'scene://town01':{'actors':[{'semantic_id':args['target_id']}]}}
            p.animation_sources,row=retain(p,{},raw,**args);p.overrides={args['target_id']:{'ActorAllocatedAnimation':{'different_assignment':True}}}
            request=dict(receipt_key=row['receipt_key'],expected_project_path=str(p.root),expected_library_key=library(p,str(p.root))['library_key'])
            catalog=SimpleNamespace(referenced_animation_metadata=lambda:dict(bindings=[dict(semantic_id=args['binding']['animation_id'],asset_semantic_id=args['binding']['asset_id'],source_record={'record_sha256':source_hash})]))
            before=deepcopy((p.overrides,p.animation_sources,p.undo_stack,p.redo_stack))
            with patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()),patch('sdk.animation_record_ledger.verified_source',return_value=(bank([source]),catalog)),patch('sdk.animation_record_ledger.compose',return_value=(bank([source]),None)):
                result=compare_native(p,**request);self.assertTrue(result['matches_current']);self.assertEqual(result['comparison_scope'],'imported_shared_clip');self.assertTrue(result['active_in_native_bank'])
                self.assertEqual((p.overrides,p.animation_sources,p.undo_stack,p.redo_stack),before)
                with patch('importer.animation.decode_animation_record',return_value={'frame_count':2,'bone_count':65}):
                    with self.assertRaisesRegex(ProjectError,'rigid clip profile'):compare_native(p,**request)
                def changed(*args):p.disc_path=Path('changed.bin');return bank([source]),None
                with patch('sdk.animation_record_ledger.compose',side_effect=changed):
                    with self.assertRaisesRegex(ProjectError,'context changed'):compare_native(p,**request)
            with self.assertRaises(ProjectError):compare_native(p,**dict(request,expected_library_key='0'*64))

    def test_retired_retained_capture_is_reconstructed_without_native_publication(self):
        from contextlib import nullcontext
        from hashlib import sha256
        from test_animation_glb import record
        from test_animation_allocation import bank
        from importer.animation_allocation import allocate_animation_record
        from sdk.animation_sources import library,compare_native
        source=record([[([0,0,0],[0,0,0])]]*2);source_hash=sha256(source).hexdigest();raw,args=self.fixture();uuid='12345678-1234-4123-8123-123456789abc'
        captured,_=allocate_animation_record(source,source_hash,[1,0],[])
        args.update(kind='retained',target_id=uuid,binding=dict(schema_version='legaia.animation-record-glb-binding.v1',scene_id='scene://town01',record_id=uuid),source_frame_indices=[1,0],candidate_sha256=sha256(captured).hexdigest())
        entry=dict(record_id=uuid,donor_animation_id='animation://town01/scene-anm/0000',donor_frame_count=2,object_count=1,donor_record_sha256=source_hash,effective_donor_record_sha256=source_hash,donor_edits=[],source_frame_indices=[1,0],edits=[],record_sha256=sha256(captured).hexdigest())
        ledger=dict(source_bank_sha256=sha256(bank([source])).hexdigest(),records=[entry],removed_record_ids=[uuid])
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.disc_path=Path('private-retail.bin');p.animation_sources,row=retain(p,{},raw,**args);p.overrides={'scene://town01':{'AnimationRecords':deepcopy(ledger)}}
            request=dict(receipt_key=row['receipt_key'],expected_project_path=str(p.root),expected_library_key=library(p,str(p.root))['library_key'])
            before=deepcopy(p.overrides)
            with patch('importer.pipeline._disc_context',side_effect=lambda _:nullcontext()),patch('sdk.animation_record_ledger.verified_source',return_value=(bank([source]),None)),patch('sdk.animation_record_ledger.validate',return_value=ledger),patch('sdk.animation_record_ledger.verify_witnesses'):
                result=compare_native(p,**request);self.assertTrue(result['matches_current']);self.assertFalse(result['active_in_native_bank']);self.assertEqual(result['comparison_scope'],'retained_capture')
            self.assertEqual(p.overrides,before);self.assertFalse(p.undo_stack)

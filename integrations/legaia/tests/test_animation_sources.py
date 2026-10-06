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

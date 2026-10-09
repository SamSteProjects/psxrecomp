import os,tempfile,unittest
from copy import deepcopy
from sdk.animation_allocation import prepare_record_allocation,prepare_record_activation
from sdk.animation_record_comparison import compare
from sdk.animation_record_ledger import verified_source,reconstruct
from sdk.scene_preview import source_key
from sdk.project import ProjectError
import test_animation_glb_workflow as workflow
from test_model_primitive_workflow import http_server

@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetainedComparison(unittest.TestCase):
    def test_literal_native_channels_retired_http_readonly_and_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            p=workflow.AnimationGlbWorkflow().project(directory);owner='scene://town01/actors/man-p1/0011';ids=[]
            for sequence,edits in [([1,0,1],[dict(frame_index=0,object_index=0,translation={'z':123})]),([0,1,0,1],[dict(frame_index=1,object_index=0,translation={'x':234},rotation_psx={'y':64})])]:
                key=source_key(p);_,r=prepare_record_allocation(p,owner,sequence,edits,key)
                p.command(dict(type='allocate_animation_record',entity_id=owner,source_frame_indices=sequence,edits=edits,expected_source_key=key,review_key=r['review_key']));ids.append(r['proposed_ledger']['records'][-1]['record_id'])
            key=source_key(p);_,r=prepare_record_activation(p,p.active_scene,ids[0],False,key)
            p.command(dict(type='set_animation_record_active',scene_id=p.active_scene,record_id=ids[0],active=False,expected_source_key=key,review_key=r['review_key']))
            before=deepcopy((p._document(),p.imports,p.undo_stack,p.redo_stack));key=source_key(p)
            ledger=deepcopy(p.overrides[p.active_scene]['AnimationRecords']);ledger['removed_record_ids']=[]
            raw,_=verified_source(p,p.active_scene);payloads={r['record_id']:r['record'] for r in reconstruct(raw,ledger)}
            a,b=payloads[ids[0]],payloads[ids[1]];objects=a[0];expected=[]
            def native(data,frame,obj):
                row=data[8+(frame*objects+obj)*8:16+(frame*objects+obj)*8]
                xyz=[row[0]|((row[2]&15)<<8),row[1]|((row[2]>>4)<<8),row[3]|((row[4]&15)<<8)]
                return [n-4096 if n&2048 else n for n in xyz]+[n*16 for n in row[5:8]]
            for frame in range(3):
                for obj in range(objects):
                    left,right=native(a,frame,obj),native(b,frame,obj)
                    for index in range(6):
                        if left[index]!=right[index]:expected.append(dict(frame_index=frame,object_index=obj,field='translation' if index<3 else 'rotation_psx',axis='xyz'[index%3],left=left[index],right=right[index],delta=right[index]-left[index]))
            body=dict(scene_id=p.active_scene,left_record_id=ids[0],right_record_id=ids[1],expected_source_key=key)
            report=compare(p,**body);self.assertEqual(report['differences'],expected)
            self.assertFalse(report['left_active']);self.assertTrue(report['right_active']);self.assertEqual(report['right_only_frame_count'],1)
            self.assertEqual(report['native_byte_difference_count'],sum(x!=y for x,y in zip(a,b))+abs(len(a)-len(b)))
            self.assertTrue(compare(p,p.active_scene,ids[0],ids[0],key)['native_bytes_equal'])
            from unittest.mock import patch
            for field,value in [('donor_asset_id','asset://foreign/model'),('object_count',1)]:
                incompatible=deepcopy(ledger);incompatible['records'][1][field]=value
                with patch('sdk.animation_record_comparison.validate',return_value=incompatible),patch('sdk.animation_record_comparison.verified_source') as untouched:
                    with self.assertRaisesRegex(ProjectError,'same captured model'):compare(p,**body)
                    untouched.assert_not_called()

            with http_server(p) as (_,post):
                status,value=post('/api/animation-record-comparison',body);self.assertEqual(status,200,value);self.assertEqual(value,report)
                for bad in (dict(body,left_record_id='missing'),dict(body,right_record_id=None),dict(body,expected_source_key='0'*64),dict(body,extra=1),dict(body,scene_id='scene://other')):
                    status,_=post('/api/animation-record-comparison',bad);self.assertEqual(status,400)
            self.assertEqual((p._document(),p.imports,p.undo_stack,p.redo_stack),before)
            p.mode='live'
            with self.assertRaises(ProjectError):compare(p,**body)

if __name__=='__main__':unittest.main()

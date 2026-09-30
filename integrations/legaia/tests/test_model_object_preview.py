from hashlib import sha256
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from importer.core import ImportError
from importer.assets import decode_tmd
from importer.model_json import translate_shape_object,rotate_shape_object,scale_shape_object
from sdk.project import ProjectService,ProjectError
import test_model_rotation

class ModelObjectPreviewTests(unittest.TestCase):
    def test_preview_serializes_exact_apply_bytes_without_mutation(self):
        source=test_model_rotation.ModelRotationTests().source();digest=sha256(source).hexdigest()
        project=SimpleNamespace(mode='edit',active_scene='scene://test',model_overrides={},
                                _model_source=Mock(return_value=source),
                                preview_model_file=Mock(side_effect=lambda asset,data:{'project_changed':False,'proposed_sha256':sha256(data).hexdigest()}),
                                set_model_replacement=Mock())
        project._prepare_model_object=lambda *args: ProjectService._prepare_model_object(project,*args)
        cases=[('translation',{'offset':[2,-3,4]},translate_shape_object(source,source,digest,0,[2,-3,4])),
               ('rotation',{'axis':'z','quarter_turns':1},rotate_shape_object(source,source,digest,0,'z',1)),
               ('scale',{'percent':125},scale_shape_object(source,source,digest,0,125))]
        for op,values,expected in cases:
            result=ProjectService.preview_model_object(project,'model',0,op,values,digest)
            self.assertEqual(result['preview'],decode_tmd(expected))
            self.assertEqual(result['current_preview'],decode_tmd(source))
            project.preview_model_file.assert_called_with('model',expected)
        project.set_model_replacement.assert_not_called()
        for op,values in [('scale',{'percent':125,'extra':0}),('unknown',{}),('rotation',{'axis':'x'})]:
            with self.assertRaises(ProjectError):ProjectService.preview_model_object(project,'model',0,op,values,digest)
        with self.assertRaises(ImportError):ProjectService.preview_model_object(project,'model',0,'scale',{'percent':125},'0'*64)
        project.set_model_replacement.assert_not_called()
    def test_scene_instance_retains_pose_and_does_not_mutate_shared_geometry(self):
        from copy import deepcopy
        from sdk.scene_preview import preview_shape_instance
        from importer.animation import pose_vertices
        source=test_model_rotation.ModelRotationTests().source();digest=sha256(source).hexdigest()
        geometry=decode_tmd(source);transforms=[dict(object_index=0,translation=[3,4,5],rotation_psx=[0,0,1024])]
        geometry.update(posed=True,pose={'object_transforms':transforms})
        scene={'entities':[{'entity_id':'one','asset_id':'model','renderable':True,'geometry_key':'shared','model_to_scene':[1]*16},
                           {'entity_id':'two','asset_id':'model','renderable':True,'geometry_key':'shared'}],
               'assets':[{'geometry_key':'shared','asset_id':'model','preview':geometry}]}
        baseline=deepcopy(scene);replacement=translate_shape_object(source,source,digest,0,[12,-7,3])
        proposed=preview_shape_instance(scene,'model','one',replacement,{})
        expected=pose_vertices(decode_tmd(replacement)['vertices'],geometry['objects'],transforms)
        self.assertEqual(proposed['vertices'],expected)
        self.assertEqual(scene,baseline)
        self.assertEqual(proposed['representation'],'proposed-shape')
        self.assertNotIn('authored_shape',proposed)
        for asset,entity in [('other','one'),('model','missing')]:
            with self.assertRaises(ProjectError):preview_shape_instance(scene,asset,entity,replacement,{})
        geometry['pose']={}
        with self.assertRaises(ImportError):preview_shape_instance(scene,'model','one',replacement,{})

    def test_shared_scene_proposal_groups_distinct_poses_and_reports_unavailable(self):
        from copy import deepcopy
        from sdk.scene_preview import preview_shape_instances
        from importer.animation import pose_vertices
        source=test_model_rotation.ModelRotationTests().source();digest=sha256(source).hexdigest()
        first=decode_tmd(source);second=decode_tmd(source)
        transforms=[dict(object_index=0,translation=[3,4,5],rotation_psx=[0,0,1024])]
        second.update(posed=True,pose={'object_transforms':transforms})
        scene={'entities':[{'entity_id':'one','asset_id':'model','renderable':True,'geometry_key':'first'},
                           {'entity_id':'two','asset_id':'model','renderable':True,'geometry_key':'first'},
                           {'entity_id':'three','asset_id':'model','renderable':True,'geometry_key':'second'},
                           {'entity_id':'missing','asset_id':'model','renderable':False,'reason':'Unknown pose'},
                           {'entity_id':'other','asset_id':'other','renderable':True,'geometry_key':'first'}],
               'assets':[{'geometry_key':'first','asset_id':'model','preview':first},
                         {'geometry_key':'second','asset_id':'model','preview':second}]}
        baseline=deepcopy(scene);replacement=translate_shape_object(source,source,digest,0,[12,-7,3])
        report=preview_shape_instances(scene,'model',replacement,{})
        self.assertEqual(len(report['proposal_assets']),2)
        self.assertEqual(len(report['proposal_instances']),3)
        self.assertEqual(report['proposal_instances'][0]['geometry_key'],report['proposal_instances'][1]['geometry_key'])
        self.assertNotEqual(report['proposal_instances'][0]['geometry_key'],report['proposal_instances'][2]['geometry_key'])
        local=decode_tmd(replacement)['vertices']
        self.assertEqual(report['proposal_assets'][0]['preview']['vertices'],local)
        self.assertEqual(report['proposal_assets'][1]['preview']['vertices'],pose_vertices(local,second['objects'],transforms))
        self.assertEqual(report['unavailable_instances'],[{'entity_id':'missing','reason':'Unknown pose'}])
        self.assertEqual(scene,baseline)
        with self.assertRaises(ProjectError):preview_shape_instances(scene,'absent',replacement,{})
        second['pose']={}
        with self.assertRaises(ImportError):preview_shape_instances(scene,'model',replacement,{})

    def test_translation_rejects_stale_types_and_overflow(self):
        source=test_model_rotation.ModelRotationTests().source();digest=sha256(source).hexdigest()
        self.assertEqual(translate_shape_object(source,source,digest,0,[0,0,0]),source)
        for index,offset in [(True,[1,2,3]),(0,[True,0,0]),(0,[65535,0,0]),(0,[1,2])]:
            with self.assertRaises(ImportError):translate_shape_object(source,source,digest,index,offset)
        with self.assertRaises(ImportError):translate_shape_object(source,source,'0'*64,0,[0,0,0])

if __name__=='__main__':unittest.main()

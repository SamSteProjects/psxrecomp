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
    def test_translation_rejects_stale_types_and_overflow(self):
        source=test_model_rotation.ModelRotationTests().source();digest=sha256(source).hexdigest()
        self.assertEqual(translate_shape_object(source,source,digest,0,[0,0,0]),source)
        for index,offset in [(True,[1,2,3]),(0,[True,0,0]),(0,[65535,0,0]),(0,[1,2])]:
            with self.assertRaises(ImportError):translate_shape_object(source,source,digest,index,offset)
        with self.assertRaises(ImportError):translate_shape_object(source,source,'0'*64,0,[0,0,0])

if __name__=='__main__':unittest.main()

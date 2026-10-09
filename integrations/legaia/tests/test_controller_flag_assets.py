from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from sdk.project import ProjectService,ProjectError
from sdk.controller_flag_assets import build_controller_flag_assets
from sdk.flag_assets import validate_flag_asset
from sdk.asset_references import assemble
from test_controller_references import controller
from test_project_workflow import synthetic_scene


class ControllerFlagAssets(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.p=ProjectService(Path(directory.name));self.doc=synthetic_scene();self.doc['source']['disc_identity']='sha256:'+'a'*64
        self.p.import_metadata(self.doc);self.controller=controller()
        self.controller.update(name='Scene Entry Controller',inspection_status='decoded_supported_paths',flag_reference_count=2,
            flag_references=[dict(pc=pc,byte_offset=100+pc,mnemonic='SYSFLAG_SET',bank='system',operation='set',index=1,
                scope='system_bank_encoded_selector',extended_target=None,context_resolution='current_script_context',
                index_semantics='encoded_selector_not_resolved_runtime_bit',status='encoded_reference',runtime_value=None) for pc in [5,7]])
        self.groups=build_controller_flag_assets(self.controller,self.doc)

    def test_grouping_graph_and_read_only_owner(self):
        before=deepcopy(self.p._document());self.assertEqual(len(self.groups),1)
        group=self.groups[0];self.assertEqual(group['reference_count'],2)
        self.assertEqual(group['id'],'flag-reference://fixture/controllers/man-p1/0000/current/system/1')
        self.assertTrue(all(row['flag_operand_id'] is None for row in group['references']))
        validate_flag_asset(group)
        record=dict(group,kind='flag',layer='derived',scene_id='scene://fixture')
        catalog=dict(source_key='c'*64,records=[self.controller,record],limitations=[])
        report=assemble(self.p,catalog,group['id'])
        self.assertEqual([row['pc'] for row in report['incoming']],[5,7])
        self.assertTrue(all(row['kind']=='controller_flag_reference' and row['runtime_binding']=='not_asserted' for row in report['incoming']))
        self.assertEqual(before,self.p._document())
        group['references'][0]['index']=2;self.assertEqual(self.controller['flag_references'][0]['index'],1)

    def test_actor_authoring_and_source_substitution_refuse(self):
        for change in [lambda g:g.update(owner_id='scene://fixture/actors/man-p1/0001'),
                       lambda g:g['references'][0].update(authored_index=2,effective_index=2),
                       lambda g:g['references'][0].update(flag_operand_id=g['script_id']+'/flag-bit/0005'),
                       lambda g:g.update(runtime_value=1),
                       lambda g:g['controller_source_evidence'].update(execution='confirmed')]:
            forged=deepcopy(self.groups[0]);change(forged)
            with self.assertRaises(ProjectError):validate_flag_asset(forged)
        missing=deepcopy(self.groups[0]);missing['references'].pop();missing['reference_count']=1
        catalog=dict(source_key='c'*64,records=[self.controller,dict(missing,kind='flag',layer='derived',scene_id='scene://fixture')],limitations=[])
        with self.assertRaises(ProjectError):assemble(self.p,catalog,missing['id'])

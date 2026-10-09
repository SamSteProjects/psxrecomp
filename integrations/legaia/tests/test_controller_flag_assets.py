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

    def test_current_selector_retains_retail_group_and_dedicated_proof(self):
        from sdk.flag_qualification import from_target,validate
        group=self.groups[0];operand=group['script_id']+'/system-flag/0005';owner=group['owner_id']
        target=dict(owner_id=owner,semantic_id=operand,source_record_sha256=group['source_record']['sha256'],pc=5,mnemonic='SYSFLAG_SET',target_context=None,values={'index':1},maximum=4095)
        proof=from_target(target,{'index':2},controller=True)
        current=build_controller_flag_assets(self.controller,self.doc,{operand:{'index':2}},{operand:proof})[0]
        self.assertEqual(current['id'],group['id']);self.assertEqual(current['authored_reference_count'],1)
        self.assertEqual([(r['retail_index'],r['authored_index'],r['effective_index']) for r in current['references']],[(1,2,2),(1,None,1)])
        self.assertEqual(self.groups[0],group);validate_flag_asset(current)
        with self.assertRaises(ProjectError):validate(proof,owner,operand,target['source_record_sha256'],5,'SYSFLAG_SET',None,1,2)
        for mutate in [lambda r:r.pop('authored_qualification'),lambda r:r['authored_qualification'].update(schema_version='legaia.system-flag-operand-qualification.v1'),lambda r:r['authored_qualification'].update(source_record_sha256='f'*64),lambda r:r.update(effective_index=3)]:
            bad=deepcopy(current);mutate(bad['references'][0])
            with self.assertRaises(ProjectError):validate_flag_asset(bad)
        catalog=dict(source_key='c'*64,records=[self.controller,dict(current,kind='flag',layer='derived',scene_id='scene://fixture')],limitations=[])
        with self.assertRaises(ProjectError):assemble(self.p,catalog,current['id'])
        self.p.overrides[owner]={'ControllerSystemFlags':{'source_record_sha256':target['source_record_sha256'],'entries':{operand:{'index':2}}}}
        report=assemble(self.p,catalog,current['id']);self.assertEqual(len(report['incoming']),3)
        effective=next(e for e in report['incoming'] if e['kind']=='effective_controller_flag_reference')
        self.assertEqual((effective['layer'],effective['runtime_binding'],effective['pc']),('effective','not_asserted',5))
        self.assertEqual(effective['flag_binding_evidence']['native_operand_qualification'],proof)
        self.assertEqual((effective['flag_binding_evidence']['retail_index'],effective['flag_binding_evidence']['effective_index']),(1,2))
        from sdk.asset_references import assemble_project
        project=assemble_project(self.p,{'scene://fixture':catalog},current['id'])
        self.assertIn(effective,project['incoming'])
        self.p.overrides[owner]['ControllerSystemFlags']['entries'][operand]['index']=3
        with self.assertRaises(ProjectError):assemble(self.p,catalog,current['id'])

    def test_controller_edits_invalidate_scene_and_project_flag_keys(self):
        from sdk.resources import scene_flag_state_key,project_flag_state_key
        before=(scene_flag_state_key(self.p),project_flag_state_key(self.p))
        self.p.overrides['scene://fixture/controllers/man-p1/0000']={'ControllerSystemFlags':{'source_record_sha256':'a'*64,'entries':{'script://fixture/controllers/man-p1/0000/system-flag/0005':{'index':2}}}}
        self.assertNotEqual(before[0],scene_flag_state_key(self.p));self.assertNotEqual(before[1],project_flag_state_key(self.p))

    def test_current_bits_preserve_retail_groups_and_qualified_graphs(self):
        from sdk.flag_qualification import from_target
        from sdk.resources import scene_flag_state_key,project_flag_state_key
        import json,subprocess
        for bank,index,authored,extended in [('global',2,31,None),('local',2,15,7),('context',2,9,255)]:
            with self.subTest(bank=bank):
                self.p.overrides={};controller=deepcopy(self.controller)
                prefix={'global':'GFLAG','local':'LFLAG','context':'CFLAG'}[bank]
                # Use the shared canonical bank labels rather than runtime scope guesses.
                from sdk.flag_assets import _SCOPES
                scope=_SCOPES[bank]
                controller['flag_references']=controller['flag_references'][:1];controller['flag_reference_count']=1
                controller['flag_references'][0].update(mnemonic=prefix+'_TEST',bank=bank,operation='test',index=index,scope=scope,extended_target=extended,context_resolution='current_script_context' if extended is None else 'extended_target_unresolved',index_semantics='operand_masked_to_five_bits')
                owner=controller['semantic_id'].replace('script://','scene://');operand=controller['semantic_id']+'/flag-bit/0005'
                target=dict(owner_id=owner,semantic_id=operand,source_record_sha256=controller['source_record']['sha256'],pc=5,mnemonic=prefix+'_TEST',target_context=extended,values={'bit':index},maximum=15 if bank=='local' else 31)
                proof=from_target(target,{'bit':authored},controller=True)
                group=build_controller_flag_assets(controller,self.doc,{operand:{'bit':authored}},{operand:proof})[0]
                self.assertEqual((group['index'],group['references'][0]['effective_index']),(index,authored));validate_flag_asset(group)
                before=(scene_flag_state_key(self.p),project_flag_state_key(self.p))
                self.p.overrides[owner]={'ControllerFlagBits':{'source_record_sha256':target['source_record_sha256'],'entries':{operand:{'bit':authored}}}}
                self.assertNotEqual(before,(scene_flag_state_key(self.p),project_flag_state_key(self.p)))
                catalog=dict(source_key='c'*64,records=[controller,dict(group,kind='flag',layer='derived',scene_id='scene://fixture')],limitations=[])
                report=assemble(self.p,catalog,group['id'])
                effective=[e for e in report['incoming'] if e['kind']=='effective_controller_flag_reference'];self.assertEqual(len(effective),1)
                self.assertEqual(effective[0]['flag_binding_evidence']['native_operand_qualification'],proof)
                path=self.p.root/'bit-reference.json';path.write_text(json.dumps(dict(group=group,report=report)),encoding='utf-8')
                subprocess.run(['C:/Program Files/nodejs/node.exe',str(Path(__file__).with_name('test_controller_flag_bit_references.mjs')),str(path)],check=True)
                for change in [lambda r:r.pop('authored_qualification'),lambda r:r['authored_qualification'].update(schema_version='legaia.flag-operand-qualification.v1'),lambda r:r['authored_qualification'].update(extended_target=None if extended is not None else 1)]:
                    forged=deepcopy(group);change(forged['references'][0])
                    with self.assertRaises(ProjectError):validate_flag_asset(forged)
                self.p.overrides[owner]['ControllerFlagBits']['entries'][operand]['bit']=index
                with self.assertRaises(ProjectError):assemble(self.p,catalog,group['id'])

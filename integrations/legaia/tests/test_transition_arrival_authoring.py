from copy import deepcopy
from pathlib import Path
import tempfile, unittest, json
from unittest.mock import patch
from importer.transition_authoring import TransitionAuthoringContext
from importer.script_catalog import _catalog
from sdk.transition_arrival import review, apply
from sdk.scene_preview import source_key
from sdk.resources import project_transition_state_key
from sdk.project import ProjectService, ProjectError
from importer.core import ImportError as RetailImportError
from test_importer_dialogue_authoring import fixture
import test_transition_resource_workflow as workflow


class ArrivalAuthoring(unittest.TestCase):
    def test_review_apply_history_persistence_and_exact_native_bytes(self):
        helper=workflow.TransitionResourceWorkflow()
        with tempfile.TemporaryDirectory() as raw:
            p=helper.project(raw);disc=Path(raw)/'disc.bin';disc.write_bytes(bytes(512));p.disc_path=str(disc)
            destination=json.loads(json.dumps(p.imports[p.active_scene]).replace('fixture','town02'));p.imports['scene://town02']=destination
            source,man=fixture(b'\x3f\0\0\x06town02\x01\x82\xf3');ctx=TransitionAuthoringContext(source)
            catalog=_catalog(man,'fixture',{'synthetic':True},set());p.active_scene='scene://town02'
            request=dict(asset_id='transition://fixture/actors/man-p1/0001/0005',expected_project_key=project_transition_state_key(p),expected_destination_key=source_key(p),arrival={'x':256,'z':512,'facing_sector':2})
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with helper.discovery(p,catalog,ctx),patch('sdk.resources.import_scene',side_effect=lambda disc,name:p.imports['scene://'+name]),patch('sdk.transition_arrival._verify'),patch.object(p,'_dialogue_context',return_value=source):
                r=review(p,**request)
                self.assertEqual(r['proposed_arrival']['x'],256);self.assertEqual(r['proposed_arrival']['z'],512)
                self.assertEqual(r['proposed_encoded']['direction_encoded']&0xf8,0xf0)
                self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
                body=dict(asset_id=request['asset_id'],project_state_key=request['expected_project_key'],destination_source_key=request['expected_destination_key'],arrival=request['arrival'],review_key=r['review_key'])
                with self.assertRaisesRegex(ProjectError,'Review changed'):apply(p,{**body,'review_key':'0'*64})
                self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
                apply(p,body);self.assertEqual(len(p.undo_stack),1)
                owner=r['preview']['resource']['owner_id'];entries=p.overrides[owner]['Transitions']['entries'];changed,audit=ctx.patch(entries)
                self.assertEqual([i for i,(a,b) in enumerate(zip(man,changed)) if a!=b],[row['decoded_byte_offset'] for row in audit])
                self.assertEqual(len(audit),3)
                with self.assertRaisesRegex(ProjectError,'project or destination changed'):apply(p,body)
                after=deepcopy(p.overrides);restored=ProjectService.open(p.save());self.assertEqual(restored.overrides,after)
                p.undo();self.assertEqual(p.overrides,{})
                p.redo();self.assertEqual(p.overrides,after)
                bad={**request,'expected_project_key':project_transition_state_key(p),'expected_destination_key':source_key(p),'arrival':{'x':65}}
                with self.assertRaises(RetailImportError):review(p,**bad)
                self.assertEqual(p.overrides,after)

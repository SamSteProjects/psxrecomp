"""Current clone script preview is read-only, independent and pre-allocation."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
from importer.pipeline import import_scene
from sdk.npc_current_script import inspect
from sdk.npc_system_flags import review
from sdk.npc_branches import review as branch_review
from sdk.system_flags import review as donor_review
from sdk.project import ProjectService, ProjectError
from test_model_primitive_workflow import http_server


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class CurrentNpcScript(unittest.TestCase):
    def test_actual_source_independent_selectors_branch_composition_and_http(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN'])
            owner='scene://town01/actors/man-p1/0011';operand='script://town01/actors/man-p1/0011/system-flag/0016'
            proposal=donor_review(p,owner,operand,{'index':4095})
            p.command(dict(type='set_system_flag_selector',entity_id=owner,operand_id=operand,value={'index':4095},review_key=proposal['review_key']))
            clones=[]
            for value in [2048,None]:
                previous=set(p.actor_drafts);p.command(dict(type='create_actor_draft',donor_entity_id=owner,name=f'Preview {value}',position={'x':3008,'z':5440}))
                identity=(set(p.actor_drafts)-previous).pop();clones.append(identity)
                if value is not None:
                    request=dict(entity_id=identity,entries={operand:{'index':value}});r=review(p,request)
                    p.command(dict(type='set_actor_draft_system_flags',**request,review_key=r['review_key']))
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            authored=inspect(p,clones[0]);inherited=inspect(p,clones[1])
            original=bytes.fromhex(authored['donor']['inspection']['record']['raw_hex']);expected=bytearray(original);expected[22:24]=b'\x78\x00'
            self.assertEqual(bytes.fromhex(authored['inspection']['record']['raw_hex']),bytes(expected))
            self.assertEqual(authored['inspection']['record']['sha256'],sha256(expected).hexdigest())
            self.assertEqual(authored['changed_byte_count'],2)
            self.assertEqual(inherited['inspection'],inherited['donor']['inspection'])
            self.assertEqual(inherited['changed_byte_count'],0)
            self.assertNotEqual(authored['state_key'],inherited['state_key'])
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            context=p._branch_context(owner);options=context.options(owner);self.assertTrue(options['targets'])
            target=options['targets'][0]
            request=dict(entity_id=clones[0],entries={target['semantic_id']:{'target_pc':22}})
            r=branch_review(p,request);p.command(dict(type='set_actor_draft_branches',**request,review_key=r['review_key']))
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack));current=inspect(p,clones[0])
            self.assertEqual(current['inspection']['record']['raw_hex'][44:48],'7800')
            self.assertTrue(any(e['pc']==22 for n in current['inspection']['instructions'] if n['pc']==target['pc'] for e in n['successors']))
            self.assertTrue(all(n['byte_offset']==current['inspection']['record']['byte_offset']+n['pc'] for n in current['inspection']['instructions']))
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            restored=ProjectService.open(p.save());self.assertEqual(inspect(restored,clones[0]),current)
            with http_server(p) as (_,post):
                self.assertEqual(post('/api/npc-current-script',dict(entity_id=clones[0])),(200,current))
                self.assertEqual(post('/api/npc-current-script',dict(entity_id=clones[0],address=0x80000000))[0],400)
            if os.environ.get('LEGAIA_NPC_CURRENT_SCRIPT_EVIDENCE'):
                from sdk.project_copy import source_key
                state=p.state();state['project_copy_source_key']=source_key(p)
                root=Path(os.environ['LEGAIA_NPC_CURRENT_SCRIPT_EVIDENCE']);root.mkdir(parents=True,exist_ok=True)
                (root/'retail.json').write_text(json.dumps(dict(entity_id=clones[0],state=state,report=current)),encoding='utf-8')
            with self.assertRaises(ProjectError):inspect(p,'missing')
            p.undo();self.assertEqual(inspect(p,clones[0])['inspection'],authored['inspection'])
            p.redo();self.assertEqual(inspect(p,clones[0]),current)


if __name__=='__main__':unittest.main()

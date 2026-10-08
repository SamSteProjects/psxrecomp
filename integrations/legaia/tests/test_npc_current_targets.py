"""Literal Current movement coordinates for private viewport qualification."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from importer.pipeline import import_scene
from sdk.npc_current_script import inspect
from sdk.npc_movement import review
from sdk.project import ProjectService
from sdk.project_copy import source_key


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class CurrentTargets(unittest.TestCase):
    def test_literal_native_movement_bytes_and_read_only_source_export(self):
        with tempfile.TemporaryDirectory() as directory:
            p=ProjectService(Path(directory));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'town01'),os.environ['LEGAIA_DISC_BIN'])
            owner='scene://town01/actors/man-p1/0011'
            p.command(dict(type='create_actor_draft',donor_entity_id=owner,name='Current destination probe',position={'x':3008,'z':5440}))
            identity=next(iter(p.actor_drafts));retail=inspect(p,identity)
            request=dict(entity_id=identity,entries={'script://town01/actors/man-p1/0011/movement/0023':{'x':64,'z':16384}})
            proposed=review(p,request);p.command(dict(type='set_actor_draft_movement',**request,review_key=proposed['review_key']))
            before=deepcopy((p._document(),p.undo_stack,p.redo_stack));report=inspect(p,identity)
            expected=bytearray.fromhex(retail['inspection']['record']['raw_hex']);expected[37:39]=b'\x00\xff'
            self.assertEqual(report['inspection']['record']['raw_hex'],expected.hex())
            node=next(n for n in report['inspection']['instructions'] if n['pc']==35)
            self.assertEqual(node['operands']['target_position'],dict(x=64,y=None,z=16384))
            self.assertFalse(node['operands']['parked_target'])
            self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            self.assertEqual(p.actor_drafts[identity]['position'],dict(x=3008,z=5440))
            restored=ProjectService.open(p.save());self.assertEqual(inspect(restored,identity),report)
            if os.environ.get('LEGAIA_NPC_CURRENT_TARGET_EVIDENCE'):
                root=Path(os.environ['LEGAIA_NPC_CURRENT_TARGET_EVIDENCE']);root.mkdir(parents=True,exist_ok=True)
                from sdk.server import EditorServer
                from sdk.npc_movement import source
                from sdk.npc_system_flags import source as system_source
                from sdk.npc_waits import source as wait_source
                from sdk.npc_facing import source as facing_source
                from sdk.npc_flags import source as flags_source
                from sdk.npc_branches import source as branches_source
                from sdk.npc_dialogue import source as dialogue_source
                from sdk.npc_model_selectors import source as model_source
                server=EditorServer(('127.0.0.1',0),p,runtime_port=65533)
                try:state=server.state()
                finally:server.server_close()
                (root/'retail.json').write_text(json.dumps(dict(entity_id=identity,state=state,report=report,movement=source(p,identity),system_flags=system_source(p,identity),waits=wait_source(p,identity),facing=facing_source(p,identity),flags=flags_source(p,identity),branches=branches_source(p,identity),dialogue=dialogue_source(p,identity),model_selectors=model_source(p,identity))),encoding='utf-8')


if __name__=='__main__':unittest.main()

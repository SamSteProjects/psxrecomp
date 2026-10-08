"""Independent clone arrival bytes, reviewed persistence and saved native spans."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

from importer.pipeline import import_scene
from importer.core import ImportError as NativeError
from sdk.project import ProjectService, ProjectError
from sdk.npc_transitions import source,review
from sdk.npc_current_script import inspect
from test_model_primitive_workflow import http_server

OWNER='scene://map02/actors/man-p1/0002'
TARGET='script://map02/actors/man-p1/0002/transition/0035'


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'Private Retail disc required')
class NpcTransitionWorkflow(unittest.TestCase):
    def project(self,root):
        p=ProjectService(Path(root));p.import_metadata(import_scene(os.environ['LEGAIA_DISC_BIN'],'map02'),os.environ['LEGAIA_DISC_BIN'])
        p.command(dict(type='create_actor_draft',donor_entity_id=OWNER,name='Arrival probe',position=dict(x=128,z=256)))
        return p,next(iter(p.actor_drafts))

    def test_review_literal_current_history_persistence_clear_and_capture_refusal(self):
        with tempfile.TemporaryDirectory() as raw:
            p,identity=self.project(raw);before=deepcopy((p._document(),p.undo_stack,p.redo_stack));imports=deepcopy(p.imports)
            retail=inspect(p,identity);request=dict(entity_id=identity,entries={TARGET:dict(entry_x_encoded=0,entry_z_encoded=255,direction_encoded=7)})
            report=review(p,request);self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            expected=bytearray.fromhex(retail['inspection']['record']['raw_hex']);self.assertEqual(expected[62:65],bytes([31,30,0]));expected[62:65]=bytes([0,255,7])
            self.assertEqual(report['inspection']['record']['raw_hex'],expected.hex())
            p.command(dict(type='set_actor_draft_transitions',**request,review_key=report['review_key']))
            self.assertEqual(inspect(p,identity)['inspection']['record']['raw_hex'],expected.hex())
            after=deepcopy((p._document(),p.undo_stack));p.undo();self.assertEqual(p._document(),before[0]);p.redo();self.assertEqual((p._document(),p.undo_stack),after)
            self.assertEqual(ProjectService.open(p.save())._document(),after[0])
            self.assertEqual(source(p,identity)['options']['transitions'][0]['effective_values'],request['entries'][TARGET])
            with self.assertRaisesRegex(ProjectError,'capture cannot omit'):
                p.command(dict(type='create_npc_preset',entity_id=identity,name='Must retain arrivals'))
            clear=dict(entity_id=identity,entries={});proposal=review(p,clear)
            p.command(dict(type='set_actor_draft_transitions',**clear,review_key=proposal['review_key']))
            self.assertEqual(inspect(p,identity)['inspection'],retail['inspection']);self.assertEqual(p.imports,imports)

    def test_typed_http_live_stale_and_foreign_fields_are_atomic(self):
        with tempfile.TemporaryDirectory() as raw:
            p,identity=self.project(raw);before=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            request=dict(entity_id=identity,entries={TARGET:dict(direction_encoded=7)})
            for values in [dict(direction_encoded=True),dict(entry_x_encoded=-1),dict(entry_z_encoded=256),dict(destination='town01'),dict(direction_encoded=1.5),{}]:
                with self.assertRaises((ProjectError,NativeError)):review(p,dict(request,entries={TARGET:values}))
            proposal=review(p,request)
            with self.assertRaises(ProjectError):p.command(dict(type='set_actor_draft_transitions',**request,review_key='0'*64))
            with http_server(p) as (server,post):
                server.RequestHandlerClass.log_message=lambda *args:None
                self.assertEqual(post('/api/npc-transitions-source',dict(entity_id=identity))[0],200)
                self.assertEqual(post('/api/npc-transitions-source',dict(entity_id=identity,path='foreign'))[0],400)
                self.assertEqual(post('/api/npc-transitions-review',dict(request,entries={TARGET:dict(direction_encoded=True)}))[0],400)
                self.assertEqual(post('/api/npc-transitions-review',request)[0],200)
            p.mode='live'
            with self.assertRaises(ProjectError):source(p,identity)
            p.mode='edit';self.assertEqual(before,(p._document(),p.undo_stack,p.redo_stack))
            p.command(dict(type='rename_actor_draft',entity_id=identity,name='Changed after Review'))
            changed=deepcopy((p._document(),p.undo_stack,p.redo_stack))
            with self.assertRaises(ProjectError):p.command(dict(type='set_actor_draft_transitions',**request,review_key=proposal['review_key']))
            self.assertEqual(changed,(p._document(),p.undo_stack,p.redo_stack))


class NativeTransitionComparison(unittest.TestCase):
    def test_native_spans_require_exact_source_fields_and_owner(self):
        from test_npc_transitions import NpcTransitionTests
        from sdk.npc_transitions import patch_allocated_transitions
        from importer.man_layout import read_man_layout
        from sdk.npc_script_compare import authored_spans
        c,base,allocations,target=NpcTransitionTests().fixture(True)
        values=dict(entry_x_encoded=0,entry_z_encoded=255,direction_encoded=7)
        result,audit=patch_allocated_transitions(c,base,allocations,[dict(draft_id='npc-a',donor_entity_id=target['owner_id'],entries={target['semantic_id']:values})])
        at,record,entry=c._source.verified_record(target['owner_id']);final=next(r for r in read_man_layout(result)['records'] if r['partition']==1 and r['record_index']==allocations['drafts'][0]['record_index'])
        metadata=dict(npc_transitions_changes=audit)
        retail=dict(raw_hex=record.hex(),script_offset=entry,byte_length=len(record),byte_offset=at)
        generated=dict(raw_hex=result[final['byte_offset']:final['byte_offset']+final['byte_length']].hex(),script_offset=entry,byte_length=final['byte_length'],byte_offset=final['byte_offset'],record_index=final['record_index'])
        draft=dict(donor_entity_id=target['owner_id'],transitions=dict(donor_entity_id=target['owner_id'],entries={target['semantic_id']:values}))
        spans=authored_spans(metadata,'npc-a',retail,generated,draft);self.assertEqual(len(spans),3);self.assertTrue(all(r['category']=='own_transition' for r in spans))
        for change in [dict(field='direction_encoded'),dict(after_byte=17),dict(pc=0),dict(transition_id='foreign'),dict(byte_length=2)]:
            bad=deepcopy(metadata);bad['npc_transitions_changes']['changes'][0].update(change)
            with self.assertRaises(ProjectError):authored_spans(bad,'npc-a',retail,generated,draft)


if __name__=='__main__':unittest.main()

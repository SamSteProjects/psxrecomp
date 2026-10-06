"""Retail-qualified audio commands, metadata lifecycle and API guards."""
from copy import deepcopy
from pathlib import Path
import json
import os
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from importer.pipeline import import_scene
from importer.audio_catalog import load_audio_asset_catalog
from importer.core import ImportError
from sdk.project import ProjectService, ProjectError
from sdk.build import authored_state_key, build_report, package_change_kinds
from sdk.audio_authoring import options, review, read, source_key, validate_collection
from sdk.scene_preview import source_key as resource_key
from sdk.project_copy import review as copy_review, create_copy
from sdk.server import EditorServer


class AudioReports(unittest.TestCase):
    def test_build_reports_describe_encoded_values_and_native_span(self):
        event=dict(scene='global-audio',semantic_id='audio://legaia/prot/0877',
                   scope='audio-SEQ-fixed-operands-only',field='audio.sequence.note_on',
                   before_value=[60,100],after_value=[61,0],event_offset=15,
                   entry_byte_offset=99,byte_length=2)
        audit=dict(edits=[event],validation={},overlays=[dict(size=2048)])
        report=build_report(audit)
        self.assertEqual(report['changes'][0]['before'],[60,100])
        self.assertEqual(report['changes'][0]['after'],[61,0])
        self.assertEqual(report['changes'][0]['event_offset'],15)
        self.assertEqual(report['changes'][0]['entry_byte_offset'],99)
        self.assertEqual(package_change_kinds([event]),['native audio sequence operands'])
        report['changes'][0]['after'][0]=99
        self.assertEqual(event['after_value'],[61,0])


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class AudioCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.disc=os.environ['LEGAIA_DISC_BIN']
        cls.metadata=import_scene(cls.disc,'town01')
        cls.rows={r['semantic_id']:r for r in load_audio_asset_catalog(cls.disc,'town01')['assets']}

    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.project=ProjectService(Path(self.directory.name),'Audio operands')
        self.project.import_metadata(deepcopy(self.metadata),self.disc)
        self.project.save()
        self.identifier='audio://legaia/prot/0877'
        self.entry_hash=self.rows[self.identifier]['source_record']['sha256']

    def tearDown(self):
        self.directory.cleanup()

    def inspect(self):
        return options(self.project,self.identifier,self.entry_hash,resource_key(self.project))

    def change(self, edits):
        value=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,
                   expected_authoring_key=source_key(self.project),edits=edits)
        result=review(self.project,**value)
        self.project.command(dict(type='set_audio_sequence_operands',review_key=result['review_key'],**value))
        return result

    def first_edit(self):
        event=next(e for e in self.inspect()['current']['events'] if e['channel'] is not None)
        return event,dict(event_offset=event['offset'],values=[(v+1)%128 for v in event['values']])

    def test_review_apply_noop_history_save_open_copy_and_retail_restore(self):
        event,edit=self.first_edit();initial=deepcopy(self.project._document())
        build_key=authored_state_key(self.project)
        arguments=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,
                       expected_authoring_key=source_key(self.project),edits=[edit])
        proposed=review(self.project,**arguments)
        self.assertEqual(self.project._document(),initial)
        self.assertEqual(len(self.project.undo_stack),0)
        self.project.command(dict(type='set_audio_sequence_operands',review_key=proposed['review_key'],**arguments))
        self.assertNotEqual(authored_state_key(self.project),build_key)
        self.assertIn('Audio sequence operands',self.project.unsaved_sections)
        self.assertEqual(self.project.imports[self.project.active_scene],self.metadata)
        self.assertEqual(len(self.project.undo_stack),1)
        body,current,_,_=read(self.project,self.identifier,self.project.audio_overrides[self.identifier])
        self.assertNotEqual(body,current)
        self.assertTrue(self.change([edit])['no_change'])
        self.assertEqual(len(self.project.undo_stack),1)
        authored=deepcopy(self.project._document())
        self.project.undo();self.assertEqual(self.project._document(),initial)
        self.project.redo();self.assertEqual(self.project._document(),authored)
        self.project.save();self.assertFalse(self.project.dirty)
        opened=ProjectService.open(self.project.root)
        self.assertEqual(opened.audio_overrides,self.project.audio_overrides)
        validate_collection(opened)
        copy_info=copy_review(self.project)
        copied=create_copy(self.project,'Audio copy',copy_info['review_key'])
        copy_project=ProjectService.open(Path(copied['copied_project']))
        self.assertEqual(copy_project.audio_overrides,self.project.audio_overrides)
        self.assertEqual(len(copy_project.undo_stack),0)
        self.change([dict(event_offset=event['offset'],values=event['values'])])
        self.assertEqual(self.project.audio_overrides,{})
        self.assertEqual(authored_state_key(self.project),build_key)

    def test_stale_review_invalid_values_clear_and_malformed_open(self):
        event,edit=self.first_edit()
        value=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,
                   expected_authoring_key=source_key(self.project),edits=[edit])
        result=review(self.project,**value)
        for invalid in ([dict(event_offset=event['offset'],values=[128]*len(event['values']))], [edit,edit]):
            with self.assertRaises(ImportError):review(self.project,**{**value,'edits':invalid})
        self.assertEqual(self.project.audio_overrides,{})
        with self.assertRaises(ProjectError):self.project.command(dict(type='set_audio_sequence_operands',review_key='f'*64,**value))
        self.change([edit]);before=deepcopy(self.project._document())
        with self.assertRaises(ProjectError):self.project.command(dict(type='set_audio_sequence_operands',review_key=result['review_key'],**value))
        self.assertEqual(self.project._document(),before)
        clear=dict(type='clear_audio_sequence_operands',asset_id=self.identifier,
                   expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project))
        with self.assertRaises(ProjectError):self.project.command(dict(**clear,other=1))
        self.project.command(clear);self.assertEqual(self.project.audio_overrides,{})
        self.project.undo();self.assertEqual(self.project._document(),before)
        path=self.project.save();document=json.loads(path.read_text(encoding='utf-8'))
        document['audio_overrides'][self.identifier]['source_record']['sequence_offset']+=4
        path.write_text(json.dumps(document),encoding='utf-8')
        with self.assertRaises(ProjectError):ProjectService.open(path)

    def test_partial_sequence_current_retains_unknown_tail_and_boundary(self):
        self.identifier='audio://legaia/prot/1045'
        self.entry_hash=self.rows[self.identifier]['source_record']['sha256']
        source=self.inspect();self.assertFalse(source['retail']['complete'])
        _,edit=self.first_edit();self.change([edit])
        after=self.inspect()
        self.assertEqual(after['current']['stop_offset'],source['retail']['stop_offset'])
        self.assertEqual(after['current']['stop_reason'],source['retail']['stop_reason'])
        body,current,record,_=read(self.project,self.identifier,self.project.audio_overrides[self.identifier])
        first=record['sequence_offset']+source['retail']['decoded_byte_end']
        self.assertEqual(body[first:],current[first:])
        before=deepcopy(self.project._document())
        with self.assertRaises(ImportError):self.change([dict(event_offset=source['retail']['stop_offset'],values=[1,2])])
        self.assertEqual(self.project._document(),before)

    def test_exact_http_fields_review_and_command(self):
        server=EditorServer(('127.0.0.1',0),self.project)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        def post(route,body):
            req=Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with urlopen(req,timeout=30) as response:return json.load(response)
        try:
            query=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_source_key=resource_key(self.project))
            inspected=post('/api/audio-sequence-authoring',query)
            with self.assertRaises(HTTPError) as error:post('/api/audio-sequence-authoring',dict(**query,extra=1))
            self.assertEqual(error.exception.code,400)
            error.exception.close()
            event=next(e for e in inspected['current']['events'] if e['channel'] is not None)
            proposal=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=inspected['authoring_key'],
                          edits=[dict(event_offset=event['offset'],values=[(v+1)%128 for v in event['values']])])
            result=post('/api/audio-sequence-review',proposal)
            self.assertFalse(self.project.audio_overrides)
            applied=post('/api/command',dict(type='set_audio_sequence_operands',review_key=result['review_key'],**proposal))
            self.assertIn(self.identifier,applied['audio_overrides'])
            with self.assertRaises(HTTPError) as stale:post('/api/command',dict(type='set_audio_sequence_operands',review_key=result['review_key'],**proposal))
            stale.exception.close()
            self.assertEqual(len(self.project.undo_stack),1)
        finally:
            server.shutdown();server.server_close();worker.join(5)


if __name__=='__main__':unittest.main()

"""Bank command persistence and independently encoded shared bank/SEQ delivery."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json,os,threading,unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from unittest.mock import patch
import test_audio_authoring as sequence_tests
from test_audio_bank_authoring import edits_and_expected
from importer.audio_bank import bank_from_entry
from importer.pipeline import _disc_context
from sdk.project import ProjectService,ProjectError
from sdk.audio_authoring import source_key,options as sequence_options,review as sequence_review
from sdk.audio_bank_authoring import options,review,read,validate_collection
from sdk.audio_composition import read_entry,merge,prepare_overlays
from sdk.scene_preview import source_key as resource_key
from sdk.build import authored_state_key,build_report,package_change_kinds
from sdk.project_copy import review as copy_review,create_copy
from sdk.server import EditorServer,EditorHandler

def digest(body):return sha256(body).hexdigest()

class Composition(unittest.TestCase):
    def test_exact_audits_and_overlapping_bytes(self):
        body=b'abcd'
        def row(candidate):return ('family',candidate,dict(source_entry_sha256=digest(body),before_entry_sha256=digest(body),after_entry_sha256=digest(candidate),changed_entry_byte_offsets=[i for i,(a,b) in enumerate(zip(body,candidate)) if a!=b]))
        self.assertEqual(merge(body,[row(b'Abcd'),row(b'abcD')]),b'AbcD')
        with self.assertRaises(ProjectError):merge(body,[row(b'Abcd'),row(b'Zbcd')])
        bad=row(b'Abcd');bad[2]['changed_entry_byte_offsets']=[]
        with self.assertRaises(ProjectError):merge(body,[bad])
        bad=row(b'Abcd');bad[2]['before_entry_sha256']='f'*64
        with self.assertRaises(ProjectError):merge(body,[bad])

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class BankWorkflow(unittest.TestCase):
    setUpClass=classmethod(sequence_tests.AudioCommands.setUpClass.__func__)
    setUp=sequence_tests.AudioCommands.setUp
    tearDown=sequence_tests.AudioCommands.tearDown
    inspect=sequence_tests.AudioCommands.inspect
    change=sequence_tests.AudioCommands.change
    first_edit=sequence_tests.AudioCommands.first_edit

    def bank_options(self):return options(self.project,self.identifier,self.entry_hash,resource_key(self.project))
    def bank_change(self,edits):
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),edits=edits)
        report=review(self.project,**args)
        self.project.command(dict(type='set_audio_bank_parameters',review_key=report['review_key'],**args))
        return report
    def bank_edit(self):
        row=self.bank_options()['retail']['parameters'][0]
        return dict(section=row['section'],field=row['field'],value=(row['value']+1)%256)
    def clear(self,family):
        self.project.command(dict(type='clear_audio_'+family,asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project)))

    def test_persistence_history_copy_noop_and_independent_clear(self):
        original=deepcopy(self.project._document());key=authored_state_key(self.project)
        self.assertNotIn('audio_bank_overrides',original)
        _,seqedit=self.first_edit();edit=self.bank_edit()
        self.bank_change([edit]);bank_current=read_entry(self.project,self.identifier)
        self.assertIn('Audio bank parameters',self.project.unsaved_sections)
        self.assertTrue(self.inspect()['bank_authored'])
        self.assertEqual(self.inspect()['current_entry_sha256'],digest(bank_current))
        self.assertNotEqual(authored_state_key(self.project),key)
        self.assertTrue(self.bank_change([edit])['no_change']);self.assertEqual(len(self.project.undo_stack),1)
        self.change([seqedit]);both=read_entry(self.project,self.identifier)
        authored=[row for row in self.project.authored_assets() if row['id']==self.identifier]
        self.assertEqual(len(authored),1);self.assertEqual(len(authored[0]['changes']),2)
        self.assertTrue(self.bank_options()['sequence_authored'])
        self.assertEqual(self.bank_options()['current_entry_sha256'],digest(both))
        self.project.save();self.assertFalse(self.project.dirty)
        opened=ProjectService.open(self.project.root);self.assertEqual(read_entry(opened,self.identifier),both)
        info=copy_review(self.project);copied=create_copy(self.project,'Bank copy',info['review_key'])
        clone=ProjectService.open(Path(copied['copied_project']));self.assertEqual(read_entry(clone,self.identifier),both)
        self.clear('sequence_operands');self.assertEqual(read_entry(self.project,self.identifier),bank_current)
        self.project.undo();self.assertEqual(read_entry(self.project,self.identifier),both)
        self.clear('bank_parameters');self.assertFalse(self.inspect()['bank_authored'])
        seq_current=read_entry(self.project,self.identifier);self.assertNotEqual(seq_current,both)
        self.project.undo();self.assertEqual(read_entry(self.project,self.identifier),both)
        self.project.redo();self.assertEqual(read_entry(self.project,self.identifier),seq_current)
        self.clear('sequence_operands');self.assertEqual(self.project._document(),original)
        self.assertEqual(authored_state_key(self.project),key)

    def test_27_parameters_and_sequence_share_one_independent_native_entry(self):
        self.bank_change([self.bank_edit()])
        body,_,record,_=read(self.project,self.identifier,self.project.audio_bank_overrides[self.identifier])
        self.clear('bank_parameters');bank,pieces,_=bank_from_entry(body)
        edits,expected_bank,_=edits_and_expected(bank)
        self.bank_change(edits);_,seqedit=self.first_edit();self.change([seqedit])
        expected=bytearray(body)
        for piece in pieces:
            at=piece['entry_offset'];start=piece['bank_offset'];size=piece['size_bytes']
            expected[at:at+size]=expected_bank[start:start+size]
        seq=sequence_options(self.project,self.identifier,self.entry_hash,resource_key(self.project))
        event=next(e for e in seq['retail']['events'] if e['offset']==seqedit['event_offset'])
        operand=seq['source_record']['sequence_offset']+event['end_offset']-len(event['values'])
        expected[operand:operand+len(seqedit['values'])]=bytes(seqedit['values'])
        self.assertEqual(read_entry(self.project,self.identifier),bytes(expected))
        with _disc_context(self.disc) as (image,_,_,archive):overlays,changes=prepare_overlays(self.project,image,archive)
        self.assertEqual(len(overlays),1);self.assertEqual(overlays[0]['payload'],bytes(expected))
        self.assertEqual(overlays[0]['source_kind'],'raw_PROT_audio_operands')
        self.assertEqual(len(changes),28)
        self.assertTrue(all(c['candidate_entry_sha256']==digest(expected) for c in changes))
        report=build_report(dict(edits=changes,validation={},overlays=overlays))
        self.assertEqual(report['change_count'],28)
        self.assertIn('bank_byte_offset',next(c for c in report['changes'] if c['scope']=='audio-VAB-fixed-parameters-only'))
        self.assertEqual(package_change_kinds(changes),['native audio bank parameters','native audio sequence operands'])

    def test_cross_family_stale_reviews_and_restoring_retail_parameter(self):
        edit=self.bank_edit();args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=source_key(self.project),edits=[edit])
        proposal=review(self.project,**args);_,seqedit=self.first_edit();self.change([seqedit])
        current=read_entry(self.project,self.identifier);document=deepcopy(self.project._document())
        with self.assertRaises(ProjectError):self.project.command(dict(type='set_audio_bank_parameters',review_key=proposal['review_key'],**args))
        self.assertEqual(self.project._document(),document)
        seqargs={**args,'expected_authoring_key':source_key(self.project),'edits':[seqedit]};seqproposal=sequence_review(self.project,**seqargs)
        retail=self.bank_options()['retail']['parameters'][0]['value'];self.bank_change([edit])
        with self.assertRaises(ProjectError):self.project.command(dict(type='set_audio_sequence_operands',review_key=seqproposal['review_key'],**seqargs))
        self.bank_change([{**edit,'value':retail}]);self.assertEqual(self.project.audio_bank_overrides,{})
        self.assertEqual(read_entry(self.project,self.identifier),current)

    def test_malformed_source_binding_fails_save_and_open(self):
        self.bank_change([self.bank_edit()]);path=self.project.save()
        self.project.audio_bank_overrides[self.identifier]['source_record']['pieces'][0]['entry_offset']+=1
        with self.assertRaises(ProjectError):self.project.save()
        document=json.loads(path.read_text(encoding='utf-8'));document['audio_bank_overrides'][self.identifier]['extra']=1
        path.write_text(json.dumps(document),encoding='utf-8')
        with self.assertRaises(ProjectError):ProjectService.open(path)

    def test_http_exact_fields_source_review_apply_and_stale_rejection(self):
        server=EditorServer(('127.0.0.1',0),self.project);thread=threading.Thread(target=server.serve_forever,daemon=True)
        def post(route,body):
            req=Request(f'http://127.0.0.1:{server.server_port}'+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with urlopen(req,timeout=30) as response:return json.load(response)
        with patch.object(EditorHandler,'log_message',lambda *args:None):
            thread.start()
            try:
                query=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_source_key=resource_key(self.project))
                value=post('/api/audio-bank-authoring',query)
                with self.assertRaises(HTTPError) as rejected:post('/api/audio-bank-authoring',{**query,'extra':1})
                rejected.exception.close()
                args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=value['authoring_key'],edits=[self.bank_edit()])
                proposal=post('/api/audio-bank-review',args);self.assertFalse(self.project.dirty)
                post('/api/command',dict(type='set_audio_bank_parameters',review_key=proposal['review_key'],**args))
                with self.assertRaises(HTTPError) as rejected:post('/api/audio-bank-review',args)
                rejected.exception.close()
                self.assertEqual(len(self.project.undo_stack),1)
            finally:server.shutdown();server.server_close();thread.join(timeout=10)

if __name__=='__main__':unittest.main()

import base64,os,unittest
from copy import deepcopy
from test_audio_midi_sources import MidiSources
from sdk.midi_input_assets import inventory,inspect,PREFIX
from sdk.project_assets import assemble,source_key
from sdk.project import ProjectError

@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'),'Retail disc not configured')
class MidiAssets(unittest.TestCase):
    setUpClass=classmethod(MidiSources.setUpClass.__func__)
    setUp=MidiSources.setUp
    tearDown=MidiSources.tearDown
    inspect=MidiSources.inspect
    retain=MidiSources.retain

    def test_inventory_shared_content_and_project_asset_membership(self):
        raw,_=self.retain();r=next(iter(self.project.audio_midi_sources.values()))
        before=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
        snapshot=inventory(self.project);identifier=PREFIX+r['midi_sha256']
        self.assertEqual(list(snapshot['assets']),[identifier]);self.assertEqual(snapshot['records_by_scene'][r['source_scene_id']],[snapshot['assets'][identifier]])
        report=assemble(self.project,{});asset=next(a for a in report['assets'] if a['id']==identifier)
        self.assertEqual(asset['scene_ids'],[r['source_scene_id']]);self.assertEqual(asset['variants'][0]['record'],snapshot['assets'][identifier])
        value=inspect(self.project,identifier,source_key(self.project),include_midi=True)
        self.assertEqual(base64.b64decode(value['midi_base64']),raw);self.assertEqual(value['current_binding'],'not_asserted');self.assertFalse(value['gameplay_verified'])
        self.assertEqual(before,(self.project._document(),self.project.undo_stack,self.project.redo_stack))

    def test_current_content_match_changes_only_with_native_sequence(self):
        from sdk.audio_authoring import review,source_key as native_key,_current,_layout
        from hashlib import sha256
        raw,_=self.retain();receipt=deepcopy(next(iter(self.project.audio_midi_sources.values())))
        identifier=PREFIX+receipt['midi_sha256']
        def check(expected):
            before=deepcopy((self.project._document(),self.project.undo_stack,self.project.redo_stack))
            value=inspect(self.project,identifier,source_key(self.project),include_midi=True)
            self.assertEqual(value['schema_version'],'legaia.midi-input-inspection.v2')
            row=value['current_comparisons'][0];body,current,_,record,_=_current(self.project,self.identifier,self.entry_hash)
            start,size=_layout(body,current,record)
            self.assertEqual(row['current_entry_sha256'],sha256(current).hexdigest())
            self.assertEqual(row['current_sequence_sha256'],sha256(current[start:start+size]).hexdigest())
            self.assertEqual((row['current_sequence_offset'],row['sequence_size_bytes']),(start,size))
            self.assertEqual(row['matches_candidate'],expected);self.assertEqual(row['input_usage'],'not_asserted')
            self.assertEqual(base64.b64decode(value['midi_base64']),raw)
            self.assertEqual(before,(self.project._document(),self.project.undo_stack,self.project.redo_stack))
            self.assertEqual(next(iter(self.project.audio_midi_sources.values())),receipt)
        check(False)
        args=dict(asset_id=self.identifier,expected_entry_sha256=self.entry_hash,expected_authoring_key=native_key(self.project),edits=receipt['edits'])
        result=review(self.project,**args)
        self.project.command(dict(type='set_audio_sequence_operands',review_key=result['review_key'],**args))
        check(True);self.project.undo();check(False);self.project.redo();check(True)
        from sdk.project import ProjectService
        self.project.save();self.project=ProjectService.open(self.project.root);check(True)
        from test_audio_native_allocation import NativeAllocation
        sample,_=NativeAllocation.retain(self);NativeAllocation.apply(self,sample)
        check(True)
        row=inspect(self.project,identifier,source_key(self.project))['current_comparisons'][0]
        self.assertNotEqual(row['current_sequence_offset'],receipt['source_record']['sequence_offset'])
        self.project.undo();check(True);self.project.redo();check(True)
        self.project.save();self.project=ProjectService.open(self.project.root);check(True)

    def test_stale_unknown_removed_and_changed_content_refuse(self):
        raw,_=self.retain();r=next(iter(self.project.audio_midi_sources.values()));identifier=PREFIX+r['midi_sha256']
        with self.assertRaises(ProjectError):inspect(self.project,identifier,'f'*64)
        with self.assertRaises(ProjectError):inspect(self.project,PREFIX+'f'*64,source_key(self.project))
        path=self.project.root/'Authored/Audio/MidiSources'/(r['midi_sha256']+'.mid');path.write_bytes(bytes([raw[0]^1])+raw[1:])
        try:
            with self.assertRaises(ProjectError):inventory(self.project)
        finally:path.write_bytes(raw)
        self.project.audio_midi_sources={}
        self.assertEqual(inventory(self.project)['assets'],{})
        with self.assertRaises(ProjectError):inspect(self.project,identifier,source_key(self.project))

if __name__=='__main__':unittest.main()

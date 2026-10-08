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

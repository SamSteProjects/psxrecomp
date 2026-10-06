import struct,unittest
from hashlib import sha256
from importer.core import ImportError
from importer.effect_color_authoring import EffectColorAuthoringContext,patch_effect_color_target
from importer.man_actor_structure import append_actor_donor
from sdk.effect_colors import merge_patch
from sdk.build import BuildError,build_report,package_change_kinds
from test_importer_dialogue_authoring import fixture,ACTOR

END=b'\x3f\0\0\x06town01\1\2\3opaque'
VALUES=dict(red=12,green=34,blue=56,intensity=-1234)
class EffectColorAuthoring(unittest.TestCase):
    def test_fixed_span_normal_extended_selector_and_signed_boundaries(self):
        for header in (b'\x34',b'\xb4\x07'):
            record=header+b'\x0f'+struct.pack('<BBBh',12,34,56,-1234)+END
            self.assertEqual(patch_effect_color_target(record,0,0,VALUES),(record,[]))
            for intensity in (-32768,0,32767):
                values=dict(red=255,green=0,blue=1,intensity=intensity);after,audit=patch_effect_color_target(record,0,0,values,base_offset=100)
                at=len(header)+1;self.assertEqual(after[:at],record[:at]);self.assertEqual(after[at+5:],END);self.assertEqual(after[at:at+5],struct.pack('<BBBh',255,0,1,intensity));self.assertEqual(audit[0]['decoded_byte_offset'],100+at)
        for values in ({},dict(VALUES,red=True),dict(VALUES,green=-1),dict(VALUES,blue=256),dict(VALUES,intensity=32768),dict(VALUES,intensity=-32769),dict(VALUES,extra=1)):
            with self.assertRaises(ImportError):patch_effect_color_target(record,0,0,values)
        for bad,pc in ((b'\x34\0\1',0),(b'\x2a'+record,1),(b'\x34\0'+struct.pack('<BBBh',1,2,3,4)+b'\xff',0)):
            with self.assertRaises(ImportError):patch_effect_color_target(bad,0,pc,VALUES)
    def test_source_context_appended_rebase_and_composition_audit(self):
        source,man=fixture(b'\x34\x0a'+struct.pack('<BBBh',1,2,3,4)+END);context=EffectColorAuthoringContext(source);target=context.options(ACTOR)['targets'][0];key=target['semantic_id'];request={key:VALUES}
        after,audit=context.patch(request);at=target['decoded_byte_offset'];self.assertEqual({i for i,(a,b) in enumerate(zip(man,after)) if a!=b},set(range(at,at+5)));self.assertEqual(context._man,man)
        expected={key:dict(target,requested_values=VALUES)};self.assertEqual(merge_patch(man,man,after,audit,expected,[]),after)
        row=dict(audit[0],scene='fixture',semantic_id=ACTOR,scope='script-effect-color-operands-only');report=build_report(dict(edits=[row],validation={},overlays=[]));self.assertEqual(report['changes'][0]['asset_id'],key);self.assertEqual(report['changes'][0]['after'],VALUES);self.assertEqual(package_change_kinds([row]),['script effect colors'])
        for changes,prior in (([dict(audit[0],byte_length=4)],[]),(audit,[dict(decoded_byte_offset=at,byte_length=1)])):
            with self.assertRaises(BuildError):merge_patch(man,man,after,changes,expected,prior)
        bad=bytearray(after);bad[-1]^=1
        with self.assertRaises(BuildError):merge_patch(man,man,bytes(bad),audit,expected,[])
        appended,_=append_actor_donor(man,sha256(man).hexdigest(),1);rebased,changes=context.patch_appended(appended,request);self.assertEqual(changes[0]['decoded_byte_offset'],at+3);self.assertEqual(rebased[at+3:at+8],struct.pack('<BBBh',12,34,56,-1234))
        with self.assertRaises(ImportError):context.patch_appended(rebased,request)

if __name__=='__main__':unittest.main()

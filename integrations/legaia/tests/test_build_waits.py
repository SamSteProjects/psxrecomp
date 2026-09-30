"""Flag composition independently checks source operands and exact audit spans."""
from copy import deepcopy
import unittest
from importer.wait_authoring import WaitAuthoringContext
from test_importer_dialogue_authoring import fixture, ACTOR
from sdk.build import _merge_wait_patch, build_report, package_change_kinds, BuildError

class WaitBuildTests(unittest.TestCase):
    def test_verified_span_composes_and_report_exposes_bit_identity(self):
        source,man=fixture(b'\x4a\x02\0\x3f\0\0\x06town01\1\2\3opaque')
        context=WaitAuthoringContext(source);target=context.options(ACTOR)['targets'][0]
        key=target['semantic_id'];values={'duration_ticks':3}
        patched,audit=context.patch({key:values})
        expected={key:dict(target,requested_values=values)}
        self.assertEqual(_merge_wait_patch(man,man,patched,audit,expected,[]),patched)
        working=bytes([man[0]^1])+man[1:]
        result=_merge_wait_patch(man,working,patched,audit,expected,[{'decoded_byte_offset':0}])
        self.assertEqual(result[0],working[0]);self.assertEqual(result[1:],patched[1:])
        wide_values={'duration_ticks':32767}
        wide,wide_audit=context.patch({key:wide_values})
        self.assertEqual(_merge_wait_patch(man,man,wide,wide_audit,{key:dict(target,requested_values=wide_values)},[]),wide)
        with self.assertRaises(BuildError):
            _merge_wait_patch(man,man,patched,audit,expected,[{'decoded_byte_offset':target['decoded_byte_offset']+1}])
        offset=audit[0]['decoded_byte_offset']
        for mutation in ('overlap','duplicate','offset','hash','duration','request','extra','length'):
            changes=deepcopy(audit);candidate=patched;targets=deepcopy(expected);previous=[]
            if mutation=='overlap':previous=[{'decoded_byte_offset':offset-1,'byte_length':2}]
            elif mutation=='duplicate':changes*=2
            elif mutation=='offset':changes[0]['decoded_byte_offset']+=1
            elif mutation=='hash':changes[0]['source_record_sha256']='stale'
            elif mutation=='duration':changes[0]['after_ticks']=4
            elif mutation=='request':targets[key]['requested_values']={'duration_ticks':4}
            elif mutation=='extra':candidate=bytes([candidate[0]^1])+candidate[1:]
            elif mutation=='length':candidate=candidate[:-1]
            with self.subTest(mutation=mutation),self.assertRaises(BuildError):
                _merge_wait_patch(man,man,candidate,changes,targets,previous)
        row=dict(audit[0],scene='fixture',semantic_id=ACTOR,scope='script-wait-target-only')
        report=build_report(dict(edits=[row],validation={},overlays=[]))
        self.assertEqual(report['changes'][0]['asset_id'],key)
        self.assertEqual(report['changes'][0]['field'],'wait.duration_ticks')
        self.assertEqual((report['changes'][0]['before'],report['changes'][0]['after']),(2,3))
        self.assertEqual(package_change_kinds([row]),['script wait targets'])

if __name__=='__main__':unittest.main()

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
from unittest import TestCase

from sdk.project import ProjectService,ProjectError
from sdk.worldmap_scripted_placement_binding import SCHEMA,owner,validate,replay,merge_current
from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from test_worldmap_scripted_placement_allocation import fixture
from test_project_workflow import synthetic_scene


def ledger():
    base,fallback,man,floor,requests=fixture()
    current,audit=allocate_scripted_placements(base,fallback,man,floor,'map01',requests,relocation_offset=0x40)
    binding=dict(schema_version=SCHEMA,scene='map01',source_disc_sha256='b'*64,
        source_map_sha256=sha256(base).hexdigest(),source_man_sha256=sha256(man).hexdigest(),
        source_floor_lut_sha256=sha256(struct.pack('<16h',*floor)).hexdigest(),
        fallback_sha256=sha256(fallback).hexdigest(),base_map_sha256=sha256(base).hexdigest(),
        operations=[dict(requests=requests,relocation_offset=0x40,proposed_map_sha256=sha256(current).hexdigest())])
    return base,fallback,man,floor,binding,current,audit


class ScriptedWorldBindingTests(TestCase):
    def test_two_operation_replay_preserves_order_and_complete_hashes(self):
        base,fallback,man,floor,binding,current,first=ledger()
        request=deepcopy(binding['operations'][0]['requests'][0])
        request.update(placement_id='placement://authored/44444444-4444-4444-8444-444444444444',
            donor_cell=200,target_cell=201,record_index=5)
        request['values']['offset']['x']=64
        expected,second=allocate_scripted_placements(current,fallback,man,floor,'map01',[request],relocation_offset=0x60)
        binding['operations'].append(dict(requests=[request],relocation_offset=0x60,proposed_map_sha256=sha256(expected).hexdigest()))
        candidate,audits=replay(base,fallback,man,floor,binding)
        self.assertEqual(candidate,expected);self.assertEqual(audits,[first,second])
        self.assertEqual(merge_current(base,candidate,base,floor,'map01',audits),candidate)
        for key in ('base_map_sha256','fallback_sha256'):
            altered=deepcopy(binding);altered[key]='0'*64
            with self.subTest(key=key),self.assertRaises(ProjectError):replay(base,fallback,man,floor,altered)
        altered=deepcopy(binding);altered['operations'][0]['proposed_map_sha256']='0'*64
        with self.assertRaises(ProjectError):replay(base,fallback,man,floor,altered)

    def test_unrelated_current_edits_merge_without_changing_created_bytes(self):
        base,fallback,man,floor,binding,allocated,_=ledger();_,audits=replay(base,fallback,man,floor,binding)
        current=bytearray(base);current[0x4000+200]=0x43
        # Existing donor transform can change without moving the retained clone.
        struct.pack_into('<h',current,9*32,32)
        actual=merge_current(base,allocated,bytes(current),floor,'map01',audits)
        expected=bytearray(allocated);expected[0x4000+200]=0x43;struct.pack_into('<h',expected,9*32,32)
        self.assertEqual(actual,bytes(expected))
        self.assertEqual(actual[4*32:5*32],allocated[4*32:5*32])
        for offset in (4*32,0x8000+200*2,0x10020,0x10040):
            altered=bytearray(base);altered[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(ProjectError):
                merge_current(base,allocated,bytes(altered),floor,'map01',audits)

    def test_exact_schema_disc_identity_and_reused_native_owners_refuse(self):
        *_,binding,_,_=ledger()
        with tempfile.TemporaryDirectory() as root:
            project=ProjectService(Path(root));document=synthetic_scene();document['source']['disc_identity']='sha256:'+'b'*64
            project.import_metadata(document)
            self.assertEqual(validate(project,owner('map01'),binding),binding)
            for case in ('disc','extra','shared','uuid','record','offset','duplicate'):
                altered=deepcopy(binding);operation=altered['operations'][0];request=operation['requests'][0]
                if case=='disc':altered['source_disc_sha256']='c'*64
                if case=='extra':altered['extra']=0
                if case=='shared':request['shared_script']=1
                if case=='uuid':request['placement_id']='foreign'
                if case=='record':request['record_index']=True
                if case=='offset':operation['relocation_offset']=True
                if case=='duplicate':altered['operations'].append(deepcopy(operation))
                with self.subTest(case=case),self.assertRaises(ProjectError):validate(project,owner('map01'),altered)

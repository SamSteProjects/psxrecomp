"""Fixed-span NPC candidate guards and optional private normal-package readback."""
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import struct
import tempfile
import json
import tomllib
import zipfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from importer.core import decompress_lzs, parse_scene_table
from sdk.build import authored_state_key
from sdk.npc_build import prepare_npc_overlays
from sdk.project import ProjectError


def fixture(candidate=b'a' * 130):
    original = b'a' * 100
    stream = b''.join(b'\xff' + original[i:i + 8] for i in range(0, 100, 8))
    header = bytearray(56)
    struct.pack_into('<I', header, 0, 6)
    offset = 56
    payload = stream
    for i in range(6):
        struct.pack_into('<II', header, 8 + i * 8,
                         ((3 if i == 0 else 1) << 24) | (100 if i == 0 else 3), offset)
        offset += len(stream) if i == 0 else 3
        if i:
            payload += bytes([i]) * 3
    container = (bytes(header) + payload).ljust(2048, b'\x77')
    prot = bytes(2048) + container
    entries = [SimpleNamespace(index=i, start_lba=i + 1) for i in range(2)]
    archive = SimpleNamespace(node=SimpleNamespace(size=len(prot), extent_lba=20), SECTOR=2048,
        entries=entries, entry=lambda i: entries[i],
        image=SimpleNamespace(read_user=lambda lba, offset, length, size: prot[offset:offset + length]))
    project = SimpleNamespace(mode='edit', name='fixture', root=Path('/fixture'), disc_path='disc',
        imports={'scene://fixture': {'scene': {'name': 'fixture'}, 'actors': [],
                                    'source': {'disc_identity': 'sha256:disc'}}},
        overrides={}, texture_overrides={}, model_overrides={},
        actor_drafts={'draft': {'scene_id': 'scene://fixture', 'donor_entity_id': 'donor'}})
    audit = {'source_prot_sha256': sha256(prot).hexdigest(), 'source_disc_sha256': 'disc',
             '_rebuild_request': {'entry_index': 0, 'table_offset': 0,
                                 'source_man_sha256': sha256(original).hexdigest(), 'candidate': candidate},
             'actor': {'drafts': [{'draft_id': 'draft', 'record_index': 2}]}}
    return project, archive, prot, container, candidate, audit


class NPCBuildGuards(unittest.TestCase):
    def setUp(self):
        # These fixtures isolate compressed carrier ownership, not executable/MAN decoding.
        helper = patch('sdk.npc_build.actor_pool_assessment', return_value={
            'runtime_allocation_verified': False, 'other_scene_and_script_demand': 'unverified'})
        self.pool = helper.start()
        self.addCleanup(helper.stop)

    def test_actor_pool_failure_rejects_before_encoding_without_mutation(self):
        from importer.core import ImportError
        project, archive, prot, source, _, audit = fixture()
        before = deepcopy(project.__dict__)
        self.pool.side_effect = ImportError('NPC initial placement demand is at least 144 nodes but the retail actor pool has only 143')
        with patch('sdk.npc_build._prepare_draft_scene', return_value=(prot, audit)), patch('sdk.npc_build.compress_lzs') as encode:
            with self.assertRaisesRegex(ImportError, 'at least 144 nodes'):
                prepare_npc_overlays(project, 'scene://fixture', archive)
        encode.assert_not_called()
        self.assertEqual(project.__dict__, before)
        self.assertNotIn('actor_pool_evidence', audit)

    def test_two_fixed_claims_change_size_and_stream_only(self):
        project, archive, prot, source, candidate, audit = fixture()
        key = authored_state_key(project)
        with patch('sdk.npc_build._prepare_draft_scene', return_value=(prot, audit)):
            overlays, edits, metadata = prepare_npc_overlays(project, 'scene://fixture', archive)
        emitted = bytearray(source)
        allowed = set()
        for row in overlays:
            at = row['offset'] - 20 * 2048 - 2048
            self.assertEqual(row['expected_sha256'], sha256(source[at:at + row['size']]).hexdigest())
            self.assertEqual(row['sha256'], sha256(row['payload']).hexdigest())
            emitted[at:at + row['size']] = row['payload']
            allowed.update(range(at, at + row['size']))
        self.assertEqual(len(emitted), len(source))
        table = parse_scene_table(bytes(emitted), 0)
        self.assertEqual(table.descriptors[0].size, len(candidate))
        self.assertEqual(decompress_lzs(emitted[56:], len(candidate))[0], candidate)
        self.assertEqual(source[12:16], emitted[12:16])
        self.assertEqual(source[169:], emitted[169:])
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(source, emitted))))
        self.assertEqual(len(overlays), 2)
        self.assertEqual(edits[0]['field'], 'npc.appended_record')
        self.assertFalse(metadata['allocation_verified'])
        self.assertEqual(authored_state_key(project), key)

    def test_capacity_identity_raw_and_stale_inputs_fail_without_writes(self):
        project, archive, prot, _, _, audit = fixture(bytes(range(256)))
        with patch('sdk.npc_build._prepare_draft_scene', return_value=(prot, audit)):
            with self.assertRaisesRegex(ProjectError, 'original consumed span'):
                prepare_npc_overlays(project, 'scene://fixture', archive)
        project, archive, prot, _, _, audit = fixture()
        for mutate, message in [
            (lambda p, a: p.imports['scene://fixture']['source'].update(disc_identity='sha256:other'), 'disc differs'),
            (lambda p, a: a.update(source_prot_sha256='stale'), 'archive changed'),
            (lambda p, a: a['_rebuild_request'].update(source_man_sha256='stale'), 'MAN source changed'),
        ]:
            p, a = deepcopy(project), deepcopy(audit)
            mutate(p, a)
            with patch('sdk.npc_build._prepare_draft_scene', return_value=(prot, a)), self.assertRaisesRegex(ProjectError, message):
                prepare_npc_overlays(p, 'scene://fixture', archive)
        project.imports['scene://fixture']['actors'] = [{'source_record': {'scene_bundle': {'kind': 'raw_streaming_man'}}}]
        with patch('sdk.npc_build._prepare_draft_scene') as prepare, self.assertRaisesRegex(ProjectError, 'Streaming'):
            prepare_npc_overlays(project, 'scene://fixture', archive)
        prepare.assert_not_called()
        project.imports['scene://fixture']['actors'] = []
        def drift(*args, **kwargs):
            project.name = 'changed'
            return prot, audit
        with patch('sdk.npc_build._prepare_draft_scene', side_effect=drift), self.assertRaisesRegex(ProjectError, 'inputs changed'):
            prepare_npc_overlays(project, 'scene://fixture', archive)


@unittest.skipUnless(os.environ.get('LEGAIA_NPC_PROJECT'), 'requires private composed Town01 fixture')
class RetailNPCPackage(unittest.TestCase):
    def test_normal_package_reopens_changed_descriptor_and_preserves_source(self):
        from sdk.project import ProjectService
        from sdk.build import build_project
        from sdk.build_review import review
        from importer.pipeline import _disc_context, _bounded_scene_range
        from importer.man_source import read_man_source
        from importer.man_layout import read_man_layout
        from importer.core import parse_man
        from importer.script_inspection import inspect_record
        from importer.trigger_scripts import _p2_entry
        project = ProjectService.open(Path(os.environ['LEGAIA_NPC_PROJECT']))
        key = authored_state_key(project)
        saved = {str(f.relative_to(project.root)): sha256(f.read_bytes()).hexdigest()
                 for f in project.root.rglob('*') if f.is_file() and 'Builds' not in f.parts}
        result = review(project)
        self.assertTrue(result['normal_build_ready'])
        with tempfile.TemporaryDirectory(prefix='npc-package-', dir=project.root.parent) as output:
            built = build_project(project, Path(output)/'Build')
            audit = json.loads(Path(built['audit']).read_text())
            metadata = audit['npc_candidates']['scene://town01']
            pool = metadata['draft_audit']['actor_pool_evidence']
            self.assertEqual(pool['source']['node_capacity'], 143)
            self.assertEqual(pool['initial_placement_minimum_nodes'], 54)
            self.assertFalse(pool['runtime_allocation_verified'])
            self.assertEqual(pool['later_setup_allocation_attempts'], 2)
            self.assertFalse(pool['later_setup_attempts_are_additive_capacity'])
            self.assertEqual(len(pool['source']['setup_allocation_sites']), 6)
            physical = metadata['physical_owner']
            with _disc_context(project.disc_path) as (_, _, mapping, archive):
                start, end = _bounded_scene_range(archive, mapping, 'town01')
                source = read_man_source(archive, start, end, 'town01').payload
                original = archive.image.read_user(archive.node.extent_lba, physical['byte_offset'],
                    physical['byte_length'], archive.node.size)
                toc_before = archive.image.read_user(archive.node.extent_lba, 0, 2048, archive.node.size)
                candidate = bytearray(original)
                allowed = set()
                with zipfile.ZipFile(built['path']) as package:
                    manifest = tomllib.loads(package.read('manifest.toml').decode())
                    self.assertEqual(len(manifest['overlay']), 2)
                    for overlay in manifest['overlay']:
                        local = overlay['offset']-archive.node.extent_lba*2048-physical['byte_offset']
                        payload = package.read(overlay['file'])
                        self.assertEqual(overlay['sha256'], sha256(payload).hexdigest())
                        self.assertEqual(overlay['expected_sha256'],sha256(original[local:local+len(payload)]).hexdigest())
                        candidate[local:local+len(payload)] = payload
                        allowed.update(range(local,local+len(payload)))
                self.assertEqual(len(candidate),len(original))
                self.assertTrue(all(a == b or at in allowed for at,(a,b) in enumerate(zip(original,candidate))))
                table = parse_scene_table(bytes(candidate),physical['entry_index'])
                oldtable = parse_scene_table(original,physical['entry_index'])
                descriptor = next(d for d in table.descriptors if d.type_byte == 3 and d.size)
                decoded,consumed = decompress_lzs(candidate[descriptor.data_offset:],descriptor.size)
                self.assertEqual(descriptor.size,45338+579)
                self.assertLessEqual(consumed,24894)
                self.assertEqual(read_man_layout(source)['partition_counts'],[36,53,39])
                self.assertEqual(read_man_layout(decoded)['partition_counts'],[36,54,39])
                for old,new in zip(oldtable.descriptors,table.descriptors):
                    self.assertEqual((old.type_byte,old.data_offset),(new.type_byte,new.data_offset))
                    if old.index != descriptor.index:
                        self.assertEqual(old.size,new.size)
                        stop = min([d.data_offset for d in oldtable.descriptors if d.data_offset>old.data_offset]+[len(original)])
                        self.assertEqual(original[old.data_offset:stop],candidate[old.data_offset:stop])
                def records(data):
                    return {(r['partition'],r['record_index']):data[r['byte_offset']:r['byte_offset']+r['byte_length']]
                            for r in read_man_layout(data)['records']}
                oldrecords,newrecords=records(source),records(decoded)
                donor=oldrecords[1,11]
                clone=bytearray(donor)
                at=1+donor[0]*2+2
                draft=next(iter(project.actor_drafts.values()))
                for relative,axis in ((at,'x'),(at+1,'z')):
                    clone[relative]=next(b for b in range(256) if (b&127)*128+(128 if b&128 else 64)==draft['position'][axis])
                self.assertEqual(newrecords[1,53],bytes(clone))
                actors={a.record_index:a for a in parse_man(decoded).actors}
                self.assertEqual((actors[53].world_x,actors[53].world_z),(3008,5440))
                self.assertEqual((actors[11].world_x,actors[11].world_z),(2944,5440))
                reached=0
                for identity,body in oldrecords.items():
                    partition,index=identity
                    if partition==0:continue
                    entry=1+body[0]*2+4 if partition==1 else _p2_entry(body)[0]
                    for node in inspect_record(body,entry)['instructions']:
                        if node['mnemonic']!='SPAWN_RECORD':continue
                        relative=node['pc']+(2 if node['target_context'] is not None else 1)
                        self.assertEqual(body[relative],node['operands']['global_record_index'])
                        self.assertGreaterEqual(body[relative],89)
                        self.assertEqual(newrecords[identity][relative],body[relative]+1)
                        reached+=1
                self.assertGreater(reached,0)
                self.assertEqual(toc_before,archive.image.read_user(archive.node.extent_lba,0,2048,archive.node.size))
            self.assertEqual(audit['validation']['live_runtime'],'not_run')
            self.assertFalse(metadata['allocation_verified'])
            self.assertTrue(any(c['field']=='npc.composed.facing_changes' for c in built['report']['changes']))
        self.assertEqual(key,authored_state_key(project))
        self.assertEqual(saved,{str(f.relative_to(project.root)):sha256(f.read_bytes()).hexdigest()
                               for f in project.root.rglob('*') if f.is_file() and 'Builds' not in f.parts})


if __name__ == '__main__':
    unittest.main()

"""Private native delivery proof for shared heights composed with real NPC appends.

Normal packages only; never exports a disc, installs a mod or launches a game.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import tempfile
import tomllib
import unittest
import zipfile

from importer.core import decompress_lzs, parse_man, parse_scene_assets
from importer.disc_relocation_package import decode_relocation_package
from importer.environment import load_environment_placements
from importer.man_source import read_man_source
from importer.model_pack_archive import _archive
from importer.pipeline import import_scene, _disc_context, _bounded_scene_range
from importer.streaming_man import streaming_chunks
from sdk.build import build_project, authored_state_key, package_change_kinds
from sdk.build_review import review as build_review
from sdk.floor_heights import review
from sdk.project import ProjectService


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail disc')
class FloorHeightDelivery(unittest.TestCase):
    def test_compressed_fixed_npc(self):
        self.check_delivery('town01', 1, False)

    def test_compressed_grown_npc(self):
        self.check_delivery('town01', 8, True)

    def test_raw_streaming_without_npc(self):
        self.check_delivery('dolk2', 0, False)

    def test_raw_streaming_grown_npc(self):
        self.check_delivery('dolk2', 1, True)

    def emitted_man(self, project, built, carrier, map_index, expected_map):
        """Reopen emitted native carrier independently of SDK candidate metadata."""
        with zipfile.ZipFile(built['path']) as package:
            manifest = tomllib.loads(package.read('manifest.toml').decode('utf-8'))
            relocated = bool(manifest.get('disc_relocation'))
            if relocated:
                self.assertEqual(len(manifest['disc_relocation']), 1)
                row = manifest['disc_relocation'][0]
                archive = _archive(decode_relocation_package(package.read(row['file']), row['sha256'])['replacement'])
                body = archive.read_entry(archive.entry(carrier.entry_index))
                self.assertEqual(archive.read_entry(archive.entry(map_index), extended=True), expected_map)
            else:
                with _disc_context(project.disc_path) as (_, _, _, archive):
                    entry = archive.entry(carrier.entry_index)
                    body = bytearray(archive.read_entry(entry))
                    base = (archive.node.extent_lba + entry.start_lba) * 2048
                    map_entry = archive.entry(map_index)
                    map_body = bytearray(archive.read_entry(map_entry, extended=True))
                    map_base = (archive.node.extent_lba + map_entry.start_lba) * 2048
                for overlay in manifest.get('overlay', []):
                    at = overlay['offset'] - base
                    if 0 <= at < len(body):
                        payload = package.read(overlay['file'])
                        self.assertLessEqual(at + len(payload), len(body))
                        self.assertEqual(sha256(body[at:at+len(payload)]).hexdigest(), overlay['expected_sha256'])
                        self.assertEqual(sha256(payload).hexdigest(), overlay['sha256'])
                        body[at:at+len(payload)] = payload
                    map_at = overlay['offset'] - map_base
                    if 0 <= map_at < len(map_body):
                        payload = package.read(overlay['file'])
                        self.assertLessEqual(map_at + len(payload), len(map_body))
                        self.assertEqual(sha256(map_body[map_at:map_at+len(payload)]).hexdigest(), overlay['expected_sha256'])
                        map_body[map_at:map_at+len(payload)] = payload
                self.assertEqual(bytes(map_body), expected_map)
                body = bytes(body)
        if carrier.kind == 'raw_streaming_man':
            chunks, terminated = streaming_chunks(body)
            self.assertTrue(terminated)
            rows = [c for c in chunks if c['type_byte'] == 3]
            self.assertEqual(len(rows), 1)
            row = rows[0]
            native = body[row['header_offset']+4:row['header_offset']+4+row['size']]
        else:
            table_offset = carrier.bundle.table_offset
            table = parse_scene_assets(body, carrier.entry_index, table_offset)
            rows = [d for d in table.descriptors if d.type_byte == 3 and d.size]
            self.assertEqual(len(rows), 1)
            row = rows[0]
            native = decompress_lzs(body[table_offset+row.data_offset:], row.size)[0]
        return native, relocated

    def check_delivery(self, name, count, expected_growth):
        with tempfile.TemporaryDirectory(prefix='floor-delivery-') as directory:
            project = ProjectService(Path(directory))
            project.disc_path = os.environ['LEGAIA_DISC_BIN']
            project.import_metadata(import_scene(project.disc_path, name))
            scene = project.active_scene
            imported = deepcopy(project.imports)
            donor = f'{scene}/actors/man-p1/{11 if name == "town01" else 1:04d}'
            for i in range(count):
                project.command(dict(type='create_actor_draft', donor_entity_id=donor,
                                     position=dict(x=64+128*i, z=64), name=f'Deferred floor NPC {i+1}'))
            source_map = project._environment_source(scene)
            map_hash = sha256(source_map).hexdigest()
            map_index = load_environment_placements(project.disc_path, name)['source_record']['map_entry_index']
            expected_map = bytearray(source_map)
            expected_map[0x4080] = ((source_map[0x4080]^16)&0xf0)|1
            expected_map = bytes(expected_map)
            project.command(dict(type='set_floor_tiers', entity_id=scene,
                                 value=dict(source_sha256=map_hash, edits=[dict(row=1,column=0,tier=1)])))
            project.command(dict(type='set_collision_walls', entity_id=scene,
                                 value=dict(source_sha256=map_hash, edits=[dict(row=1,column=0,quadrant=0,blocked=not bool(source_map[0x4080]&16))])))
            with _disc_context(project.disc_path) as (_, _, mapping, archive):
                start, end = _bounded_scene_range(archive, mapping, name)
                carrier = read_man_source(archive, start, end, name)
            baseline = build_project(project)
            before, baseline_growth = self.emitted_man(project, baseline, carrier, map_index, expected_map)
            self.assertEqual(baseline_growth, expected_growth)
            heights = list(struct.unpack_from('<16h', carrier.payload, 2))
            heights[1] += 16
            reviewed = review(project, scene, heights)
            project.command(dict(type='apply_floor_heights', entity_id=scene, heights=heights, review_key=reviewed['review_key']))
            project = ProjectService.open(project.save())
            saved = deepcopy((project.overrides, project.actor_drafts, project.undo_stack))
            key = authored_state_key(project)
            assessment = build_review(project)
            self.assertTrue(assessment['normal_build_ready'], assessment['blockers'])
            built = build_project(project)
            with zipfile.ZipFile(built['path']) as package:
                manifest = tomllib.loads(package.read('manifest.toml').decode('utf-8'))
                self.assertIn('source floor heights', manifest['feature'][0]['description'])
            actual, growth = self.emitted_man(project, built, carrier, map_index, expected_map)
            expected = bytearray(before)
            struct.pack_into('<h', expected, 4, heights[1])
            self.assertEqual(actual, bytes(expected))
            self.assertEqual(growth, expected_growth)
            self.assertEqual(len(parse_man(actual, name).actors), len(imported[scene]['actors'])+count)
            self.assertEqual(project.imports, imported)
            self.assertEqual((project.overrides, project.actor_drafts, project.undo_stack), saved)
            self.assertEqual(authored_state_key(project), key)
            audit = json.loads(Path(built['audit']).read_text(encoding='utf-8'))
            self.assertEqual(audit['validation']['live_runtime'], 'not_run')
            if count:
                changes = audit['npc_candidates'][scene]['draft_audit']['floor_height_changes']
            else:
                changes = [row for row in audit['edits'] if row.get('field') == 'floor_height']
            self.assertEqual(len(changes), 1)
            self.assertEqual(changes[0]['decoded_byte_offset'], 4)
            self.assertEqual(changes[0]['byte_length'], 2)
            self.assertIn('source floor heights', package_change_kinds(audit['edits']))
            evidence = dict(scene=name, npc_count=count, source_kind=carrier.kind,
                            relocated=growth, exact_complete_MAN=True, exact_complete_MAP=True, source_and_history_unchanged=True,
                            gameplay_verified=False, native_man_sha256=sha256(actual).hexdigest(),
                            native_map_sha256=sha256(expected_map).hexdigest(),
                            source_man_sha256=sha256(carrier.payload).hexdigest(),
                            baseline_man_sha256=sha256(before).hexdigest(),
                            change_kinds=package_change_kinds(audit['edits']),
                            manifest_names_floor_heights=True,
                            package_sha256=built['sha256'])
            target = os.environ.get('LEGAIA_FLOOR_DELIVERY_PROOF')
            if target:
                output = Path(target); output.mkdir(parents=True, exist_ok=True)
                (output/f'{name}-{count}.json').write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()

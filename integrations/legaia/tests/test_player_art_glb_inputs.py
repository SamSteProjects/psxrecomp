import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.me_archive import entries
from importer.player_art_authoring import compose, owner
from importer.player_battle import decode_part
from sdk.project import ProjectError
from sdk.player_art_glb import prepare_input, validate_input, retain_inputs, _path


@unittest.skipUnless(os.getenv('PLAYER_ART_CURRENT_EXPORT_CASES') and os.getenv('LEGAIA_DISC_BIN'),
                     'Private qualified exports and source disc required')
class ArtInputTests(unittest.TestCase):
    def test_historical_replay_neighbors_tampering_and_storage_preflight(self):
        cases = json.loads(Path(os.environ['PLAYER_ART_CURRENT_EXPORT_CASES']).read_text(encoding='utf-8'))['cases']
        clips = [c for c in cases if c['selection']['mode'] == 'clip']
        self.assertEqual(len(clips), 2)
        for case in clips:
            with tempfile.TemporaryDirectory() as root:
                project = SimpleNamespace(root=Path(root), disc_path=os.environ['LEGAIA_DISC_BIN'])
                inspection = case['inspection']; base = inspection['base_playback']
                stream = base['stream']; catalog = case['art_report']['catalog']
                original = base64.b64decode(base['source_slot_base64'])
                baseline_owners = deepcopy(inspection['owners'])
                neighbor = next(s for s in catalog['streams'] if s['archive_asset_id'] == stream['archive_asset_id'] and s['semantic_id'] != stream['semantic_id'])
                channels = decode_part(entries(original)[neighbor['stream_index']]['decoded'][2:11])
                channels['translation'][0] ^= 1
                baseline_owners[neighbor['semantic_id']] = owner(original, catalog, stream['archive_asset_id'], neighbor['semantic_id'], [dict(frame_index=0, part_index=0, **channels)])
                current = compose(original, catalog, stream['archive_asset_id'], baseline_owners)
                doc, binary = _read_glb(base64.b64decode(case['export']['glb_base64'])); binary = bytearray(binary)
                parts = base['base_inspection']['assembly']['animation_part_indices']
                for channel in doc['animations'][0]['channels']:
                    if channel['target']['path'] == 'translation' and parts[channel['target']['node']] == 0:
                        accessor = doc['accessors'][doc['animations'][0]['samplers'][channel['sampler']]['output']]
                        at = doc['bufferViews'][accessor['bufferView']]['byteOffset']
                        struct.pack_into('<f', binary, at, struct.unpack_from('<f', binary, at)[0] + 1)
                content = _write_glb(doc, bytes(binary))
                args = (project, original, catalog, stream['archive_asset_id'], stream['semantic_id'], current, baseline_owners, content)
                kwargs = dict(equipped=base['base_inspection']['assembly']['equipped'], fps=23.5)
                candidate, report, evidence = prepare_input(*args, **kwargs)
                self.assertFalse((project.root / 'Authored').exists())
                self.assertEqual(len(report['edits']), 1)
                row = entries(current)[stream['stream_index']]; start = row['byte_offset']; end = start + row['byte_length']
                self.assertEqual(candidate[:start], current[:start]); self.assertEqual(candidate[end:], current[end:])
                self.assertNotEqual(candidate, current)
                held = deepcopy(evidence)
                retain_inputs(project, evidence, current, content)
                retain_inputs(project, evidence, current, content, active_inputs=[evidence] * 87)
                self.assertEqual(validate_input(project, original, catalog, evidence), (candidate, report))
                self.assertEqual(evidence, held)
                for key in ['../escape', 'A' * 64, '', None]:
                    with self.assertRaises(ProjectError): _path(project, key, 'glb')
                with self.assertRaises(ProjectError): _path(project, evidence['glb_sha256'], 'txt')
                # Later Current numeric edits do not rewrite or become the import baseline.
                later_owners = deepcopy(baseline_owners); later_owners.pop(neighbor['semantic_id'])
                later = compose(original, catalog, stream['archive_asset_id'], later_owners)
                self.assertNotEqual(later, current)
                self.assertEqual(validate_input(project, original, catalog, evidence)[0], candidate)
                mutations = [lambda v:v.update(extra=True), lambda v:v.update(model_source_sha256='0'*64),
                             lambda v:v.update(import_digest='0'*64), lambda v:v.update(fps=True),
                             lambda v:v.update(baseline_slot_byte_length=True),
                             lambda v:v['object_part_indices'].__setitem__(0, 1),
                             lambda v:v['baseline_owners'].pop(neighbor['semantic_id']),
                             lambda v:v['source_record'].update(sha256='0'*64)]
                for mutate in mutations:
                    bad = deepcopy(evidence); mutate(bad)
                    with self.assertRaises(ProjectError): validate_input(project, original, catalog, bad)
                for kind, key, raw in [('glb', evidence['glb_sha256'], content), ('bin', evidence['baseline_slot_sha256'], current)]:
                    path = _path(project, key, kind)
                    path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                    with self.assertRaises(ProjectError): validate_input(project, original, catalog, evidence)
                    path.write_bytes(raw)
                    path.unlink()
                    with self.assertRaises(ProjectError): validate_input(project, original, catalog, evidence)
                    path.write_bytes(raw)
                # A newly rehashed baseline with an edited tail still fails canonical replay.
                changed = current[:-1] + bytes([current[-1] ^ 1]); bad = deepcopy(evidence)
                bad['baseline_slot_sha256'] = sha256(changed).hexdigest()
                _path(project, bad['baseline_slot_sha256'], 'bin').write_bytes(changed)
                with self.assertRaises(ProjectError): validate_input(project, original, catalog, bad)
                with tempfile.TemporaryDirectory() as fresh:
                    target = SimpleNamespace(root=Path(fresh), disc_path=project.disc_path)
                    with self.assertRaises(ProjectError): retain_inputs(target, evidence, current[:-1], content)
                    self.assertFalse((target.root / 'Authored').exists())
                    oversized = []
                    for index in range(16):
                        value = deepcopy(evidence); value['glb_sha256'] = sha256(str(index).encode()).hexdigest(); value['glb_byte_length'] = 4 * 1024 * 1024
                        oversized.append(value)
                    with self.assertRaisesRegex(ProjectError, '64 MiB'):
                        retain_inputs(target, evidence, current, content, active_inputs=oversized)
                    self.assertFalse((target.root / 'Authored').exists())
                    baseline_path = _path(target, evidence['baseline_slot_sha256'], 'bin')
                    baseline_path.parent.mkdir(parents=True); baseline_path.write_bytes(b'broken')
                    with self.assertRaises(ProjectError): retain_inputs(target, evidence, current, content)
                    self.assertFalse(_path(target, evidence['glb_sha256'], 'glb').exists())
                    baseline_path.unlink()
                    from sdk.project import atomic_write
                    calls = []
                    def fail_second(path, raw):
                        calls.append(path)
                        if len(calls) == 2: raise OSError('simulated write failure')
                        atomic_write(path, raw)
                    with patch('sdk.player_art_glb.atomic_write', side_effect=fail_second):
                        with self.assertRaises(OSError): retain_inputs(target, evidence, current, content)
                    self.assertFalse(any((target.root / 'Authored').rglob('*.glb')))
                    self.assertFalse(any((target.root / 'Authored').rglob('*.bin')))
        print('Two art imports: canonical neighboring owners, immutable source/assembly replay, altered/missing inputs, budget/collision and write rollback checks passed', flush=True)


if __name__ == '__main__': unittest.main()

import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from importer.me_archive import entries
from importer.player_art_authoring import owner
from importer.player_battle import decode_part
from importer.pipeline import import_scene
from sdk.project import ProjectService, ProjectError
from sdk.project_assets import source_key
from sdk.build import authored_state_key, build_project
from sdk.player_art_glb import prepare_input, retain_inputs, _path
from sdk.player_art_store import context, validate, composed_slots
from sdk.player_art_authoring import inspect, review, apply


@unittest.skipUnless(os.getenv('PLAYER_ART_CURRENT_EXPORT_CASES') and os.getenv('LEGAIA_DISC_BIN'),
                     'Private qualified exports and source disc required')
class ArtInputStoreTests(unittest.TestCase):
    def test_open_history_numeric_edits_restoration_and_package(self):
        cases = json.loads(Path(os.environ['PLAYER_ART_CURRENT_EXPORT_CASES']).read_text(encoding='utf-8'))['cases']
        case = next(c for c in cases if c['selection']['mode'] == 'clip' and c['selection']['layer'] == 'retail')
        base = case['inspection']['base_playback']; stream = base['stream']
        with tempfile.TemporaryDirectory() as root:
            p = ProjectService(Path(root)); p.disc_path = os.environ['LEGAIA_DISC_BIN']; p.save()
            raw, catalog, _ = context(p); at = stream['source_record']['slot_offset']; original = raw[at:at+0x10800]
            content = base64.b64decode(case['export']['glb_base64'])
            # Import the fixture's previously qualified numeric Current motion
            # onto Retail; use complete native rows rather than import-relative deltas.
            candidate, analysis, evidence = prepare_input(p, original, catalog,
                stream['archive_asset_id'], stream['semantic_id'], original, {}, content,
                equipped=base['base_inspection']['assembly']['equipped'], fps=23.5)
            self.assertTrue(analysis['edits'])
            decoded = entries(candidate)[stream['stream_index']]['decoded']; retail = entries(original)[stream['stream_index']]['decoded']
            rows = []
            for frame in range(stream['frame_count']):
                for part in range(stream['part_count']):
                    offset = 2 + (frame * stream['part_count'] + part) * 9
                    if decoded[offset:offset+9] != retail[offset:offset+9]:
                        rows.append(dict(frame_index=frame, part_index=part, **decode_part(decoded[offset:offset+9])))
            values = {stream['semantic_id']: owner(original, catalog, stream['archive_asset_id'], stream['semantic_id'], rows)}
            values[stream['semantic_id']]['glb_import'] = deepcopy(evidence)
            with self.assertRaises(ProjectError): validate(p, values)
            self.assertEqual(p.player_art_overrides, {})
            retain_inputs(p, evidence, original, content)
            with self.assertRaises(ProjectError): composed_slots(raw, catalog, values)
            current = composed_slots(raw, catalog, values, project=p)[stream['archive_asset_id']]
            self.assertEqual(current, candidate)
            initial_source = source_key(p); initial_build = authored_state_key(p)
            p.player_art_overrides = validate(p, values)
            imported_source = source_key(p); imported_build = authored_state_key(p)
            numeric_only = deepcopy(values); numeric_only[stream['semantic_id']].pop('glb_import')
            p.player_art_overrides = numeric_only
            self.assertNotEqual(source_key(p), imported_source); self.assertNotEqual(authored_state_key(p), imported_build)
            p.player_art_overrides = deepcopy(values)
            p.undo_stack.append(dict(target='player_art_overrides', before={}, after=deepcopy(values), label='PLAYER Art GLB'))
            self.assertNotEqual(source_key(p), initial_source); self.assertNotEqual(authored_state_key(p), initial_build)
            p.undo(); self.assertEqual(p.player_art_overrides, {})
            glb = _path(p, evidence['glb_sha256'], 'glb'); glb.unlink()
            held = deepcopy((p._document(), p.undo_stack, p.redo_stack))
            with self.assertRaises(ProjectError): p.redo()
            self.assertEqual((p._document(), p.undo_stack, p.redo_stack), held)
            glb.write_bytes(content); p.redo(); p.save(); p = ProjectService.open(p.root)
            self.assertEqual(p.player_art_overrides, values)
            args = dict(expected_project_path=str(p.root), expected_source_key=source_key(p),
                asset_id=stream['model_asset_id'], catalog_source_key=base['catalog_source_key'],
                equipped=evidence['equipped'], art_source_key=catalog['source_key'], stream_id=stream['semantic_id'],
                art_record_id=None, layer='retail', expected_current_sha256=None, frame_index=0, part_index=0)
            inspection = inspect(p, **args); channels = deepcopy(inspection['channels']); channels['translation'][0] ^= 2
            changed_args = dict(args, expected_current_slot_sha256=inspection['current_slot_sha256'], **channels)
            proposal = review(p, **changed_args)
            self.assertEqual(proposal['ownership_after']['glb_import'], evidence)
            apply(p, review_key=proposal['review_key'], **changed_args)
            self.assertEqual(p.player_art_overrides[stream['semantic_id']]['glb_import'], evidence)
            p.save(); p = ProjectService.open(p.root)
            p.import_metadata(import_scene(p.disc_path, 'town01')); p.save()
            built = build_project(p); audit = json.loads(Path(built['audit']).read_text(encoding='utf-8'))
            overlays = [o for o in audit['overlays'] if o.get('source_kind') == 'fixed_span_player_art_me_body']
            self.assertEqual(len(overlays), 1)
            expected = bytearray(raw); expected[at:at+0x10800] = composed_slots(raw, catalog, p.player_art_overrides, project=p)[stream['archive_asset_id']]
            reconstructed = bytearray(raw)
            with zipfile.ZipFile(built['path']) as package:
                for overlay in overlays:
                    payload = package.read(overlay['file']); self.assertEqual(payload, (Path(built['package_directory']) / overlay['file']).read_bytes())
                    self.assertEqual(sha256(payload).hexdigest(), overlay['sha256'])
                    offset = overlay['source_record']['byte_offset']; reconstructed[offset:offset+len(payload)] = payload
            self.assertEqual(reconstructed, expected)
            # Every persistence/native-delivery entry point rejects changed retained bytes.
            glb = _path(p, evidence['glb_sha256'], 'glb'); glb.write_bytes(content[:-1] + bytes([content[-1] ^ 1]))
            held = deepcopy((p._document(), p.undo_stack, p.redo_stack))
            for operation in [lambda:p.save(), lambda:ProjectService.open(p.root), lambda:build_project(p)]:
                with self.assertRaises(ProjectError): operation()
                self.assertEqual((p._document(), p.undo_stack, p.redo_stack), held)
            glb.write_bytes(content)
            # Fully restoring sparse Retail rows removes membership, not files.
            while stream['semantic_id'] in p.player_art_overrides:
                row = p.player_art_overrides[stream['semantic_id']]['edits'][0]
                args.update(expected_source_key=source_key(p), frame_index=row['frame_index'], part_index=row['part_index'])
                inspection = inspect(p, **args); offset = 2 + (row['frame_index'] * stream['part_count'] + row['part_index']) * 9
                restore_args = dict(args, expected_current_slot_sha256=inspection['current_slot_sha256'], **decode_part(retail[offset:offset+9]))
                proposal = review(p, **restore_args); apply(p, review_key=proposal['review_key'], **restore_args)
            self.assertTrue(glb.is_file()); self.assertTrue(_path(p, evidence['baseline_slot_sha256'], 'bin').is_file())
            p.undo(); self.assertEqual(p.player_art_overrides[stream['semantic_id']]['glb_import'], evidence)
            p.redo(); self.assertEqual(p.player_art_overrides, {})
            print('Retained art owner: history/Open/Save, later numeric edits, exact complete-entry ZIP/directory delivery, corrupt input refusal and restoration passed', flush=True)


if __name__ == '__main__': unittest.main()

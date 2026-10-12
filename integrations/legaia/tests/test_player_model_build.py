"""Private-disc proof of all four physical PLAYER overlays and package readback."""
import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
import zipfile
from importer.animation_glb import _read_glb
from importer.model_glb import _write_glb
from importer.pipeline import _disc_context, import_scene
from sdk.build import build_project, _build_project, package_change_kinds
from sdk.player_battle import resources
from sdk.player_model_authoring import export, review, apply
from sdk.player_model_build import prepare
from sdk.project import ProjectService, ProjectError
from sdk.project_assets import source_key


@unittest.skipUnless(os.getenv('LEGAIA_DISC_BIN'), 'Retail disc is private')
class PlayerModelBuildTests(unittest.TestCase):
    def test_all_player_files_package_readback_and_neighbors(self):
        with tempfile.TemporaryDirectory() as directory:
            p = ProjectService(Path(directory))
            p.disc_path = os.environ['LEGAIA_DISC_BIN']
            p.import_metadata(import_scene(p.disc_path, 'town01'))
            catalog = resources(p, str(p.root), source_key(p))['catalog']
            for record in catalog['models']:
                ctx = dict(expected_project_path=str(p.root), expected_source_key=source_key(p),
                    asset_id=record['semantic_id'], catalog_source_key=catalog['source_key'], equipped=[0]*5)
                exported = export(p, **ctx)
                doc, binary = _read_glb(base64.b64decode(exported['glb_base64']))
                doc['nodes'][0]['translation'] = [10, 0, 0]
                payload = base64.b64encode(_write_glb(doc, binary)).decode()
                reviewed = review(p, **ctx, binding=exported['binding'], glb_base64=payload)
                apply(p, **ctx, binding=exported['binding'], glb_base64=payload,
                    review_key=reviewed['review_key'])
            p.save()
            p = ProjectService.open(p.root)
            before = deepcopy((p._document(), p.undo_stack, p.redo_stack))
            with _disc_context(p.disc_path) as (image, digest, _, archive):
                overlays, changes = prepare(p, archive, digest)
                self.assertEqual(len(overlays), 4)
                self.assertEqual(package_change_kinds(changes), ['PLAYER native models'])
                for overlay in overlays:
                    source = overlay['source_record']
                    self.assertEqual(overlay['offset'], (archive.node.extent_lba + source['start_lba'])*2048)
                    self.assertEqual(overlay['size'], (source['next_start_lba']-source['start_lba'])*2048)
                    original = image.read_user(0, overlay['offset'], overlay['size'], (image.size//2352)*2048)
                    self.assertEqual(sha256(original).hexdigest(), overlay['expected_sha256'])
                    self.assertEqual(original[:0x8000], overlay['payload'][:0x8000])
                # Independent sectors immediately outside the entire PLAYER range.
                for edge in (overlays[0]['offset']-2048, overlays[-1]['offset']+overlays[-1]['size']):
                    retail = image.read_user(0, edge, 2048, (image.size//2352)*2048)
                    applied = bytearray(retail)
                    for o in overlays:
                        a, b = max(edge, o['offset']), min(edge+2048, o['offset']+o['size'])
                        if a < b: applied[a-edge:b-edge] = o['payload'][a-o['offset']:b-o['offset']]
                    self.assertEqual(bytes(applied), retail)
                bad = deepcopy(p.player_model_overrides)
                p.player_model_overrides[next(iter(bad))]['source_record']['next_start_lba'] += 1
                with self.assertRaises(ProjectError): prepare(p, archive, digest)
                p.player_model_overrides = bad
            preview = _build_project(p, None, review_only=True)
            self.assertFalse(preview['output_written'])
            built = build_project(p)
            self.assertEqual(built['overlay_count'], 4)
            self.assertEqual({r['scope'] for r in built['report']['changes']}, {'PLAYER-native-model-pools-only'})
            with zipfile.ZipFile(built['path']) as package:
                manifest = tomllib.loads(package.read('manifest.toml').decode())
                self.assertEqual(len(manifest['overlay']), 4)
                for overlay in overlays:
                    self.assertEqual(package.read(overlay['file']), overlay['payload'])
                    self.assertEqual((Path(built['package_directory'])/overlay['file']).read_bytes(), overlay['payload'])
                self.assertEqual([r['expected_sha256'] for r in manifest['overlay']],
                    [o['expected_sha256'] for o in overlays])
            self.assertEqual(before, (p._document(), p.undo_stack, p.redo_stack))
            audit = json.loads(Path(built['audit']).read_text(encoding='utf-8'))
            self.assertTrue(all(o['retained_input_replay'] for o in audit['overlays']))
            self.assertEqual(audit['validation']['live_runtime'], 'not_run')
            evidence = os.getenv('LEGAIA_PLAYER_BUILD_PROOF')
            if evidence:
                Path(evidence).write_text(json.dumps(dict(overlay_count=4,
                    physical_sizes=[o['size'] for o in overlays],
                    package_sha256=built['sha256'], review_matches_build=preview['audit_sha256']==sha256(Path(built['audit']).read_bytes()).hexdigest(),
                    directory_zip_readback=True, record0_unchanged=True, neighbors_unchanged=True,
                    saved_input_replay=True, project_unchanged=True, gameplay_verified=False), indent=2), encoding='utf-8')

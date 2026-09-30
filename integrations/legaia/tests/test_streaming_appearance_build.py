"""Opt-in retail composition of independent edits in one raw streaming MAN."""
import os
from pathlib import Path
import tempfile
import unittest
from importer.pipeline import import_scene
from importer.core import ProtArchive, IsoNode, parse_man
from sdk.project import ProjectService
from sdk.streaming_build import prepare_streaming_scene
from sdk.draft_build import prepare_draft_archive


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class StreamingAppearanceBuild(unittest.TestCase):
    def test_streaming_npc_export_rebases_existing_dialogue_and_transition(self):
        from importer.man_layout import read_man_layout
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.disc_path = os.environ["LEGAIA_DISC_BIN"]
            project.import_metadata(import_scene(project.disc_path, "dolk2"))
            draft_id = "authored-actor://00000000-0000-4000-8000-000000000001"
            project.actor_drafts = {draft_id: dict(scene_id="scene://dolk2", donor_entity_id="scene://dolk2/actors/man-p1/0001",
                                                 position={"x": 64, "z": 16320}, name="Streaming NPC probe")}
            project.overrides = {
                "scene://dolk2/actors/man-p1/0003": {"Dialogue": {"runs": {
                    "script://dolk2/actors/man-p1/0003/dialogue/0017/run/0018": "SDK"}}},
                "scene://dolk2/scripts/man-p2/0000": {"Transitions": {"entries": {
                    "script://dolk2/scripts/man-p2/0000/transition/001a": {"entry_x_encoded": 55}}}}}
            from importer.flag_authoring import load_flag_authoring_context
            context = load_flag_authoring_context(project.disc_path, 'dolk2')
            target = next(target for actor in project.imports['scene://dolk2']['actors']
                          for target in context.options(actor['semantic_id'])['targets']
                          if target['mnemonic'] == 'CFLAG_SET' and target['values']['bit'] == 24)
            bit = (target['values']['bit'] + 1) % 32
            project.command(dict(type='set_flag_bit', entity_id=target['owner_id'],
                                 flag_id=target['semantic_id'], values={'bit':bit}))
            source, prepared = prepare_streaming_scene(project, "scene://dolk2")
            output, audit = prepare_draft_archive(project, draft_id)
            self.assertEqual(audit["selected_draft_id"], draft_id)
            self.assertGreater(len(output), len(source))
            candidate = prepared["_rebuild_request"]["candidate"]
            actors = parse_man(candidate, "dolk2").actors
            self.assertEqual(len(actors), 73)
            self.assertEqual((actors[-1].world_x, actors[-1].world_z), (64, 16320))
            from importer.dialogue_authoring import load_dialogue_authoring_context
            baseline = load_dialogue_authoring_context(project.disc_path, "dolk2")._man
            self.assertEqual(read_man_layout(candidate)["partition_counts"][1], read_man_layout(baseline)["partition_counts"][1] + 1)
            self.assertTrue(audit["container"]["entries"][0]["reopened_man_verified"])
            for change in prepared["existing_actor_dialogue_changes"]:
                at = change["decoded_byte_offset"]
                self.assertEqual(candidate[at:at + change["byte_length"]], bytes.fromhex(change["after_hex"]))
                self.assertGreater(at, change["source_decoded_byte_offset"])
            self.assertEqual(len(prepared['flag_changes']),1)
            flag = prepared['flag_changes'][0]
            self.assertEqual(candidate[flag['decoded_byte_offset']] & 31, bit)
            self.assertGreater(flag['decoded_byte_offset'],flag['source_decoded_byte_offset'])
            self.assertEqual(audit['scenes']['scene://dolk2']['flag_changes'],prepared['flag_changes'])
            self.assertTrue(prepared["transition_changes"])
            self.assertEqual(prepared["actor_changes"]["drafts"][0]["draft_id"], draft_id)

    def test_streaming_texture_and_model_reopen_as_exact_changed_assets(self):
        from hashlib import sha256
        from importer.texture_authoring import load_texture_authoring_context
        from importer.assets import load_model_source
        from importer.core import decompress_lzs
        import struct
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.disc_path = os.environ["LEGAIA_DISC_BIN"]
            project.import_metadata(import_scene(project.disc_path, "dolk2"))
            context = load_texture_authoring_context(project.disc_path, "dolk2")
            identifier = "texture://dolk2/69/0/0"
            original = context.original_tim(identifier)
            replacement = bytearray(original)
            replacement[-2] ^= 1
            replacement = bytes(replacement)
            project.texture_overrides = {identifier: dict(source_scene_id="scene://dolk2", format="tim",
                asset_sha256=sha256(replacement).hexdigest(), byte_length=len(replacement))}
            model = project.imports["scene://dolk2"]["assets"]["models"][0]
            model_id = model["semantic_id"]
            model_original = load_model_source(project.disc_path, model)
            model_replacement = bytearray(model_original)
            vertex_offset = 12 + struct.unpack_from("<I", model_original, 12)[0]
            model_replacement[vertex_offset] ^= 1
            model_replacement = bytes(model_replacement)
            project.model_overrides = {model_id: dict(source_scene_id="scene://dolk2", format="tmd",
                asset_sha256=sha256(model_replacement).hexdigest(), byte_length=len(model_replacement))}
            with patch.object(project, "read_texture_replacement", return_value=replacement), patch.object(
                    project, "read_model_replacement", return_value=model_replacement):
                output, audit = prepare_draft_archive(project)
            carrier = audit["scenes"]["scene://dolk2"]["texture_changes"]["carriers"][0]
            self.assertTrue(carrier["reopened_payload_verified"])
            class MemoryImage:
                def read_user(self, lba, offset, length, file_size): return output[offset:offset + length]
            archive = ProtArchive(MemoryImage(), IsoNode(0, len(output), False, "PROT.DAT"))
            _, source = context._items[identifier]
            final_carrier = context._carrier(archive, source)
            a, b = final_carrier["ranges"][source["pack_slot"]]
            self.assertEqual(final_carrier["decoded"][a:b], replacement)
            self.assertEqual(context.original_tim(identifier), original)
            model_carrier = audit["scenes"]["scene://dolk2"]["model_changes"]["carriers"][0]
            self.assertTrue(model_carrier["reopened_payload_verified"])
            model_source = model["source_record"]
            entry_body = archive.read_entry(archive.entry(model_source["prot_entry_index"]))
            decoded, _ = decompress_lzs(entry_body[model_source["compressed_stream_offset"]:], model_source["containing_size"])
            offset = model_source["byte_offset"]
            self.assertEqual(decoded[offset:offset + len(model_replacement)], model_replacement)
            self.assertEqual(load_model_source(project.disc_path, model), model_original)


    def test_raw_animation_and_man_changes_survive_composition(self):
        from hashlib import sha256
        from importer.scene_animation import load_scene_actor_animation_catalog
        from importer.animation import decode_animation_record
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.disc_path = os.environ["LEGAIA_DISC_BIN"]
            project.import_metadata(import_scene(project.disc_path, "dolk2"))
            catalog = load_scene_actor_animation_catalog(project.disc_path, "dolk2")
            owner = "scene://dolk2/actors/man-p1/0001"
            actor = catalog._actors[owner]
            asset = catalog._assets[actor["model_reference"]["asset_semantic_id"]]
            index, _ = catalog._binding(actor, asset)
            start, end = catalog._ranges[index]
            record = catalog._body[start:end]
            translation = decode_animation_record(record)["frames"][0]["object_transforms"][0]["translation"][0]
            binding = dict(animation_id=f"animation://dolk2/scene-anm/{index:04d}",
                           source_record_sha256=sha256(record).hexdigest(),
                           edits=[dict(frame_index=0, object_index=0, translation={"x": translation + 1 if translation < 2047 else translation - 1})])
            project.overrides = {owner: {"AnimationChannels": binding},
                "scene://dolk2/actors/man-p1/0041": {"ActorAppearance": {"donor_entity_id": owner}}}
            expected, changes = catalog.authored_bank({owner: binding})
            self.assertTrue(changes)
            source, prepared = prepare_streaming_scene(project, "scene://dolk2")
            output, audit = prepare_draft_archive(project)
            carrier = audit["scenes"]["scene://dolk2"]["animation_changes"]["carriers"][0]
            self.assertTrue(carrier["reopened_payload_verified"])
            class MemoryImage:
                def read_user(self, lba, offset, length, file_size): return output[offset:offset + length]
            archive = ProtArchive(MemoryImage(), IsoNode(0, len(output), False, "PROT.DAT"))
            bank_offset = archive.entry(carrier["map_entry_index"]).start_lba * 2048 + carrier["relative_offset"]
            self.assertEqual(output[bank_offset:bank_offset + len(expected)], expected)
            request = prepared["_rebuild_request"]
            man_offset = archive.entry(request["entry_index"]).start_lba * 2048 + request["chunk_header_offset"] + 4
            candidate = request["candidate"]
            self.assertEqual(output[man_offset:man_offset + len(candidate)], candidate)
            restored = bytearray(output)
            for offset, size in ((bank_offset, len(expected)), (man_offset, len(candidate))):
                restored[offset:offset + size] = source[offset:offset + size]
            self.assertEqual(bytes(restored), source)
            from copy import deepcopy
            from sdk.map_build import verify_rebuilt_maps
            from sdk.project import ProjectError
            from importer.prot_rebuild import rebuild_streaming_man_entry
            enlarged, _ = rebuild_streaming_man_entry(output, sha256(output).hexdigest(), request["entry_index"],
                request["chunk_header_offset"], sha256(candidate).hexdigest(), candidate + bytes(4))
            moved = deepcopy(carrier)
            verify_rebuilt_maps(enlarged, [moved])
            self.assertTrue(moved["reopened_payload_verified"])
            stale = deepcopy(carrier)
            stale.pop("streaming_binding")
            with self.assertRaises(ProjectError):
                verify_rebuilt_maps(enlarged, [stale])
            self.assertNotIn("reopened_payload_verified", stale)
            wrong = deepcopy(carrier)
            wrong["streaming_binding"]["type_byte"] = 3
            with self.assertRaises(ProjectError):
                verify_rebuilt_maps(enlarged, [wrong])
            draft_id = "authored-actor://00000000-0000-4000-8000-000000000002"
            project.actor_drafts = {draft_id: dict(scene_id="scene://dolk2", donor_entity_id=owner,
                position={"x": 64, "z": 16320}, name="Animated streaming NPC probe")}
            with_npc, combined = prepare_draft_archive(project, draft_id)
            animation = combined["scenes"]["scene://dolk2"]["animation_changes"]
            self.assertTrue(all(c["reopened_payload_verified"] for c in animation["carriers"]))
            self.assertGreater(len(with_npc), len(output))
            self.assertTrue(combined["scenes"]["scene://dolk2"]["actor_changes"]["drafts"])



    def test_appearance_dialogue_transition_and_position_survive_archive_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            project = ProjectService(Path(directory))
            project.disc_path = os.environ["LEGAIA_DISC_BIN"]
            project.import_metadata(import_scene(project.disc_path, "dolk2"))
            project.overrides = {
                "scene://dolk2/actors/man-p1/0001": {
                    "ActorAppearance": {"donor_entity_id": "scene://dolk2/actors/man-p1/0041"},
                    "Transform": {"position": {"x": 64, "z": 16320}}},
                "scene://dolk2/actors/man-p1/0003": {"Dialogue": {"runs": {
                    "script://dolk2/actors/man-p1/0003/dialogue/0017/run/0018": "SDK"}}},
                "scene://dolk2/scripts/man-p2/0000": {"Transitions": {"entries": {
                    "script://dolk2/scripts/man-p2/0000/transition/001a": {"entry_x_encoded": 55}}}}}
            source, prepared = prepare_streaming_scene(project, "scene://dolk2")
            request = prepared["_rebuild_request"]
            rebuilt, audit = prepare_draft_archive(project)
            class MemoryImage:
                def __init__(self, data): self.data = data
                def read_user(self, lba, offset, length, file_size):
                    return self.data[offset:offset + length]
            archive = ProtArchive(MemoryImage(rebuilt), IsoNode(0, len(rebuilt), False, "PROT.DAT"))
            start = archive.entry(request["entry_index"]).start_lba * 2048 + request["chunk_header_offset"] + 4
            candidate = request["candidate"]
            self.assertEqual(rebuilt[start:start + len(candidate)], candidate)
            self.assertEqual(source[:start], rebuilt[:start])
            self.assertEqual(source[start + len(candidate):], rebuilt[start + len(candidate):])
            changed = {i for i, (a,b) in enumerate(zip(source[start:start+len(candidate)], candidate)) if a != b}
            authorized = set()
            for key in ("existing_actor_appearance_changes", "existing_actor_dialogue_changes", "transition_changes", "existing_actor_placement_changes"):
                self.assertTrue(prepared[key], key)
                for change in prepared[key]:
                    offset = change["decoded_byte_offset"]
                    authorized.update(range(offset, offset + change.get("byte_length", 1)))
            self.assertTrue(changed <= authorized)
            actor = next(a for a in parse_man(candidate, "dolk2").actors if a.record_index == 1)
            self.assertEqual(actor.world_x, 64)
            self.assertFalse(audit["gameplay_verified"])


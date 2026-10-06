"""Build reports describe emitted changes and track authored snapshot identity."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdk.build import authored_state_key, build_report, package_change_kinds
from sdk.project import ProjectService
from integrations.legaia.tests.test_project_workflow import synthetic_scene


class BuildReportTests(unittest.TestCase):
    def test_npc_floor_heights_summary_requires_emitted_height_evidence(self):
        row = dict(scope='source-man-draft-composed-overrides',
                   field='npc.composed.floor_height_changes',
                   composition_changes=[dict(scope='MAN-floor-height-table-only',field='floor_height')])
        original = deepcopy(row)
        self.assertEqual(package_change_kinds([row]), ['NPC scene operand composition','source floor heights'])
        self.assertEqual(row, original)
        for changes in ([], {}, None, [dict(scope='unknown',field='floor_height')]):
            self.assertEqual(package_change_kinds([{**row,'composition_changes':changes}]), ['NPC scene operand composition'])
        self.assertNotIn('source floor heights', package_change_kinds([{**row,'field':'npc.composed.facing_changes'}]))

    def test_texture_payload_report_is_detached_with_exact_pixel_identity(self):
        diff={'palette_words_changed':1,'pixel_indices_changed':1,'image_bytes_changed':1,
              'total_change_count':2,'changes_truncated':False,
              'changes':[{'kind':'palette_word','word_index':1,'before':10,'after':11},
                         {'kind':'pixel_index','x':1,'y':0,'before':13,'after':14}]}
        audit={'edits':[{'scene':'town01','semantic_id':'texture://town01/5/raw/0',
                         'field':'texture.tim','before_sha256':'a','after_sha256':'b',
                         'scope':'TIM-image-and-palette-payload-only','payload_changes':diff}],
               'validation':{},'overlays':[]}
        report=build_report(audit)
        row=report['changes'][0]
        self.assertEqual(row['payload_changes'],diff)
        self.assertEqual((row['before'],row['after']),('a','b'))
        row['payload_changes']['changes'][1]['after']=15
        self.assertEqual(diff['changes'][1]['after'],14)

    def test_model_vectors_are_detached_and_preserve_scalar_context(self):
        vector={'object_index':1,'kind':'normal','vector_index':0,'axis':'x',
                'byte_offset':3332,'before_value':0,'after_value':1}
        audit={'edits':[{'scene':'town01','semantic_id':'asset://town01/models/scene-tmd/0009',
                         'field':'model.shape','before_sha256':'a','after_sha256':'b',
                         'scope':'TMD-vertex-normal-XYZ-only','coordinate_changes':[vector]}],
               'validation':{},'overlays':[]}
        result=build_report(audit)
        self.assertEqual(result['change_count'],1)
        self.assertEqual(result['changes'][0]['coordinate_changes'],[vector])
        result['changes'][0]['coordinate_changes'][0]['after_value']=99
        self.assertEqual(vector['after_value'],1)

    def test_package_content_summary_keeps_all_emitted_families(self):
        edits=[{'scope':'shared-scene-animation-record'}, {'scope':'source-MAP-wall-bit-only'},
               {'scope':'TMD-vertex-normal-XYZ-only'}, {'scope':'script-movement-target-only'},
               {'scope':'shared-scene-animation-record'}]
        expected=['animation channels','model shapes','script movement targets','source collision walls']
        self.assertEqual(package_change_kinds(edits),expected)
        self.assertEqual(package_change_kinds(list(reversed(edits))),expected)
        self.assertEqual(package_change_kinds([]),[])
        self.assertEqual(package_change_kinds([{'scope':'unknown'}]),['other audited scene data'])
        self.assertEqual(package_change_kinds([{}]),['actor positions'])

    def test_snapshot_tracks_build_inputs_but_not_selection_or_templates(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(synthetic_scene())
            baseline = authored_state_key(project)
            project.select(None)
            self.assertIsNone(project.selected)
            self.assertEqual(authored_state_key(project), baseline)
            project.select("scene://fixture/actors/man-p1/0001")
            self.assertEqual(project.selected, "scene://fixture/actors/man-p1/0001")
            project.actor_templates = {"template": {"name": "Unused template"}}
            self.assertEqual(authored_state_key(project), baseline)
            for attribute, replacement in (("name", "different"), ("disc_path", "different"),
                    ("overrides", {"actor": {"Transform": {"position": {"x": 64}}}}),
                    ("texture_overrides", {"texture": {"asset_sha256": "a" * 64}}),
                    ("imports", {})):
                before = deepcopy(getattr(project, attribute))
                setattr(project, attribute, replacement)
                self.assertNotEqual(authored_state_key(project), baseline, attribute)
                setattr(project, attribute, before)
                self.assertEqual(authored_state_key(project), baseline, attribute)

    def test_real_edit_history_and_reopen_restore_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as raw:
            project = ProjectService(Path(raw))
            project.import_metadata(synthetic_scene())
            actor = "scene://fixture/actors/man-p1/0001"
            baseline = authored_state_key(project)
            project.command({"type": "set_transform", "entity_id": actor,
                             "position": {"x": 192}})
            edited = authored_state_key(project)
            self.assertNotEqual(edited, baseline)
            project.undo()
            self.assertEqual(authored_state_key(project), baseline)
            project.redo()
            self.assertEqual(authored_state_key(project), edited)
            project.command({"type": "create_actor_template", "entity_id": actor,
                             "name": "Saved position"})
            self.assertEqual(authored_state_key(project), edited)
            reopened = ProjectService.open(project.save())
            self.assertEqual(authored_state_key(reopened), edited)
            self.assertEqual(reopened.actor_templates, project.actor_templates)

    def test_animation_report_retains_frame_and_object_identity(self):
        edits=[{'scene':'fixture','semantic_id':'animation://fixture/scene-anm/0000',
                'field':'translation.x','before_value':0,'after_value':123,
                'scope':'shared-scene-animation-record','frame_index':frame,'object_index':2,'authored_owners':['actor-a','actor-b']}
               for frame in (1,3)]
        report=build_report({'edits':edits,'overlays':[],'validation':{}})
        self.assertEqual([(c['frame_index'],c['object_index']) for c in report['changes']],[(1,2),(3,2)])
        self.assertTrue(all(c['field']=='translation.x' for c in report['changes']))
        self.assertEqual(report['changes'][0]['authored_owners'],['actor-a','actor-b'])
        report['changes'][0]['authored_owners'].clear();self.assertEqual(edits[0]['authored_owners'],['actor-a','actor-b'])
        edits[0]['axis_owners']=['actor-b']
        exact=build_report({'edits':edits,'overlays':[],'validation':{}})['changes'][0]
        self.assertEqual(exact['authored_owners'],['actor-b']);self.assertEqual(exact['contributor_scope'],'axis')

    def test_transition_report_retains_navigable_resource_and_owner(self):
        owner = "scene://fixture/scripts/man-p2/0000"
        resource = "script://fixture/scripts/man-p2/0000/transition/0016"
        report = build_report({"edits": [{"scene": "fixture", "semantic_id": owner,
            "transition_id": resource, "field": "entry_x_encoded", "before_byte": 96,
            "after_byte": 97, "scope": "encoded-transition-entry-only"}],
            "overlays": [{"size": 10}], "validation": {"live_runtime": "not_run"}})
        change = report["changes"][0]
        self.assertEqual((change["asset_id"], change["owner_id"]), (resource, owner))
        self.assertEqual((change["before"], change["after"]), (96, 97))
        self.assertEqual(change["scope"], "encoded-transition-entry-only")

    def test_report_uses_audited_values_and_excludes_binary_spans(self):
        audit = {"edits": [
            {"scene": "fixture", "semantic_id": "actor", "field": "position.x",
             "before_value": 128, "after_value": 192, "before_byte": 1, "after_byte": 2},
            {"scene": "fixture", "semantic_id": "actor", "run_id": "run", "field": "dialogue.text",
             "before_hex": b"Before".hex(), "after_hex": b"After ".hex()},
            {"scene": "other", "semantic_id": "texture", "field": "texture.tim",
             "before_sha256": "a" * 64, "after_sha256": "b" * 64}],
            "overlays": [{"size": 20}, {"size": 30}], "validation": {"live_runtime": "not_run"}}
        report = build_report(audit)
        self.assertEqual((report["change_count"], report["scene_count"], report["overlay_bytes"]), (3, 2, 50))
        self.assertEqual(report["changes"][0]["before"], 128)
        self.assertEqual(report["changes"][1]["asset_id"], "run")
        self.assertEqual(report["changes"][1]["owner_id"], "actor")
        self.assertEqual(report["changes"][1]["after"], "After ")
        self.assertEqual(report["changes"][2]["after"], "b" * 64)
        self.assertNotIn("before_hex", str(report))
        report["validation"]["live_runtime"] = "changed"
        self.assertEqual(audit["validation"]["live_runtime"], "not_run")
        audit["edits"] = []; audit["overlays"] = []
        self.assertEqual(build_report(audit)["change_count"], 0)


if __name__ == "__main__":
    unittest.main()

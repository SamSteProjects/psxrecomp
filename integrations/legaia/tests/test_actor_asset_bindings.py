from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk.project import ProjectService
from sdk.actor_asset_bindings import components
from sdk.project_assets import assemble
from test_project_appearance import appearance_scene


class ActorAssetBindings(unittest.TestCase):
    def test_authored_appearance_preserves_retail_model_and_distinct_initial_clips(self):
        with tempfile.TemporaryDirectory() as directory:
            project=ProjectService(Path(directory));document=appearance_scene();project.import_metadata(document)
            actor,donor=document['actors'];identifier=actor['semantic_id']
            with patch.object(project,'appearance_options',return_value={'supported':True,'options':[{'donor_entity_id':donor['semantic_id']}] }):
                project.command({'type':'set_actor_appearance','entity_id':identifier,'donor_entity_id':donor['semantic_id']})
            before=deepcopy(project._document());imports=deepcopy(project.imports);history=deepcopy(project.undo_stack)
            bindings=components(project,actor,document)
            self.assertEqual(bindings['ActorAppearance']['imported']['asset_id'],'asset://fixture/model/0')
            self.assertEqual(bindings['ActorAppearance']['effective']['asset_id'],'asset://fixture/model/1')
            self.assertEqual(bindings['ActorAppearance']['authored'],{'donor_entity_id':donor['semantic_id']})
            self.assertEqual(bindings['ActorAnimation']['imported']['animation_asset_id'],'animation://fixture/scene-anm/0001')
            self.assertEqual(bindings['ActorAnimation']['base']['animation_asset_id'],'animation://fixture/scene-anm/0002')
            self.assertEqual(bindings['ActorAnimation']['effective'],bindings['ActorAnimation']['base'])
            report=assemble(project,{})
            record=next(a for a in report['assets'] if a['id']==identifier)['variants'][0]['record']
            self.assertEqual(record['components'],bindings)
            record['components']['ActorAppearance']['authored']['donor_entity_id']='changed'
            self.assertEqual(project._document(),before);self.assertEqual(project.imports,imports);self.assertEqual(project.undo_stack,history)

"""Native initial header composition preserves edits and rejects overlap."""
from hashlib import sha256
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from importer.animation import animation_record_ranges
from importer.core import parse_man
from importer.serialization import patch_man_positions
from sdk.allocated_animation_build import patch_assignments
from sdk.project import ProjectError
from test_allocated_man_assignment import allocated
from test_importer_man_assignments import fixture


class AllocatedAnimationBuild(unittest.TestCase):
    def test_merge_preserves_placement_and_rejects_header_overlap(self):
        context,baseline=fixture();bank=allocated(context)
        a,b=animation_record_ranges(bank)[2]
        value=dict(record_id='retained-id',record_sha256=sha256(bank[a:b]).hexdigest(),model_asset_id='model-5')
        project=SimpleNamespace(disc_path='fixture',imports={'scene':dict(scene=dict(name='synthetic'),actors=[
            dict(semantic_id='target',source_record=dict(record_index=1)),
            dict(semantic_id='donor',source_record=dict(record_index=2))])})
        actor=parse_man(baseline).actors[0]
        positioned,_=patch_man_positions(baseline,'synthetic',{1:dict(x=actor.world_x+64)})
        with patch('sdk.allocated_animation_build.compose',return_value=(bank,dict(allocated_records=[dict(record_id='retained-id',record_index=2)]))), \
             patch('sdk.allocated_animation_build.validate_binding',return_value=dict(channel_owner_entity_id='donor')), \
             patch('sdk.allocated_animation_build.load_man_assignment_context',return_value=context):
            result,audit=patch_assignments(project,'scene',{'target':value},baseline,positioned)
            after=parse_man(result).actors[0]
            self.assertEqual((after.world_x,after.model_index,after.animation_id),(actor.world_x+64,5,3))
            self.assertTrue(all(row['record_id']=='retained-id' for row in audit))
            overlapping=bytearray(positioned);overlapping[audit[0]['decoded_byte_offset']]^=1
            with self.assertRaisesRegex(ProjectError,'overlaps'):
                patch_assignments(project,'scene',{'target':value},baseline,bytes(overlapping))
            with self.assertRaisesRegex(ProjectError,'original MAN layout'):
                patch_assignments(project,'scene',{'target':value},baseline,positioned+b'x')


if __name__=='__main__':unittest.main()

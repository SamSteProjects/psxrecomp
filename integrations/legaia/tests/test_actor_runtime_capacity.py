"""Known retail actor-pool lower bound, not script/gameplay capacity claims."""
import os
from unittest import TestCase, skipUnless
from importer.actor_runtime_capacity import qualify_actor_pool, assess_initial_placement_capacity, EXECUTABLE_SHA256
from importer.core import ImportError


class ActorPoolAssessmentTests(TestCase):
    def profile(self):
        return dict(schema_version='legaia.actor-pool-source.v1', executable_sha256=EXECUTABLE_SHA256,
                    node_capacity=143, node_stride=216)

    def test_lower_bound_boundary_and_unknown_remaining_consumers(self):
        for count, remaining in ((0, 142), (54, 89), (143, 0)):
            result = assess_initial_placement_capacity(self.profile(), [36, count, 39])
            self.assertEqual(result['remaining_after_placement_lower_bound'], remaining)
            self.assertFalse(result['runtime_allocation_verified'])
            self.assertEqual(result['other_scene_and_script_demand'], 'unverified')
        with self.assertRaisesRegex(ImportError, 'at least 144 nodes'):
            assess_initial_placement_capacity(self.profile(), [36, 144, 39])
        for counts in ([36, True, 39], [36, -1, 39], [36, 54], [36, 32768, 39]):
            with self.assertRaises(ImportError): assess_initial_placement_capacity(self.profile(), counts)
        with self.assertRaises(ImportError): qualify_actor_pool(b'PS-X EXE' + bytes(2048))

    @skipUnless(os.environ.get('LEGAIA_DISC_BIN'), 'requires private retail source')
    def test_complete_retail_executable_qualification_and_changed_source_rejection(self):
        from importer.pipeline import _disc_context
        with _disc_context(os.environ['LEGAIA_DISC_BIN']) as (image, *_):
            executable = image.read_file(image.find('SCUS_942.54'))
        profile = qualify_actor_pool(executable)
        self.assertEqual((profile['node_capacity'], profile['node_stride']), (143, 216))
        self.assertEqual(len(profile['functions']), 7)
        altered = bytearray(executable); altered[2048] ^= 1
        with self.assertRaises(ImportError): qualify_actor_pool(bytes(altered))

"""Browser yaw matrices agree with independent SDK source rotation projection."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from sdk.scene_preview import environment_matrix


class EnvironmentYawGoldenTests(unittest.TestCase):
    def test_browser_matrices_match_sdk_for_compound_retail_axes_and_wrapped_angles(self):
        module = (Path(__file__).resolve().parents[1] / 'editor/environment-rotation.js').as_uri()
        node = shutil.which('node') or 'C:/Program Files/nodejs/node.exe'
        cases = [dict(position=dict(x=128, y=-32, z=256), rotation_psx=dict(x=x, y=y, z=z))
                 for x, y, z in [(0, 0, 0), (0, 1024, 0), (256, 300, 768),
                                 (4095, 4000, 4096), (-1024, 900, -512)]]
        original = deepcopy(cases)
        script = f"""import {{environmentYawMatrix}} from {json.dumps(module)};
let input='';for await(const chunk of process.stdin)input+=chunk;
const cases=JSON.parse(input);console.log(JSON.stringify(cases.map(c=>environmentYawMatrix({{effective_transform:c}},c.rotation_psx.y))));"""
        result = subprocess.run([node, '--input-type=module', '-e', script], input=json.dumps(cases),
                                text=True, capture_output=True, timeout=20, check=True)
        matrices = json.loads(result.stdout)
        self.assertEqual(len(matrices), len(cases))
        for transform, actual in zip(cases, matrices):
            with self.subTest(rotation=transform['rotation_psx']):
                expected = environment_matrix(transform)
                self.assertEqual(len(actual), 16)
                for value, golden in zip(actual, expected):
                    self.assertAlmostEqual(value, golden, places=12)
                self.assertEqual([actual[index] for index in (3, 7, 11)], [128, 32, 256])
        self.assertEqual(cases, original)


if __name__ == '__main__':
    unittest.main()

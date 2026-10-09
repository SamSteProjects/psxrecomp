"""Exercise all eleven native family decoders in the combined editor comparison."""
import json
import subprocess
from pathlib import Path
import unittest
import test_controller_party_selector_workflow as fixture
from sdk.controller_snapshots import snapshot
from sdk.controller_system_flags import state_key

class ControllerOperandComparison(unittest.TestCase):
    def test_eleven_families_and_composed_changes(self):
        case=fixture.ControllerPartySelectorWorkflow();case.setUp()
        try:
            for changed in [False,True]:
                if changed:
                    case.apply({'party_selector':7});case.selector({'index':4095});case.branch({'target_pc':7})
                key=state_key(case.p);families=snapshot(case.p,fixture.OWNER,key)['families']
                path=Path(case.temp.name)/'comparison.json'
                path.write_text(json.dumps(dict(owner=fixture.OWNER,context=dict(projectPath=case.temp.name,sceneId=case.p.active_scene,mode='edit',scriptKey=key),families=families,count=11,changed=3 if changed else 0)),encoding='utf-8')
                subprocess.run(['C:/Program Files/nodejs/node.exe',str(Path(__file__).with_suffix('.mjs')),str(path)],check=True)
        finally:
            case.doCleanups()

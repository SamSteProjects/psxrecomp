from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import struct,tempfile
from sdk.project import ProjectService,ProjectError
from sdk.worldmap_authoring import state_key
from sdk.worldmap_current_man import inspect
from test_worldmap_scripted_placement_binding import ledger
from test_project_workflow import synthetic_scene


class CurrentWorldManTests(TestCase):
    def test_complete_height_composition_read_only_and_stale_refusal(self):
        _,_,man,_,_,_,_=ledger();provenance=dict(source_disc_sha256='b'*64,source_man_sha256=sha256(man).hexdigest())
        inputs=(man,{},provenance,8,0,{},b'',None,man,[])
        with tempfile.TemporaryDirectory() as root:
            p=ProjectService(Path(root));p.import_metadata(synthetic_scene());p.imports['scene://map01']=dict(scene=dict(name='map01'))
            p.overrides['scene://map01']={'FloorHeights':dict(source_sha256=sha256(man).hexdigest(),edits=[dict(tier=0,height=-32768),dict(tier=15,height=32767)])}
            held=deepcopy(p._document());key=state_key(p)
            with patch('sdk.worldmap_current_man.context',return_value=inputs),patch.object(p,'_validate_floor_heights'):
                value=inspect(p,'map01',key);expected=bytearray(man);struct.pack_into('<h',expected,2,-32768);struct.pack_into('<h',expected,32,32767)
                self.assertEqual(b64decode(value['current_man_base64']),bytes(expected));self.assertEqual(b64decode(value['retail_man_base64']),man)
                self.assertEqual(value['records'],[]);self.assertEqual(p._document(),held)
            with patch('sdk.worldmap_current_man.context',side_effect=AssertionError('stale must refuse before reading')):
                with self.assertRaises(ProjectError):inspect(p,'map01','0'*64)
                p.mode='live'
                with self.assertRaises(ProjectError):inspect(p,'map01',state_key(p))

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from importer.script_inspection import _instruction
from importer.core import ImportError
from importer.controller_branches import ControllerBranchAuthoringContext
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from test_controller_branches import source,OWNER
from test_project_workflow import synthetic_scene
from sdk.project import ProjectService
from sdk.controller_selector_build import compose

class ControllerRectBranch(unittest.TestCase):
 def test_ordinary_extended_bounds_and_relative_edges(self):
  for header in [b'\x4c',b'\xcc\x07']:
   word_pc=len(header)+5;raw=(-word_pc)&65535
   data=header+b'\xe4\x00\x80\x7f\xff'+raw.to_bytes(2,'little')
   node=_instruction(data,0)
   self.assertEqual(node['length'],len(header)+7)
   self.assertEqual(node['operands']['bounds_inclusive'],dict(x_min=32,z_min=96,x_max=16352,z_max=16416))
   self.assertEqual(node['operands']['target_word_pc'],word_pc);self.assertEqual(node['operands']['target_pc'],0)
   self.assertEqual(node['successors'],[dict(pc=len(data),condition='dispatch_position_inside_rect'),dict(pc=0,condition='dispatch_position_outside_rect')])
   self.assertEqual(node['operands']['actor_binding'],'dispatch_context_unresolved');self.assertEqual(node['operands']['runtime_effect'],'not_evaluated')
   for length in range(len(header)+1,len(data)):
    with self.assertRaises(ImportError):_instruction(data[:length],0)
 def test_complete_literal_authoring_and_build_keep_rect_bytes(self):
  src,man=source(b'\x4c\xe4\x00\x80\x7f\xff\xfa\xff\x26\xf7\xff')
  ctx=ControllerBranchAuthoringContext(src);identity=OWNER.replace('scene://','script://',1)+'/branch/0005'
  options=ctx.options(OWNER);target=next(t for t in options['targets'] if t['semantic_id']==identity)
  self.assertEqual(target['target_pc'],5);self.assertEqual(target['operand_pc'],11)
  expected=bytearray(man);expected[68:70]=b'\x02\x00'
  result,audit=ctx.patch({identity:{'target_pc':13}});self.assertEqual(result,bytes(expected));self.assertEqual(src._man,man)
  self.assertEqual(ctx.patch({identity:{'target_pc':5}}),(man,[]))
  with tempfile.TemporaryDirectory() as folder:
   p=ProjectService(Path(folder));p.import_metadata(synthetic_scene());p.overrides[OWNER]={'ControllerBranches':dict(source_record_sha256=sha256(src.verified_record(OWNER)[1]).hexdigest(),entries={identity:{'target_pc':13}})}
   before=deepcopy(p._document())
   with patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=ControllerSystemFlagAuthoringContext(src)):
    built,receipts=compose(p,'scene://fixture',man,man)
   self.assertEqual(built,bytes(expected));self.assertEqual(len(receipts),1);self.assertEqual(p._document(),before)

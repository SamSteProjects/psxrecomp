from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from importer.script_inspection import inspect_record,_instruction
from importer.controller_branches import ControllerBranchAuthoringContext
from importer.controller_system_flags import ControllerSystemFlagAuthoringContext
from importer.core import ImportError
from sdk.controller_selector_build import compose
from sdk.project import ProjectService
from test_project_workflow import synthetic_scene
from test_controller_branches import source,OWNER,ID


class ActorLookupBranch(unittest.TestCase):
    def test_relative_words_context_selector_limits_and_truncation(self):
        for header,context in ((b'\x4c',None),(b'\xcc\x07',7)):
            for selector in (0,255):
                for raw in (0,1,32767,32768,65535):
                    data=header+b'\xeb'+bytes([selector])+raw.to_bytes(2,'little')
                    node=_instruction(data,0);at=len(header)+2;target=(at+raw)&65535
                    self.assertEqual(node['mnemonic'],'ACTOR_LOOKUP_BRANCH')
                    self.assertEqual(node['length'],len(data));self.assertEqual(node['target_context'],context)
                    self.assertEqual(node['operands']['target_word_pc'],at)
                    self.assertEqual(node['operands']['target_pc'],target)
                    self.assertEqual(node['operands']['actor_selector'],selector)
                    self.assertEqual(node['successors'],[dict(pc=len(data),condition='actor_lookup_found'),dict(pc=target,condition='actor_lookup_missing')])
                    self.assertEqual(node['operands']['actor_binding'],'runtime_lookup_unresolved')
                    for length in range(1,len(data)):
                        with self.assertRaises(ImportError):_instruction(data[:length],0)
        # A backwards miss edge returns to its own opcode, while found advances.
        self.assertFalse(inspect_record(b'\x4c\xeb\xff\xfd\xff\x24',0)['stops'])

    def test_normal_extended_authoring_and_build_keep_literal_complete_man(self):
        for header in (b'\x4c',b'\xcc\x07'):
            at=5+len(header)+2;fallthrough=5+len(header)+4
            script=header+b'\xeb\xff'+((5-at)&65535).to_bytes(2,'little')+b'\x24'
            src,man=source(script);ctx=ControllerBranchAuthoringContext(src)
            target=next(t for t in ctx.options(OWNER)['targets'] if t['pc']==5)
            self.assertEqual(target['condition'],'actor_lookup_missing');self.assertEqual(target['values'],{'target_pc':5})
            changed,audit=ctx.patch({ID:{'target_pc':fallthrough}})
            expected=bytearray(man);expected[57+at:59+at]=((fallthrough-at)&65535).to_bytes(2,'little')
            self.assertEqual(changed,bytes(expected));self.assertEqual(changed[57+5:57+at],man[57+5:57+at]);self.assertEqual(ctx.patch({ID:{'target_pc':5}}),(man,[]))
            with tempfile.TemporaryDirectory() as tmp:
                p=ProjectService(Path(tmp));p.import_metadata(synthetic_scene());p.overrides[OWNER]={'ControllerBranches':dict(source_record_sha256=sha256(src.verified_record(OWNER)[1]).hexdigest(),entries={ID:{'target_pc':fallthrough}})}
                with patch('sdk.controller_selector_build.load_controller_system_flag_context',return_value=ControllerSystemFlagAuthoringContext(src)):
                    built,receipts=compose(p,'scene://fixture',man,man)
                self.assertEqual(built,bytes(expected));self.assertEqual(len(receipts),1);self.assertEqual(receipts[0]['condition'],'actor_lookup_missing')
                self.assertEqual(receipts[0]['byte_length'],2);self.assertEqual(receipts[0]['after_target_pc'],fallthrough)
        # Retain unrelated unsupported bytes as an explicit stop, never recover by scanning.
        report=inspect_record(b'\x4c\xeb\x00\x02\x00\x4c\xe7'+bytes(6),0)
        self.assertEqual(report['status'],'partial');self.assertEqual(len(report['instructions']),1)
        self.assertIn('0xe7',report['stops'][0]['reason'])

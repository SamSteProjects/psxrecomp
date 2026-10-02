"""Source boundary, composed operand and retail carrier proofs for branch words."""
from copy import deepcopy
from hashlib import sha256
import os
import struct
import unittest

from importer.branch_authoring import BranchAuthoringContext, validate_branch_values
from importer.core import ImportError, decompress_lzs, parse_man
from importer.dialogue_authoring import DialogueAuthoringContext, load_dialogue_authoring_context
from importer.man_actor_structure import append_actor_donor
from importer.man_layout import read_man_layout
from importer.pipeline import _disc_context
from importer.script_inspection import inspect_record
from importer.serialization import serialize_man_decoded
from test_importer_dialogue_authoring import ACTOR, fixture, literals

END = b'\x3f\0\0\x06town01\x01\x02\x03opaque'
LOOP = b'\x26\x02\0\x21\x26\xfb\xff'


def family_script(mnemonic, extended=False, variant=0):
    """Independent packet positions and word encoding against P1 entry5."""
    opcode, prefix = {
        'JMP_REL': (0x26, b''),
        'COND_JMP': (0x42, bytes((variant, 0x82))),
        'BBOX_TEST': (0x4d, b'\x04\x03\x02\x01'),
        'FLAG_WORD_BRANCH': (0x4c, bytes((0xa0 + variant, 0xe3))),
        'SYSFLAG_TEST': (0x70 + variant, b'\x02'),
    }[mnemonic]
    header = bytes((opcode | 0x80, 0xf8)) if extended else bytes((opcode,))
    operand = 5 + len(header) + len(prefix)
    fallthrough = operand + 2
    target = fallthrough + 1
    first = header + prefix + ((target - operand) & 0xffff).to_bytes(2, 'little')
    closing_pc = fallthrough + 2
    closing = b'\x26' + ((5 - (closing_pc + 1)) & 0xffff).to_bytes(2, 'little')
    return first + b'\x21\x21' + closing, operand, target, closing_pc


def p2_fixture(script):
    counts = (1, 2, 1); base = 0x2b + 3 * sum(counts)
    actor = b'\0\1\1\2\3\x21\x26\xfe\xff'
    p2 = b'\0\0\0\0' + script
    section = 8 + len(actor) + len(p2)
    man = bytearray(base + section + 18)
    struct.pack_into('<hhh', man, 0x22, *counts)
    man[0x28:0x2b] = section.to_bytes(3, 'little')
    for i, start in enumerate((0, 4, 8, 8 + len(actor))):
        man[0x2b + 3*i:0x2e + 3*i] = start.to_bytes(3, 'little')
    man[base + 8:base + 8 + len(actor)] = actor
    man[base + 8 + len(actor):base + section] = p2
    man = bytes(man)
    return DialogueAuthoringContext('fixture', man, literals(man), {'synthetic':True}), man


class BranchAuthoringTests(unittest.TestCase):
    def test_five_families_preserve_condition_bytes_and_context_and_allow_changed_edges(self):
        variants = [('JMP_REL',0), ('COND_JMP',0), ('COND_JMP',1), ('BBOX_TEST',0)]
        variants += [('FLAG_WORD_BRANCH',v) for v in range(3)]
        variants += [('SYSFLAG_TEST',v) for v in (0,7,15)]
        for mnemonic, variant in variants:
            for extended in (False, True):
                with self.subTest(mnemonic=mnemonic, variant=variant, extended=extended):
                    script, operand, target, closing = family_script(mnemonic, extended, variant)
                    source, man = fixture(script); context = BranchAuthoringContext(source)
                    options = context.options(ACTOR)
                    if mnemonic == 'SYSFLAG_TEST' and extended:
                        self.assertFalse(options['supported'])
                        with self.assertRaises(ImportError):
                            context.patch({'script://fixture/actors/man-p1/0001/branch/0005':{'target_pc':5}})
                        continue
                    self.assertTrue(options['supported'],options['reason'])
                    row = next(r for r in options['targets'] if r['pc']==5)
                    self.assertEqual(row['operand_pc'],operand);self.assertEqual(row['target_pc'],target)
                    self.assertEqual(row['target_context'],0xf8 if extended else None)
                    self.assertEqual(context.patch({row['semantic_id']:row['values']}),(man,[]))
                    changed,audit=context.patch({row['semantic_id']:{'target_pc':closing}})
                    expected=bytearray(man);at=row['decoded_byte_offset']
                    expected[at:at+2]=((closing-operand)&0xffff).to_bytes(2,'little')
                    self.assertEqual(changed,bytes(expected));self.assertEqual(len(audit),1)
                    self.assertEqual(audit[0]['scope'],'script-branch-target-only')
                    self.assertEqual(audit[0]['field'],'script.branch_target')
                    self.assertEqual((audit[0]['before_value'],audit[0]['after_value']),(target,closing))
                    self.assertEqual(audit[0]['before_hex'],man[at:at+2].hex())
                    self.assertEqual(audit[0]['after_hex'],changed[at:at+2].hex())
                    self.assertEqual(audit[0]['source_record_sha256'],row['source_record_sha256'])
                    self.assertTrue(audit[0]['changed_bytes'])
                    self.assertEqual({r['decoded_byte_offset'] for r in audit[0]['changed_bytes']},
                                     {i for i,(a,b) in enumerate(zip(man,changed)) if a!=b})
                    self.assertFalse(context.inspect_owner(ACTOR,changed)['stops'])
                    self.assertEqual(read_man_layout(changed),read_man_layout(man))
                    self.assertEqual(parse_man(changed),parse_man(man))

    def test_unreachable_source_spans_are_retained_and_multiple_edits_are_atomic(self):
        source,man=fixture(LOOP);context=BranchAuthoringContext(source);rows=context.options(ACTOR)['targets']
        first=next(row for row in rows if row['pc']==5);last=next(row for row in rows if row['pc']==9)
        changed,audit=context.patch({first['semantic_id']:{'target_pc':9}})
        self.assertEqual(audit[0]['unreachable_source_pcs'],[8])
        self.assertEqual(context.inspect_owner(ACTOR,changed)['unreachable_source_pcs'],[8])
        offset=source._actors[ACTOR].byte_offset
        self.assertEqual(changed[offset+8],man[offset+8])
        edits={first['semantic_id']:{'target_pc':9},last['semantic_id']:{'target_pc':8}}
        both,audits=context.patch(edits)
        self.assertEqual(context.patch(dict(reversed(list(edits.items())))),(both,audits))
        self.assertTrue(all(row['unreachable_source_pcs']==[] for row in audits))
        self.assertEqual(len(audits),2)
        self.assertEqual(context._man,man)

    def test_actual_atomic_mes_destinations_remain_valid_without_glyph_or_interior_targets(self):
        # Source entry at5, message at6, branch at10 targets that exact message.
        source,man=fixture(b'\x21\x1fHi\0\x26\xfb\xff')
        context=BranchAuthoringContext(source);options=context.options(ACTOR)
        self.assertIn({'pc':6,'mnemonic':'MES_SEGMENT'},options['destinations'])
        row=options['targets'][0]
        self.assertEqual(context.patch({row['semantic_id']:{'target_pc':6}}),(man,[]))
        changed,_=context.patch({row['semantic_id']:{'target_pc':5}})
        self.assertFalse(context.inspect_owner(ACTOR,changed)['stops'])
        for pc in (7,8,9):
            with self.assertRaises(ImportError):context.patch({row['semantic_id']:{'target_pc':pc}})

    def test_composed_all_existing_operand_families_survive_new_edges(self):
        from importer.flag_authoring import FlagAuthoringContext
        from importer.wait_authoring import WaitAuthoringContext
        from importer.movement_authoring import MovementAuthoringContext
        from importer.facing_authoring import FacingAuthoringContext
        from importer.transition_authoring import TransitionAuthoringContext
        from importer.serialization import patch_man_positions
        # Conditional taken path reaches transition; fallthrough reaches all
        # scalar/text edits and loops. Retargeting makes transition dormant.
        body=b'\x2e\xe2\x4a\x02\0\x23\x01\x02\x38\x81\0\x1fHello\0'
        jump_pc=10+len(body)
        tail=b'\x26'+((5-(jump_pc+1))&0xffff).to_bytes(2,'little')
        transition_pc=jump_pc+3
        script=b'\x42\0\x02'+((transition_pc-8)&0xffff).to_bytes(2,'little')+body+tail+END
        source,man=fixture(script);context=BranchAuthoringContext(source)
        composed,placement=patch_man_positions(man,'fixture',{1:{'x':384}})
        components=[(FlagAuthoringContext(source),'targets',{'bit':3}),
                    (WaitAuthoringContext(source),'targets',{'duration_ticks':7}),
                    (MovementAuthoringContext(source),'targets',{'x':384}),
                    (FacingAuthoringContext(source),'targets',{'sector':3}),
                    (TransitionAuthoringContext(source),'transitions',{'entry_x_encoded':9})]
        previous=list(placement)
        for writer,key,values in components:
            target=writer.options(ACTOR)[key][0]
            changed,audit=writer.patch({target['semantic_id']:values})
            result=bytearray(composed)
            for row in audit:
                at=row['decoded_byte_offset'];width=row.get('byte_length',1)
                result[at:at+width]=changed[at:at+width]
            composed=bytes(result);previous+=audit
        run=source.options(ACTOR)['runs'][0]
        changed,audit=source.patch({run['semantic_id']:'World'})
        result=bytearray(composed)
        for row in audit:
            at=row['decoded_byte_offset'];result[at:at+row['byte_length']]=changed[at:at+row['byte_length']]
        composed=bytes(result);previous+=audit
        row=next(r for r in context.options(ACTOR)['targets'] if r['pc']==5)
        final,branch_audit=context.patch_composed(composed,{row['semantic_id']:{'target_pc':10}})
        allowed={row['decoded_byte_offset'],row['decoded_byte_offset']+1}
        self.assertTrue(all(a==b or at in allowed for at,(a,b) in enumerate(zip(composed,final))))
        self.assertIn(transition_pc,branch_audit[0]['unreachable_source_pcs'])
        self.assertEqual(branch_audit[0]['effective_record_sha256'],
                         sha256(composed[source._actors[ACTOR].byte_offset:source._actors[ACTOR].byte_offset+source._actors[ACTOR].byte_length]).hexdigest())
        for change in previous:
            at=change['decoded_byte_offset'];width=change.get('byte_length',1)
            self.assertEqual(final[at:at+width],composed[at:at+width])
        self.assertFalse(context.inspect_owner(ACTOR,final)['stops'])

    def test_appended_rebinding_preserves_donor_clone_and_supports_partition_two(self):
        for partition in (1,2):
            with self.subTest(partition=partition):
                if partition==1:source,man=fixture(LOOP);owner=ACTOR
                else:
                    # P2 entry4, first jump→7, NOP7, closing jump8→4.
                    source,man=p2_fixture(b'\x26\x02\0\x21\x26\xfb\xff')
                    owner='scene://fixture/scripts/man-p2/0000'
                context=BranchAuthoringContext(source);row=context.options(owner)['targets'][0]
                dest=next(r['pc'] for r in context.options(owner)['destinations'] if r['pc']!=row['target_pc'])
                appended,_=append_actor_donor(man,sha256(man).hexdigest(),1)
                before=read_man_layout(appended);changed,audit=context.patch_appended(appended,{row['semantic_id']:{'target_pc':dest}})
                self.assertEqual(read_man_layout(changed),before)
                self.assertEqual({i for i,(a,b) in enumerate(zip(appended,changed)) if a!=b},
                                 {r['decoded_byte_offset'] for r in audit[0]['changed_bytes']})
                self.assertEqual(audit[0]['source_decoded_byte_offset'],row['decoded_byte_offset'])
                clone=next(r for r in before['records'] if r['partition']==1 and r['record_index']==2)
                start,size=clone['byte_offset'],clone['byte_length']
                self.assertEqual(changed[start:start+size],appended[start:start+size])
                with self.assertRaises(ImportError):context.patch_composed(appended,{row['semantic_id']:{'target_pc':dest}})

    def test_guards_reject_aliases_stops_interiors_unknowns_and_shapes(self):
        source,man=fixture(LOOP);context=BranchAuthoringContext(source);row=context.options(ACTOR)['targets'][0];key=row['semantic_id']
        for values in ({}, {'target_pc':True},{'target_pc':-1},{'target_pc':32768},
                       {'target_pc':8.0},{'target_pc':8,'delta':2},[],{'target_pc':6},{'target_pc':7},{'target_pc':4},{'target_pc':12}):
            with self.subTest(values=values),self.assertRaises(ImportError):context.patch({key:values})
        for invalid in ({'bad':{'target_pc':8}}, {key.replace('fixture','elsewhere'):{'target_pc':8}},
                        {key.replace('/0001/','/0000/'):{'target_pc':8}}, {key.replace('0005','0006'):{'target_pc':8}}, [],
                        {f'script://fixture/actors/man-p1/0001/branch/{i:04x}':{'target_pc':8} for i in range(1025)}):
            with self.assertRaises(ImportError):context.patch(invalid)
        with self.assertRaises(ImportError):context.patch({key:{'target_pc':9}},original=man[:-1])
        alias,_=fixture(LOOP,alias=True)
        with self.assertRaises(ImportError):BranchAuthoringContext(alias).options(ACTOR)
        stopped,_=fixture(b'\x26\x02\0\x20')
        self.assertFalse(BranchAuthoringContext(stopped).options(ACTOR)['supported'])
        for values in ({'target_pc':True},{'target_pc':32768}):
            with self.assertRaises(ImportError):validate_branch_values(values)
        for owner in ([], {}, None, 1):
            with self.assertRaises(ImportError):context.options(owner)

    def test_candidate_preimages_layout_conditions_new_paths_and_original_anchors_reject(self):
        source,man=fixture(LOOP+b'\x21\x26\xfe\xff');context=BranchAuthoringContext(source)
        row=context.options(ACTOR)['targets'][0];key=row['semantic_id'];at=row['decoded_byte_offset'];offset=source._actors[ACTOR].byte_offset
        invalid=[]
        candidate=bytearray(man);candidate[at]^=1;invalid.append(bytes(candidate))
        candidate=bytearray(man);candidate[offset+8]=0x24;invalid.append(bytes(candidate))
        candidate=bytearray(man);candidate[0x2b]^=1;invalid.append(bytes(candidate))
        candidate=bytearray(man);candidate[offset]=1;invalid.append(bytes(candidate))
        invalid += [man[:-1],man+b'\0',bytearray(man)]
        for candidate in invalid:
            with self.assertRaises(ImportError):context.patch_composed(candidate,{key:{'target_pc':9}})
        # Retargeting forged current bytes to a valid-looking opaque tail is
        # rejected even when that tail forms a complete supported loop.
        candidate=bytearray(man);candidate[at:at+2]=((12-row['operand_pc'])&0xffff).to_bytes(2,'little')
        with self.assertRaisesRegex(ImportError,'new|opaque'):
            context.inspect_owner(ACTOR,bytes(candidate))
        # Even a dormant original branch cannot gain an opaque destination.
        # The first jump loops at5, hiding the closing branch from rescanning.
        candidate=bytearray(man);candidate[at:at+2]=b'\xff\xff'
        candidate[offset+10:offset+12]=(2).to_bytes(2,'little')
        with self.assertRaisesRegex(ImportError,'unreachable branch'):
            context.inspect_owner(ACTOR,bytes(candidate))
        script,_,_,closing=family_script('COND_JMP')
        source,man=fixture(script);context=BranchAuthoringContext(source);row=context.options(ACTOR)['targets'][0]
        at=source._actors[ACTOR].byte_offset+6
        candidate=bytearray(man);candidate[at]=1
        with self.assertRaisesRegex(ImportError,'immutable'):
            context.patch_composed(bytes(candidate),{row['semantic_id']:{'target_pc':closing}})

    def test_options_and_reports_are_detached_and_noop_keeps_original_encoding(self):
        source,man=fixture(LOOP);context=BranchAuthoringContext(source);saved=context.options(ACTOR)
        altered=context.options(ACTOR);altered['targets'][0]['values']['target_pc']=123
        altered['inspection']['instructions'].clear();altered['source']['limitations'].clear()
        self.assertEqual(context.options(ACTOR),saved)
        self.assertEqual(context.patch({}),(man,[]))
        self.assertEqual(context.patch_composed(man,{}),(man,[]))
        inspected=context.inspect_owner(ACTOR);inspected['instructions'].clear()
        self.assertTrue(context.inspect_owner(ACTOR)['instructions'])
        row=saved['targets'][0];changed,audit=context.patch({row['semantic_id']:{'target_pc':9}})
        audit[0]['changed_bytes'].clear()
        self.assertTrue(context.patch({row['semantic_id']:{'target_pc':9}})[1][0]['changed_bytes'])

    def test_target32767_is_a_real_source_boundary_and32768_is_rejected(self):
        # Two source instructions with a large opaque gap, not a magic scan.
        script=bytearray(32770-5)
        script[0]=0x26;script[1:3]=(32767-6).to_bytes(2,'little')
        script[32767-5]=0x26;script[32768-5:32770-5]=((5-32768)&0xffff).to_bytes(2,'little')
        source,man=fixture(bytes(script));context=BranchAuthoringContext(source)
        row=context.options(ACTOR)['targets'][0]
        self.assertEqual(row['target_pc'],32767)
        self.assertEqual(context.patch({row['semantic_id']:{'target_pc':32767}}),(man,[]))
        with self.assertRaises(ImportError):context.patch({row['semantic_id']:{'target_pc':32768}})

    def test_terminal_or_out_of_domain_source_targets_are_not_offered_as_writable_rows(self):
        # The inspection walker accepts an explicit end-of-record exit, but
        # authoring offers only retained instruction/MES starts.
        source,_=fixture(b'\x26\x02\0')
        options=BranchAuthoringContext(source).options(ACTOR)
        self.assertFalse(options['supported']);self.assertFalse(options['targets'])
        # A reached node above signed-PC range remains decoded evidence, not
        # an authoring destination or a writable source branch.
        script=bytearray(32771-5)
        script[0]=0x26;script[1:3]=(32768-6).to_bytes(2,'little')
        script[32768-5]=0x26;script[32769-5:32771-5]=((5-32769)&0xffff).to_bytes(2,'little')
        source,_=fixture(bytes(script));options=BranchAuthoringContext(source).options(ACTOR)
        self.assertFalse(options['supported']);self.assertEqual(options['destinations'],[{'pc':5,'mnemonic':'JMP_REL'}])


@unittest.skipUnless(os.environ.get('LEGAIA_DISC_BIN'),'requires private retail disc')
class RetailBranchAuthoringTests(unittest.TestCase):
    def test_fresh_compressed_and_raw_sources_roundtrip_without_layout_growth(self):
        path=os.environ['LEGAIA_DISC_BIN']
        with _disc_context(path):
            for scene,owner,pc,target in [('town01','scene://town01/actors/man-p1/0002',31,11),
                                          ('dolk2','scene://dolk2/actors/man-p1/0002',28,9)]:
                with self.subTest(scene=scene):
                    source=load_dialogue_authoring_context(path,scene);context=BranchAuthoringContext(source)
                    row=next(r for r in context.options(owner)['targets'] if r['pc']==pc)
                    changed,audit=context.patch({row['semantic_id']:{'target_pc':target}})
                    self.assertEqual(context.patch({}),(source._man,[]))
                    self.assertEqual(read_man_layout(changed),read_man_layout(source._man))
                    self.assertEqual(parse_man(changed),parse_man(source._man))
                    self.assertFalse(context.inspect_owner(owner,changed)['stops'])
                    self.assertEqual({i for i,(a,b) in enumerate(zip(source._man,changed)) if a!=b},
                                     {r['decoded_byte_offset'] for r in audit[0]['changed_bytes']})
                    if source._compression=='lzs':
                        replacement,info=serialize_man_decoded(source._stream,len(changed),changed,scene)
                        self.assertEqual(len(replacement),len(source._stream))
                        self.assertLessEqual(info['new_encoded_size'],info['original_encoded_size'])
                        self.assertEqual(decompress_lzs(replacement,len(changed))[0],changed)
                    else:
                        self.assertEqual(len(changed),len(source._stream))
                        self.assertEqual(source._compression,'none')


if __name__=='__main__':unittest.main()

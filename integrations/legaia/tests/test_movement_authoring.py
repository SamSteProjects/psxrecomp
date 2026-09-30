"""Fixed-width movement authoring preserves dispatch and untouched source bytes."""
import unittest
from importer.core import ImportError
from importer.movement_authoring import MovementAuthoringContext, patch_movement_target
from importer.script_inspection import inspect_record
from test_importer_dialogue_authoring import fixture, ACTOR


class MovementAuthoringTests(unittest.TestCase):
    def test_appended_source_owner_rebases_without_touching_donor_clone(self):
        from hashlib import sha256
        from importer.man_actor_structure import append_actor_donor
        source,man=fixture(b'\x23\x00\x80\x3f\0\0\x06town01\1\2\3opaque')
        context=MovementAuthoringContext(source);target=context.options(ACTOR)['targets'][0]
        appended,_=append_actor_donor(man,sha256(man).hexdigest(),1)
        edits={target['semantic_id']:{'x':128}}
        result,audit=context.patch_appended(appended,edits)
        self.assertEqual(len(audit),1)
        self.assertEqual(audit[0]['decoded_byte_offset'],target['decoded_byte_offset']+3)
        self.assertEqual({i for i,(a,b) in enumerate(zip(appended,result)) if a!=b},{target['decoded_byte_offset']+3})
        self.assertEqual(context.patch_appended(appended,{}),(appended,[]))
        with self.assertRaisesRegex(ImportError,'preimage'):context.patch_appended(result,edits)
        wrong=bytearray(appended);wrong[target['decoded_byte_offset']+2]=0x40
        with self.assertRaises(ImportError):context.patch_appended(bytes(wrong),edits)

    def test_all_grid_bytes_roundtrip_and_context_operands_survive(self):
        for header, trailer in ((b'\x23', b''), (b'\xa3\x07', b''),
                                (b'\x4c\x51', b'\xab\xcd'), (b'\xcc\x07\x51', b'\xab\xcd')):
            for byte in range(256):
                record = header + bytes((byte, 255 - byte)) + trailer + b'\x3f\0\0\x06town01\x01\x02\x03opaque'
                original = inspect_record(record, 0)['instructions'][0]
                values = {axis: original['operands']['target_position'][axis] for axis in ('x', 'z')}
                self.assertEqual(patch_movement_target(record, 0, 0, values), (record, []))
            changed, audit = patch_movement_target(record, 0, 0, {'x':64, 'z':16384}, base_offset=100)
            self.assertEqual(changed[:len(header)], header)
            self.assertEqual(changed[len(header)+2:], trailer+b'\x3f\0\0\x06town01\x01\x02\x03opaque')
            node = inspect_record(changed, 0)['instructions'][0]
            self.assertEqual(node['target_context'], original['target_context'])
            self.assertEqual(node['operands']['target_position'], {'x':64,'y':None,'z':16384})
            self.assertEqual({i for i,(a,b) in enumerate(zip(record,changed)) if a!=b},
                             {row['record_relative_byte_offset'] for row in audit})
            self.assertTrue(all(row['decoded_byte_offset']==100+row['record_relative_byte_offset'] for row in audit))

    def test_npc_run_move_selector_preserves_depth_and_composes_with_coordinates(self):
        for header in (b'\x4c\x51', b'\xcc\x07\x51'):
            source = header + b'\x00\x80\xab\x09\x3f\0\0\x06town01\1\2\3opaque'
            for value in range(256):
                result, audit = patch_movement_target(source, 0, 0, {'move_id': value})
                offset = len(header) + 3
                self.assertEqual(result[:offset], source[:offset])
                self.assertEqual(result[offset + 1:], source[offset + 1:])
                self.assertEqual(inspect_record(result, 0)['instructions'][0]['operands']['move_id'], value)
                self.assertEqual(len(audit), int(value != 9))
        source, man = fixture(b'\x4c\x51\x00\x80\xab\x09\x3f\0\0\x06town01\1\2\3opaque')
        context = MovementAuthoringContext(source)
        target = context.options(ACTOR)['targets'][0]
        self.assertEqual(target['values']['move_id'], 9)
        values = {'x': 128, 'move_id': 10}
        result, audit = context.patch({target['semantic_id']: values})
        from sdk.build import _merge_movement_patch
        expected = {target['semantic_id']: dict(target, requested_values=values)}
        self.assertEqual(_merge_movement_patch(man, man, result, audit, expected, []), result)
        self.assertEqual({row['field'] for row in audit}, {'x', 'move_id'})
        from hashlib import sha256
        from importer.man_actor_structure import append_actor_donor
        appended, _ = append_actor_donor(man, sha256(man).hexdigest(), 1)
        _, rebased = context.patch_appended(appended, {target['semantic_id']: values})
        self.assertEqual([row['field'] for row in rebased], [row['field'] for row in audit])
        for value in (True, -1, 256, 1.5):
            with self.assertRaises(ImportError):
                patch_movement_target(b'\x4c\x51\x00\x80\xab\x09\x3f\0\0\x06town01\1\2\3opaque', 0, 0, {'move_id': value})
        with self.assertRaises(ImportError):
            patch_movement_target(b'\x23\x00\x80\x3f\0\0\x06town01\1\2\3opaque', 0, 0, {'move_id': 1})

    def test_exec_move_has_selector_only_and_fixed_dispatch_width(self):
        trailer = b'\x3f\0\0\x06town01\1\2\3opaque'
        for header in (b'\x22', b'\xa2\x07'):
            record = header + b'\x09' + trailer
            for value in range(256):
                changed, audit = patch_movement_target(record, 0, 0, {'move_id': value})
                self.assertEqual(changed[:len(header)], header)
                self.assertEqual(changed[len(header) + 1:], trailer)
                self.assertEqual(inspect_record(changed, 0)['instructions'][0]['operands']['move_id'], value)
                self.assertEqual(len(audit), int(value != 9))
            for values in ({'x': 64}, {'z': 128}, {'move_id': 2, 'x': 64}):
                with self.assertRaises(ImportError):
                    patch_movement_target(record, 0, 0, values)
        source, man = fixture(b'\x22\x09' + trailer)
        context = MovementAuthoringContext(source)
        target = context.options(ACTOR)['targets'][0]
        self.assertEqual(target['values'], {'move_id': 9})
        self.assertEqual(target['encoded_xz'], [])
        self.assertEqual(target['operand_offsets'], {'move_id': 0})
        result, audit = context.patch({target['semantic_id']: {'move_id': 10}})
        from sdk.build import _merge_movement_patch, BuildError
        expected = {target['semantic_id']: dict(target, requested_values={'move_id': 10})}
        self.assertEqual(_merge_movement_patch(man, man, result, audit, expected, []), result)
        with self.assertRaises(BuildError):
            _merge_movement_patch(man, man, result, [dict(audit[0], decoded_byte_offset=audit[0]['decoded_byte_offset'] + 3)], expected, [])
        from hashlib import sha256
        from importer.man_actor_structure import append_actor_donor
        appended, _ = append_actor_donor(man, sha256(man).hexdigest(), 1)
        changed, rebased = context.patch_appended(appended, {target['semantic_id']: {'move_id': 10}})
        self.assertEqual(len(rebased), 1)
        self.assertEqual({i for i, (a, b) in enumerate(zip(appended, changed)) if a != b}, {rebased[0]['decoded_byte_offset']})

    def test_invalid_values_unknown_paths_and_wrong_pc_rejected(self):
        record=b'\x23\x00\x80\x2a'
        for values in ({},{'y':0},{'x':True},{'x':65},{'z':0},{'z':16385},{'x':float('nan')}):
            with self.assertRaises(ImportError):patch_movement_target(record,0,0,values)
        for data,pc in ((record,1),(record,True),(b'\x23\x00',0),(b'\x23\x00\x80\xff',0),(b'\x2a\x23\x00\x80',1)):
            with self.assertRaises(ImportError):patch_movement_target(data,0,pc,{'x':64})

    def test_verified_context_is_atomic_and_parked_state_remains_explicit(self):
        source,man=fixture(b'\x23\x00\x80\x4c\x51\x7f\xff\x03\x09\x3f\0\0\x06town01\x01\x02\x03opaque')
        context=MovementAuthoringContext(source)
        targets=context.options(ACTOR)['targets'];self.assertEqual(len(targets),2)
        self.assertTrue(targets[1]['parked_target'])
        edits={targets[0]['semantic_id']:{'x':128},targets[1]['semantic_id']:{'z':64}}
        result,audit=context.patch(edits,original=man)
        self.assertEqual(len(result),len(man));self.assertEqual(len(audit),2)
        self.assertEqual({i for i,(a,b) in enumerate(zip(man,result)) if a!=b}, {row['decoded_byte_offset'] for row in audit})
        self.assertEqual(context.patch({}),(man,[]))
        for invalid in ({**edits,'foreign':{'x':128}}, {targets[0]['semantic_id'].replace('fixture','other'):{'x':128}}):
            with self.assertRaises(ImportError):context.patch(invalid)
        with self.assertRaisesRegex(ImportError,'baseline'):context.patch(edits,original=result)
        aliased,_=fixture(b'\x23\x00\x80\x2a',alias=True)
        with self.assertRaisesRegex(ImportError,'aliased'):MovementAuthoringContext(aliased).options(ACTOR)
        self.assertEqual(context.patch({}),(man,[]))


if __name__=='__main__':unittest.main()

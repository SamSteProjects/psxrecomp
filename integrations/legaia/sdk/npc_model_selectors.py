"""Source-qualified signed model selector words in appended NPC scripts.

Uses the existing MENU_CTRL 0x50 serializer. Encoded selectors are not resolved
asset IDs; model restaging, pairing and story execution remain unknown.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.model_selector_authoring import patch_model_selector_target
from .npc_script_allocation import allocated_scripts
from .project import ProjectError


def patch_allocated_model_selectors(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        owner=item['donor_entity_id'];source_offset=item['source_offset'];source=item['source_record'];entry=item['entry'];start=item['start'];length=item['length']
        for identifier,values in sorted(item['entries'].items()):
            target=item['targets'][identifier];pc=target['pc'];relative=target['decoded_byte_offset']-source_offset
            _,source_changes=patch_model_selector_target(source,entry,pc,values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            # A no-op must still prove the opcode, sub-op, extended dispatch and
            # original word. Existing unrelated script operands may differ.
            if clone[pc:relative+2]!=source[pc:relative+2]:
                raise ProjectError('NPC model selector dispatch or operand preimage differs from source')
            _,clone_changes=patch_model_selector_target(clone,entry,pc,values,base_offset=start)
            if len(source_changes)!=len(clone_changes):raise ProjectError('NPC model selector candidate instruction differs from source')
            for change,current in zip(source_changes,clone_changes):
                fields=('field','pc','mnemonic','target_context','record_relative_byte_offset','byte_length','before_hex','after_hex','before_selector','after_selector')
                if any(change[k]!=current[k] for k in fields):raise ProjectError('NPC model selector candidate operand differs from source')
                at=start+change['record_relative_byte_offset'];span=set(range(at,at+2))
                if span&occupied or not start<=at<=start+length-2:raise ProjectError('NPC model selector words overlap or escape their clone')
                occupied.update(span);output[at:at+2]=bytes.fromhex(change['after_hex'])
                audit.append(dict(change,draft_id=item['draft_id'],donor_entity_id=owner,model_selector_id=identifier,record_index=item['record_index'],source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC model selectors changed MAN structure')
    return result,dict(schema_version='legaia.npc-model-selectors-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_source_qualified_signed_model_selector_words_only',gameplay_verified=False,runtime_model_identity='not_asserted',model_restaging='not_asserted',npc_placement_changed=False)

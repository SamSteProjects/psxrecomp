"""Native NPC-owned named scene-change arrival bytes; no runtime simulation.

Only qualified SCENE_CHANGE entry X/Z/direction bytes serialize here. Names and
complete dispatch/preimages remain bound to the imported donor instruction.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.transition_authoring import patch_transition_entry
from importer.script_inspection import _instruction
from .npc_script_allocation import allocated_scripts
from .project import ProjectError


def patch_allocated_transitions(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests,target_key='transitions')
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        owner=item['donor_entity_id'];source_offset=item['source_offset'];source=item['source_record'];entry=item['entry'];start=item['start'];length=item['length']
        for identifier,values in sorted(item['entries'].items()):
            target=item['targets'][identifier];pc=target['pc'];relative=target['decoded_byte_offset']-source_offset;node=_instruction(source,pc)
            _,source_changes=patch_transition_entry(source,entry,pc,values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            # Bind all source arguments even for partial/no-op requests: an
            # edited destination or context must never be silently inherited.
            if relative+3!=pc+node['length'] or clone[pc:relative+3]!=source[pc:relative+3]:
                raise ProjectError('NPC transition instruction, destination or arrival preimage differs from source')
            _,clone_changes=patch_transition_entry(clone,entry,pc,values,base_offset=start)
            if len(source_changes)!=len(clone_changes):raise ProjectError('NPC transition candidate instruction differs from source')
            for change,current in zip(source_changes,clone_changes):
                if any(change[k]!=current[k] for k in ('field','pc','record_relative_byte_offset','before_byte','after_byte')):
                    raise ProjectError('NPC transition candidate operand differs from source')
                at=start+change['record_relative_byte_offset']
                if at in occupied or not start<=at<start+length:raise ProjectError('NPC transition bytes overlap or escape their clone')
                occupied.add(at);output[at]=change['after_byte']
                audit.append(dict(change,draft_id=item['draft_id'],donor_entity_id=owner,transition_id=identifier,record_index=item['record_index'],mnemonic=node['mnemonic'],target_context=node['target_context'],destination=target['destination'],source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at,byte_length=1))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC transitions changed MAN structure')
    return result,dict(schema_version='legaia.npc-transitions-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_source_qualified_named_transition_arrival_bytes_only',gameplay_verified=False,transition_activation='not_asserted',destination_name_changed=False,npc_placement_changed=False)

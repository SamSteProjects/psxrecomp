"""Source-qualified low-nibble facing edits in allocated NPC script records.

This serializer does not establish initial heading, runtime dispatch or execution.
"""
from copy import deepcopy
from hashlib import sha256
from importer.facing_authoring import patch_facing_sector,PRESERVATION_MASK
from importer.man_layout import read_man_layout
from .npc_script_allocation import allocated_scripts
from .project import ProjectError


def patch_allocated_facing(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        identifier,owner,entries,targets,source_offset,source_record,entry,start,length,index=(item[k] for k in ('draft_id','donor_entity_id','entries','targets','source_offset','source_record','entry','start','length','record_index'))
        for facing_id,values in sorted(entries.items()):
            target=targets[facing_id];relative=target['decoded_byte_offset']-source_offset;pc=target['pc']
            _,changes=patch_facing_sector(source_record,entry,pc,values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            # Only dispatch/opcode bytes are immutable here: composed movement may
            # already have changed NPC_RUN X/Z and its move selector.
            header_end=pc+(2 if target['target_context'] is not None else 1)+(target['mnemonic']=='NPC_RUN')
            if clone[pc:header_end]!=source_record[pc:header_end]:
                raise ProjectError('NPC facing dispatch/opcode preimage differs from source')
            if target['mnemonic']=='CAM_CFG' and clone[relative+1]!=source_record[relative+1]:
                raise ProjectError('NPC facing CAM_CFG mode differs from source')
            if clone[relative]!=source_record[relative]:
                raise ProjectError('NPC facing operand preimage differs from source')
            _,current_changes=patch_facing_sector(clone,entry,pc,values,base_offset=start)
            if len(changes)!=len(current_changes):raise ProjectError('NPC facing candidate instruction differs from source')
            for change,current in zip(changes,current_changes):
                if any(change[k]!=current[k] for k in ('field','pc','mnemonic','target_context','record_relative_byte_offset','before_byte','after_byte','before_sector','after_sector')):
                    raise ProjectError('NPC facing candidate operand differs from source')
                at=start+change['record_relative_byte_offset']
                if at in occupied or not start<=at<start+length or change['before_byte']&PRESERVATION_MASK!=change['after_byte']&PRESERVATION_MASK:
                    raise ProjectError('NPC facing spans overlap, escape their clone or change upper flags')
                occupied.add(at);output[at]=change['after_byte']
                audit.append(dict(change,draft_id=identifier,donor_entity_id=owner,facing_id=facing_id,record_index=index,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC facing changed MAN structure')
    return result,dict(schema_version='legaia.npc-facing-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_supported_facing_nibbles_only',gameplay_verified=False,runtime_dispatch='not_asserted',initial_heading='not_asserted',npc_placement_changed=False)

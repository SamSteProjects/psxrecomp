"""Source-qualified flag bit operands owned by final appended NPC records.

Only bit indices serialize here; runtime variables, story meaning and execution
remain unknown. The imported flag adapter owns width and side-effect exclusions.
"""
from copy import deepcopy
from hashlib import sha256
from importer.flag_authoring import patch_flag_bit
from importer.man_layout import read_man_layout
from .npc_script_allocation import allocated_scripts
from .project import ProjectError


def patch_allocated_flags(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        identifier,owner,entries,targets,source_offset,source_record,entry,start,length,index=(item[k] for k in ('draft_id','donor_entity_id','entries','targets','source_offset','source_record','entry','start','length','record_index'))
        for flag_id,values in sorted(entries.items()):
            target=targets[flag_id];pc=target['pc'];relative=target['decoded_byte_offset']-source_offset
            _,changes=patch_flag_bit(source_record,entry,pc,values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            # Bind the full opcode, any extended context and complete operand,
            # even for a source-identical no-op request.
            if clone[pc:relative+1]!=source_record[pc:relative+1]:
                raise ProjectError('NPC flag dispatch or operand preimage differs from source')
            _,current_changes=patch_flag_bit(clone,entry,pc,values,base_offset=start)
            if len(changes)!=len(current_changes):raise ProjectError('NPC flag candidate instruction differs from source')
            for change,current in zip(changes,current_changes):
                if any(change[k]!=current[k] for k in ('field','pc','mnemonic','target_context','record_relative_byte_offset','before_byte','after_byte','before_bit','after_bit')):
                    raise ProjectError('NPC flag candidate operand differs from source')
                at=start+change['record_relative_byte_offset']
                if at in occupied or not start<=at<start+length or change['before_byte']&0xe0!=change['after_byte']&0xe0:
                    raise ProjectError('NPC flag spans overlap, escape their clone or change upper bits')
                occupied.add(at);output[at]=change['after_byte']
                audit.append(dict(change,draft_id=identifier,donor_entity_id=owner,flag_id=flag_id,record_index=index,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC flags changed MAN structure')
    return result,dict(schema_version='legaia.npc-flags-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_supported_flag_bit_indices_only',gameplay_verified=False,runtime_variable_identity='not_asserted',story_meaning='not_asserted',npc_placement_changed=False)

"""Qualified fixed-width movement operands owned by appended NPC scripts.

Script targets remain distinct from NPC placement and live positions. The
serializer does not resolve dispatch identity or change Y/depth/branch layout.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from importer.movement_authoring import patch_movement_target
from .npc_script_allocation import allocated_scripts
from .project import ProjectError


def patch_allocated_movement(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        identifier,owner,entries,targets,source_offset,source_record,entry,start,length,index=(item[k] for k in ('draft_id','donor_entity_id','entries','targets','source_offset','source_record','entry','start','length','record_index'))
        for movement_id,values in sorted(entries.items()):
            target=targets[movement_id]
            _,changes=patch_movement_target(source_record,entry,target['pc'],values,base_offset=source_offset)
            clone=bytes(output[start:start+length])
            _,clone_changes=patch_movement_target(clone,entry,target['pc'],values,base_offset=start)
            relative=target['decoded_byte_offset']-source_offset
            # Retain opcode, extended context and NPC_RUN's extra dispatch byte.
            if clone[target['pc']:relative]!=source_record[target['pc']:relative]:
                raise ProjectError('NPC movement dispatch/header preimage differs from source')
            # Verify source-identical requested operands as well as changed ones.
            for field in values:
                at=relative+target['operand_offsets'][field]
                if clone[at]!=source_record[at]:raise ProjectError('NPC movement operand preimage differs from source')
            if len(changes)!=len(clone_changes):raise ProjectError('NPC movement candidate instruction differs from source')
            for change,current in zip(changes,clone_changes):
                if any(change[k]!=current[k] for k in ('field','pc','mnemonic','target_context','record_relative_byte_offset','before_byte','after_byte')):
                    raise ProjectError('NPC movement candidate instruction differs from source')
                at=start+change['record_relative_byte_offset']
                if at in occupied or not start<=at<start+length:raise ProjectError('NPC movement spans overlap or escape their clone')
                occupied.add(at);output[at]=change['after_byte']
                audit.append(dict(change,draft_id=identifier,donor_entity_id=owner,movement_id=movement_id,record_index=index,source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=at))
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC movement changed MAN structure')
    return result,dict(schema_version='legaia.npc-movement-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_supported_movement_operands_only',gameplay_verified=False,runtime_dispatch='not_asserted',npc_placement_changed=False)

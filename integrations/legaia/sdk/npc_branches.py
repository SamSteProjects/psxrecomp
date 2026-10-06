"""Independent source-qualified branch words in final appended NPC records.

Branch edits are composed last: original instructions and message boundaries stay
qualified even when changed edges make some of them unreachable. No VM executes.
"""
from copy import deepcopy
from hashlib import sha256
from importer.man_layout import read_man_layout
from .npc_script_allocation import allocated_scripts
from .project import ProjectError


def patch_allocated_branches(context,candidate,allocations,requests):
    original,layout,prepared=allocated_scripts(context,candidate,allocations,requests)
    output=bytearray(candidate);audit=[];occupied=set()
    for item in prepared:
        owner=item['donor_entity_id'];source_offset=item['source_offset'];record=item['source_record'];start=item['start'];length=item['length']
        # The existing native adapter owns source graph and condition qualification.
        # Bind this clone to its immutable donor slot for that request only; never
        # derive source boundaries from authored or newly reached candidate bytes.
        rebound=bytearray(original);rebound[source_offset:source_offset+length]=output[start:start+length]
        patched,changes=context.patch_composed(bytes(rebound),item['entries'])
        clone=patched[source_offset:source_offset+length]
        allowed=set()
        for change in changes:
            relative=change['record_relative_byte_offset'];span=set(range(start+relative,start+relative+2))
            if not 0<=relative<=length-2 or span&occupied:
                raise ProjectError('NPC branch words overlap or escape their clone')
            occupied.update(span);allowed.update(range(relative,relative+2))
            changed_bytes=[dict(row,source_decoded_byte_offset=row['decoded_byte_offset'],decoded_byte_offset=start+row['decoded_byte_offset']-source_offset) for row in change['changed_bytes']]
            audit.append(dict(change,draft_id=item['draft_id'],donor_entity_id=owner,record_index=item['record_index'],source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=start+relative,changed_bytes=changed_bytes))
        if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(output[start:start+length],clone))):
            raise ProjectError('NPC branch composition changed an unaudited clone byte')
        output[start:start+length]=clone
    result=bytes(output)
    if read_man_layout(result)!=layout:raise ProjectError('NPC branch composition changed MAN structure')
    return result,dict(schema_version='legaia.npc-branches-native.v1',source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),result_man_sha256=sha256(result).hexdigest(),changes=deepcopy(audit),scope='appended_source_qualified_branch_target_words_only',gameplay_verified=False,branch_activation='not_asserted',runtime_termination='not_asserted',npc_placement_changed=False)

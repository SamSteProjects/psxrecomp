"""Qualified initial appearance edits for allocated NPC clones.

This native adapter is not yet an editor command. It separates the retail
script donor from the model/animation witness without rewriting script bytes.
"""
from hashlib import sha256
from importer.core import parse_man
from importer.man_layout import read_man_layout
from .project import ProjectError

def patch_allocated_appearance(context, candidate, allocations, requests):
    """Apply source-qualified donor pairs to exact appended record identities.

    ``context`` is a verified ManAssignmentContext, ``allocations`` is the
    append-actor audit, and requests contain stable draft IDs plus retail donor
    record indices. Clients never supply native model/animation numbers or bytes.
    """
    if not isinstance(candidate,bytes) or not 0<len(candidate)<=4*1024*1024:
        raise ProjectError('NPC appearance requires a bounded immutable MAN candidate')
    if not isinstance(allocations,dict) or not isinstance(allocations.get('drafts'),list):
        raise ProjectError('NPC appearance requires an actor allocation audit')
    if not isinstance(requests,list) or not 1<=len(requests)<=128:
        raise ProjectError('NPC appearance requires 1 through 128 donor requests')
    original,_=context.patch({});source={a.record_index:a for a in parse_man(original).actors}
    layout=read_man_layout(candidate);actors={a.record_index:a for a in parse_man(candidate).actors}
    rows={}
    for row in allocations['drafts']:
        if not isinstance(row,dict) or not isinstance(row.get('draft_id'),str) or row['draft_id'] in rows:
            raise ProjectError('NPC appearance allocation identities are ambiguous')
        rows[row['draft_id']]=row
    output=bytearray(candidate);audit=[];seen=set();indices=set()
    for request in requests:
        if not isinstance(request,dict) or set(request)!={'draft_id','appearance_donor_record_index'}:
            raise ProjectError('NPC appearance accepts only draft identity and a retail donor index')
        identifier=request['draft_id'];donor_index=request['appearance_donor_record_index']
        if not isinstance(identifier,str) or identifier in seen or identifier not in rows or type(donor_index) is not int or donor_index not in source:
            raise ProjectError('NPC appearance draft or donor is unavailable or duplicated')
        seen.add(identifier);allocation=rows[identifier];index=allocation.get('record_index');script_index=allocation.get('donor',{}).get('record_index')
        if type(index) is not int or index in source or index in indices or index not in actors or type(script_index) is not int or script_index not in source:
            raise ProjectError('NPC appearance must target a unique appended actor, never a retail record')
        indices.add(index);actor=actors[index];script=source[script_index];donor=source[donor_index]
        if actor.byte_length!=script.byte_length or actor.local_count!=script.local_count or actor.byte_length!=allocation.get('byte_length'):
            raise ProjectError('NPC appearance allocation extent differs from its script donor')
        if sum(row['byte_offset']==actor.byte_offset for row in layout['records'])!=1:
            raise ProjectError('NPC appearance cannot write an aliased appended record')
        pair=dict(model_index=donor.model_index,animation_id=donor.animation_id)
        options=context.options(script_index)
        if not any(row['model_index']==donor.model_index and row['animation_id']==donor.animation_id and donor_index in row['donor_records'] for row in options['pairs']):
            raise ProjectError('NPC appearance donor pair is not source-qualified for this script donor')
        # Reuse native model/channel and alias guards, including exact preimages.
        _,changes=context.patch({script_index:pair})
        offset=actor.byte_offset+1+actor.local_count*2
        if (actor.model_index,actor.animation_id)!=(script.model_index,script.animation_id):
            raise ProjectError('NPC appearance header preimage differs from its retail script donor')
        for change in changes:
            relative=change['decoded_byte_offset']-script.byte_offset
            target=actor.byte_offset+relative
            if target not in (offset,offset+1) or output[target]!=change['before_byte']:
                raise ProjectError('NPC appearance header ownership or preimage differs')
            output[target]=change['after_byte']
            audit.append(dict(change,draft_id=identifier,record_index=index,
                script_donor_record_index=script_index,appearance_donor_record_index=donor_index,
                source_decoded_byte_offset=change['decoded_byte_offset'],decoded_byte_offset=target))
    result=bytes(output)
    if read_man_layout(result)!=layout:
        raise ProjectError('NPC appearance changed MAN structure')
    reparsed={a.record_index:a for a in parse_man(result).actors}
    for request in requests:
        actor=reparsed[rows[request['draft_id']]['record_index']];donor=source[request['appearance_donor_record_index']]
        if (actor.model_index,actor.animation_id)!=(donor.model_index,donor.animation_id):
            raise ProjectError('NPC appearance native pair did not round-trip')
    return result,dict(schema_version='legaia.npc-appearance-native.v1',
        source_man_sha256=sha256(original).hexdigest(),candidate_man_sha256=sha256(candidate).hexdigest(),
        result_man_sha256=sha256(result).hexdigest(),changes=audit,
        scope='appended_initial_model_animation_header_only',gameplay_verified=False,
        script_compatibility='not_asserted',runtime_binding='not_asserted')

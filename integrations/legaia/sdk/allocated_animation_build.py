"""Compose source-qualified allocated initial headers with normal MAN edits."""
from hashlib import sha256
from importer.core import parse_man
from importer.man_assignments import load_man_assignment_context
from .animation_record_ledger import compose
from .allocated_animation_assignment import validate_binding
from .project import ProjectError


def patch_assignments(project,scene_id,bindings,baseline,changed,*,appended=False):
    document=project.imports[scene_id];scene=document['scene']['name']
    actors={a['semantic_id']:a for a in document['actors']}
    bank,allocation=compose(project,scene_id)
    ordinals={row['record_id']:row['record_index'] for row in allocation['allocated_records']}
    edits={};identities={}
    for entity,value in sorted(bindings.items()):
        entry=validate_binding(project,entity,value,verify_disc=True)
        target=actors[entity]['source_record']['record_index']
        donor=actors[entry['channel_owner_entity_id']]['source_record']['record_index']
        edits[target]=dict(donor_record_index=donor,allocated_record_index=ordinals[value['record_id']],
                           record_sha256=value['record_sha256'])
        identities[target]=(entity,value)
    context=load_man_assignment_context(project.disc_path,scene)
    if appended:
        proposal,audit=context.patch_allocated_appended(changed,bank,sha256(bank).hexdigest(),edits,original=baseline)
        preimage=changed
    else:
        proposal,audit=context.patch_allocated(bank,sha256(bank).hexdigest(),edits,original=baseline)
        preimage=baseline
    if len(changed)!=len(preimage) or len(proposal)!=len(preimage):
        raise ProjectError('Allocated initial header composition requires the original MAN layout')
    result=bytearray(changed);covered=set()
    for row in audit:
        offset=row['decoded_byte_offset']
        if offset in covered or result[offset]!=row['before_byte'] or preimage[offset]!=row['before_byte']:
            raise ProjectError('Allocated initial header overlaps another authored MAN edit')
        if proposal[offset]!=row['after_byte']:
            raise ProjectError('Allocated initial header audit disagrees with native proposal')
        result[offset]=row['after_byte'];covered.add(offset)
        entity,value=identities[row['record_index']]
        row.update(semantic_id=entity,assignment_kind='ActorAllocatedAnimation',record_id=value['record_id'],
                   model_asset_id=value['model_asset_id'],gameplay_verified=False)
    if {i for i,(a,b) in enumerate(zip(preimage,proposal)) if a!=b}!=covered:
        raise ProjectError('Allocated initial header audit omits native changed bytes')
    parsed={a.record_index:a for a in parse_man(bytes(result),scene).actors}
    expected={a.record_index:a for a in parse_man(proposal,scene).actors}
    for record in edits:
        a,b=parsed[record],expected[record]
        if (a.local_count,a.model_index,a.animation_id)!=(b.local_count,b.model_index,b.animation_id):
            raise ProjectError('Composed allocated initial header failed native readback')
    return bytes(result),audit

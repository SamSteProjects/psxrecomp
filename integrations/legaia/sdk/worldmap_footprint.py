"""Static-object footprint offsets from pinned field_objects.rs, not live bounds."""
from hashlib import sha256
import re, struct
from importer.worldmap_placements import decode_worldmap_placements
from .project import ProjectError
from .worldmap_placement_allocation import _context, _fresh


def inspect(project, scene, key, entity_id):
    if scene not in ('map01','map02','map03') or not isinstance(entity_id,str) or not re.fullmatch(r'scene://'+re.escape(scene)+r'/worldmap/placements/[0-3][0-9a-f]{3}',entity_id):
        raise ProjectError('Footprint inspection requires a native source placement identity')
    raw,provenance,floor,current,_=_context(project,scene,key)
    seed=next((p for p in decode_worldmap_placements(current,floor,scene=scene)['placements'] if p['entity_id']==entity_id),None)
    if seed is None or seed['source_layer']!='placed':
        raise ProjectError('Footprint inspection requires a resolved placed static-object seed')
    at=seed['object_record_index']*32
    x,y,z=struct.unpack_from('<3h',current,at)
    dc,dr=struct.unpack_from('<2b',current,at+6)
    sx,sz=struct.unpack_from('<2b',current,at+14)
    flags=struct.unpack_from('<H',current,at+18)[0]
    dx,dz=dc*128+sx*16,dr*128+sz*16
    if flags&8:dx-=x;dz+=z
    anchor=seed['source_anchor'];cell=anchor['row']*128+anchor['col']
    result=dict(schema_version='legaia.worldmap-footprint-inspection.v1',project_path=str(project.root),scene=scene,
        source_key=key,source_record=provenance,current_map_sha256=sha256(current).hexdigest(),entity_id=entity_id,
        source_cell=seed['source_cell'],record_index=seed['object_record_index'],record_sha256=sha256(current[at:at+32]).hexdigest(),
        encoded=dict(offset=dict(x=x,y=y,z=z),anchor_delta=dict(col=dc,row=dr),sub_anchor=dict(x=sx,z=sz),flags=flags),
        anchor=dict(col=anchor['col'],row=anchor['row'],cell_index=cell,cell_flags=anchor['cell_flags'],bind_owner=seed['source_bind_owner']),
        correction=bool(flags&8),offset=dict(x=dx,z=dz),centre=dict(x=seed['source_position']['x']+dx,z=seed['source_position']['z']+dz),
        source_position=seed['source_position'],extents='unknown',runtime_collision='not_evaluated',interaction_script='not_resolved',
        animation='not_resolved',scope='source-static-footprint-offset-only',read_only=True,project_changed=False,gameplay_verified=False)
    _fresh(project,key)
    return result

"""Read-only project-qualified scripted World placement source and Review."""
from base64 import b64encode
from copy import deepcopy
from hashlib import sha256
import json
import struct

from importer.pipeline import _disc_context,_bounded_scene_range
from importer.worldmap_object_bind_allocation import _tables,_catalog
from importer.worldmap_object_binds import resolve_object_bind
from importer.worldmap_placement_allocation import inventory
from importer.worldmap_placements import decode_worldmap_placements
from importer.worldmap_scripted_placement_allocation import allocate_scripted_placements
from .project import ProjectError,digest
from .worldmap_placement_allocation import _context,_fresh
from .worldmap_script_operands import context as script_context


def _merge_map(raw,current,patched,name,audit):
    if len(patched)!=len(raw):raise ProjectError('Scripted World MAP coauthor changed its source footprint')
    walls={}
    if name=='Collision':
        for row in audit:walls[row['byte_offset']]=walls.get(row['byte_offset'],0)|row['bit_mask']
    merged=bytearray(current)
    for i,(old,new) in enumerate(zip(raw,patched)):
        if old==new:continue
        mask=walls.get(i,0) if name=='Collision' else 15 if name=='FloorTiers' else 255
        if not mask or (current[i]&mask) not in (old&mask,new&mask):
            raise ProjectError('Scripted World MAP coauthor conflicts with Current ownership')
        merged[i]=(current[i]&~mask)|(new&mask)
    return bytes(merged)


def _inputs(project,scene,key):
    raw,provenance,floor,current,allocations=_context(project,scene,key)
    man,_,man_provenance,_,_,_,_,_,current_man,_=script_context(project,scene)
    with _disc_context(project.disc_path) as (_,disc_hash,mapping,archive):
        start,end=_bounded_scene_range(archive,mapping,scene)
        entry=archive.entry(start)
        if disc_hash!=provenance['source_disc_sha256'] or sha256(archive.read_entry(entry,extended=True)).hexdigest()!=provenance['source_map_sha256'] or start+1>=end:
            raise ProjectError('Scripted World source differs from the qualified MAP/disc')
        following=archive.entry(start+1)
        if following.start_lba!=entry.start_lba+36 or following.size_sectors<4:
            raise ProjectError('Scripted World allocation requires a qualified contiguous fallback block')
        fallback=archive.image.read_user(archive.node.extent_lba,following.start_lba*archive.SECTOR,0x2000,archive.node.size)
    components=project.overrides.get('scene://'+scene,{})
    if components.get('FloorHeights'):
        identifier='scene://'+scene
        project._validate_floor_heights(identifier,components['FloorHeights'])
        from .floor_heights import compose as compose_floor_heights
        current_man,_=compose_floor_heights(project,identifier,man,current_man)
    # Compose each existing scene MAP family against its immutable source.
    # Declared masks permit independent floor/wall fields in the same byte;
    # coordinate and record fields must never become a hybrid of two edits.
    from importer.environment_authoring import patch_environment_overrides
    from importer.collision_authoring import patch_collision_walls
    from importer.floor_authoring import patch_floor_tiers
    from importer.region_authoring import patch_field_regions
    from importer.trigger_authoring import patch_field_triggers
    from importer.trigger_script_authoring import patch_trigger_scripts
    writers={
        'Environment':lambda b:patch_environment_overrides(raw,b),
        'Collision':lambda b:patch_collision_walls(raw,b['source_sha256'],b['edits']),
        'FloorTiers':lambda b:patch_floor_tiers(raw,b['source_sha256'],b['edits']),
        'RegionBounds':lambda b:patch_field_regions(raw,b['source_sha256'],scene,b['edits']),
        'TriggerCells':lambda b:patch_field_triggers(raw,b['source_sha256'],scene,b['edits']),
        'TriggerScripts':lambda b:patch_trigger_scripts(raw,b['source_sha256'],scene,b['edits'])}
    coauthors=[]
    for name,writer in writers.items():
        if name not in components:continue
        patched,audit=writer(components[name])
        current=_merge_map(raw,current,patched,name,audit);coauthors.append(name)
    floor=list(struct.unpack_from('<16h',current_man,2))
    if current_man[2:34]!=man[2:34]:
        seeds={p['source_cell']:p for p in decode_worldmap_placements(current,floor,scene=scene)['placements']}
        allocations=deepcopy(allocations)
        for allocation in allocations:
            allocation['native_seed']=deepcopy(seeds[allocation['target_cell']])
    _fresh(project,key)
    return raw,provenance,floor,current,allocations,fallback,man,current_man,man_provenance,coauthors


def _options(current,fallback,man,floor,scene):
    inv=inventory(current,floor,scene);catalog=_catalog(current[0x10000:],fallback,scene)
    donors=[]
    for seed in inv['current_placements']:
        if seed['source_layer']!='placed' or seed['source_bind_owner']!='init_bind' or not seed['model_pool_index']:continue
        bind=resolve_object_bind(catalog,man,seed['source_anchor']['col'],seed['source_anchor']['row'])
        if bind['status']=='resolved_source_header' and bind['trigger']['table_source']=='primary':
            donors.append(dict(seed=deepcopy(seed),bind=bind,shared_script_required=True))
    tables,occupied=_tables(current[0x10000:]);count=len(tables[1][1]);size=4*(count+32)
    lower=(max([0x12]+[hi for _,hi in occupied])+3)&~1
    destination=next((i for i in range(lower,0x2000-size+1,2) if current[0x10000+i:0x10000+i+size]==bytes(size)),None)
    return dict(donors=donors,free_record_indices=inv['free_record_indices'],target_cells=inv['target_cells'],
        relocation_offset=destination,relocation_capacity=32 if destination is not None else 0)


def _bounded(result):
    if len(json.dumps(result,allow_nan=False).encode('utf-8'))>2*1024*1024:
        raise ProjectError('Scripted World allocation exceeds its response budget')
    return result


def source(project,scene,key):
    raw,provenance,floor,current,allocations,fallback,man,current_man,man_provenance,coauthors=_inputs(project,scene,key)
    result=dict(schema_version='legaia.worldmap-scripted-placement-source.v1',project_path=str(project.root),
        scene=scene,source_key=key,source_record=provenance,man_source=man_provenance,
        source_map_base64=b64encode(raw).decode('ascii'),source_man_base64=b64encode(man).decode('ascii'),
        current_map_sha256=sha256(current).hexdigest(),current_map_base64=b64encode(current).decode('ascii'),
        source_man_sha256=sha256(man).hexdigest(),current_man_sha256=sha256(current_man).hexdigest(),
        current_man_base64=b64encode(current_man).decode('ascii'),fallback_sha256=sha256(fallback).hexdigest(),
        fallback_base64=b64encode(fallback).decode('ascii'),floor_lut=floor,authored_decorations=allocations,
        scene_map_coauthors=coauthors,
        scene_man_coauthors=['FloorHeights'] if project.overrides.get('scene://'+scene,{}).get('FloorHeights') else [],
        **_options(current,fallback,current_man,floor,scene),
        read_only=True,project_changed=False,build_ready=False,gameplay_verified=False,
        limitations=['Script records remain shared; creation requires explicit shared-script scope.',
            'Target cells are preliminary empty candidates; donor footprints and binds are checked during Review.',
            'Runtime actor demand, script effects and opaque zero relocation-space ownership remain unverified.',
            'Apply, persistence, editor controls and package Build are not implemented for this proposal.'])
    _fresh(project,key)
    return _bounded(result)


def review(project,scene,key,requests):
    raw,provenance,floor,current,allocations,fallback,man,current_man,man_provenance,coauthors=_inputs(project,scene,key)
    options=_options(current,fallback,current_man,floor,scene)
    if options['relocation_offset'] is None:raise ProjectError('Scripted World allocation has no bounded zero relocation candidate')
    existing={a['placement_id'] for a in allocations}
    if isinstance(requests,list) and any(isinstance(r,dict) and r.get('placement_id') in existing for r in requests):
        raise ProjectError('Scripted World placement UUID already belongs to an authored decoration')
    candidate,audit=allocate_scripted_placements(current,fallback,current_man,floor,scene,requests,relocation_offset=options['relocation_offset'])
    result=dict(schema_version='legaia.worldmap-scripted-placement-review.v1',project_path=str(project.root),
        scene=scene,source_key=key,source_record=provenance,man_source=man_provenance,
        current_map_sha256=sha256(current).hexdigest(),current_man_sha256=sha256(current_man).hexdigest(),
        fallback_sha256=sha256(fallback).hexdigest(),requests=deepcopy(requests),
        relocation_offset=options['relocation_offset'],proposed_map_sha256=sha256(candidate).hexdigest(),
        proposed_map_base64=b64encode(candidate).decode('ascii'),audit=audit,scene_map_coauthors=coauthors,
        scene_man_coauthors=['FloorHeights'] if project.overrides.get('scene://'+scene,{}).get('FloorHeights') else [],
        read_only=True,project_changed=False,build_ready=False,gameplay_verified=False)
    result['review_key']=digest(result)
    _fresh(project,key)
    return _bounded(result)

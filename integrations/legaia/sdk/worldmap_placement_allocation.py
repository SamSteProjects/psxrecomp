"""Read-only native decoration donors and complete source-bound clone Review."""
from copy import deepcopy
from hashlib import sha256
import base64
import json

from importer.worldmap_placement_allocation import inventory, allocate
from .project import ProjectError, digest
from .worldmap_authoring import state_key
from .worldmap_placements import context
from .worldmap_placement_allocation_binding import COMPONENT, SCHEMA, owner, validate, replay, compose


def _fresh(project, key):
    if project.mode != 'edit' or key != state_key(project):
        raise ProjectError('World placement allocation requires current Edit source inputs')


def _context(project, scene, key):
    _fresh(project, key)
    raw, provenance, records, offset, floor, binding, current, placements = context(project, scene)
    _fresh(project, key)
    current, allocations = compose(project,scene,raw,provenance,floor,current)
    _fresh(project, key)
    return raw, provenance, floor, current, allocations


def source(project, scene, key):
    raw, provenance, floor, current, allocations = _context(project, scene, key)
    result = dict(schema_version='legaia.worldmap-placement-allocation-source.v2',
        project_path=str(project.root), scene=scene, source_key=key, source_record=provenance,
        current_map_sha256=sha256(current).hexdigest(), current_map_base64=base64.b64encode(current).decode('ascii'),
        floor_lut=floor, authored_allocations=allocations,
        binding=deepcopy(project.overrides.get(owner(scene),{}).get(COMPONENT)),
        **inventory(current, floor, scene), read_only=True, project_changed=False,
        gameplay_verified=False, limitations=[
            'Clones are walk-decoration source seeds, not scripted NPCs or placed landmark actors.',
            'Complete donor placement metadata is copied; target terrain selectors and cell upper flags are preserved.',
            'Collision, script side effects, native visibility and resting positions require gameplay verification.',
            'Authored placement identity remains separate from Retail instances and live observations.'])
    if len(json.dumps(result, allow_nan=False).encode('utf-8')) > 2*1024*1024:
        raise ProjectError('World placement allocation source exceeds its response budget')
    _fresh(project, key)
    return result


def review(project, scene, key, requests):
    raw, provenance, floor, current, allocations = _context(project, scene, key)
    candidate, audit = allocate(current, floor, scene, requests)
    before = deepcopy(project.overrides.get(owner(scene),{}).get(COMPONENT))
    binding = deepcopy(before) if before else dict(schema_version=SCHEMA,**provenance,operations=[])
    canonical, _ = replay(raw,floor,before) if before else (raw,[])
    canonical, _ = allocate(canonical,floor,scene,requests)
    binding['operations'].append(dict(requests=deepcopy(requests),proposed_map_sha256=sha256(canonical).hexdigest()))
    validate(project,owner(scene),binding)
    # Existing source XYZ/yaw edits are independent of cloned records. The
    # clone's explicit values replace those donor words during either replay.
    _, _, _, _, _, _, transformed, _ = context(project,scene)
    independently_composed, _ = compose(project,scene,raw,provenance,floor,transformed,binding)
    if independently_composed != candidate:
        raise ProjectError('World placement allocation differs from retained lineage and source transforms')
    result = dict(schema_version='legaia.worldmap-placement-allocation-review.v2',
        project_path=str(project.root), scene=scene, source_key=key, source_record=provenance,
        requests=deepcopy(requests), current_map_sha256=sha256(current).hexdigest(),
        proposed_map_sha256=sha256(candidate).hexdigest(), proposed_map_base64=base64.b64encode(candidate).decode('ascii'),
        audit=audit, binding=binding, before_binding=before,
        read_only=True, project_changed=False, gameplay_verified=False, build_ready=False)
    result['review_key'] = digest(result)
    if len(json.dumps(result, allow_nan=False).encode('utf-8')) > 2*1024*1024:
        raise ProjectError('World placement allocation Review exceeds its response budget')
    _fresh(project, key)
    return result


def apply(project, command):
    if (not isinstance(command,dict) or set(command) != {'type','scene','source_key','requests','review_key'}
            or command['type'] != 'allocate_worldmap_placements'):
        raise ProjectError('World placement allocation Apply requires its exact reviewed requests')
    result = review(project,command['scene'],command['source_key'],command['requests'])
    if result['review_key'] != command['review_key']:
        raise ProjectError('World placement allocation Review changed; review again')
    identifier = owner(command['scene']);before=deepcopy(project.overrides.get(identifier))
    after = {COMPONENT:deepcopy(result['binding'])}
    project.overrides[identifier] = after
    project.undo_stack.append(dict(entity_id=identifier,before=before,after=deepcopy(after)))
    project.redo_stack.clear()


def build(project, overlays):
    changes = []
    for scene in ('map01','map02','map03'):
        if COMPONENT not in project.overrides.get(owner(scene),{}): continue
        raw,provenance,_,offset,floor,_,transformed,_ = context(project,scene)
        candidate,allocations = compose(project,scene,raw,provenance,floor,transformed)
        matching = [o for o in overlays if o['offset']==offset and o['size']==len(raw)]
        if len(matching)>1: raise ProjectError('World allocation MAP overlay ownership is ambiguous')
        if matching:
            target=matching[0]
            if target['expected_sha256'] != sha256(raw).hexdigest():
                raise ProjectError('World allocation MAP overlay source changed')
            if not isinstance(target.get('payload'),bytes) or len(target['payload']) != len(raw):
                raise ProjectError('World allocation MAP overlay has an incomplete payload')
            merged=bytearray(target['payload'])
            for i,(old,new) in enumerate(zip(raw,candidate)):
                if old==new: continue
                if merged[i] not in (old,new):
                    raise ProjectError('World allocation conflicts with another authored MAP field')
                merged[i]=new
            target.update(payload=bytes(merged),sha256=sha256(merged).hexdigest())
        else:
            overlays.append(dict(scene=scene,offset=offset,size=len(raw),payload=candidate,
                file=f'assets/{scene}-world-allocations.map',expected_sha256=sha256(raw).hexdigest(),
                sha256=sha256(candidate).hexdigest()))
        for allocation in allocations:
            changes.append(dict(scene=scene,semantic_id=allocation['placement_id'],
                field='world_placement_allocation',before_value=None,after_value=deepcopy(allocation),
                record_index=allocation['record_index'],scope='walk-decoration-cell-allocation',
                affected_source_entities=[allocation['native_seed']['entity_id']]))
    return changes

"""Retained native decoration lineage, independent of source transform edits."""
from copy import deepcopy
from hashlib import sha256
import re

from importer.worldmap_placement_allocation import allocate
from .project import ProjectError
from .worldmap_placements import SCENES, values

COMPONENT = 'WorldMapPlacementAllocations'
SCHEMA = 'legaia.worldmap-placement-allocation-ledger.v1'
MODEL_SCHEMA = 'legaia.worldmap-placement-allocation-ledger.v2'


def owner(scene):
    if scene not in SCENES:
        raise ProjectError('Choose a qualified walk kingdom')
    return f'worldmap://{scene}/placement-allocations'


def validate(project, identifier, binding):
    keys = {'schema_version','scene','source_disc_sha256','source_map_sha256','source_floor_lut_sha256','operations'}
    if (not isinstance(binding, dict) or set(binding) != keys or binding['schema_version'] not in (SCHEMA,MODEL_SCHEMA)
            or identifier != owner(binding['scene']) or any(not isinstance(binding[k],str) or not re.fullmatch(
                '[0-9a-f]{64}',binding[k]) for k in keys if k.startswith('source_'))
            or not isinstance(binding['operations'],list) or not 1 <= len(binding['operations']) <= 32):
        raise ProjectError('World placement allocation lacks exact bounded source lineage')
    if {doc['source']['disc_identity'] for doc in project.imports.values()} != {'sha256:'+binding['source_disc_sha256']}:
        raise ProjectError('World placement allocation belongs to another imported disc')
    ids = set()
    for operation in binding['operations']:
        if (not isinstance(operation,dict) or set(operation) != {'requests','proposed_map_sha256'}
                or not isinstance(operation['proposed_map_sha256'],str)
                or not re.fullmatch('[0-9a-f]{64}',operation['proposed_map_sha256'])
                or not isinstance(operation['requests'],list) or not 1 <= len(operation['requests']) <= 32):
            raise ProjectError('World placement allocation operation is malformed or unbounded')
        for request in operation['requests']:
            allowed = {'placement_id','donor_cell','target_cell','record_index','values'}
            if binding['schema_version'] == MODEL_SCHEMA and isinstance(request,dict) and 'model_pool_index' in request:
                allowed.add('model_pool_index')
            if (not isinstance(request,dict) or set(request) != allowed
                    or not isinstance(request['placement_id'],str) or not re.fullmatch(
                        r'placement://authored/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',request['placement_id'])
                    or request['placement_id'] in ids
                    or any(type(request[k]) is not int or not 0 <= request[k] < 16384 for k in ('donor_cell','target_cell'))
                    or type(request['record_index']) is not int or not 4 <= request['record_index'] < 512):
                raise ProjectError('World placement allocation identity or native indices differ')
            if 'model_pool_index' in request and (type(request['model_pool_index']) is not int or not 1 <= request['model_pool_index'] < 512):
                raise ProjectError('World placement model override requires a nonzero native pool index')
            values(request['values']);ids.add(request['placement_id'])
    if len(ids) > 511:
        raise ProjectError('World placement allocation exceeds its stable identity budget')
    return deepcopy(binding)


def replay(raw, floor, binding):
    if binding['schema_version'] not in (SCHEMA,MODEL_SCHEMA) or (binding['schema_version'] == SCHEMA and
            any('model_pool_index' in r for op in binding['operations'] for r in op['requests'])):
        raise ProjectError('World model overrides require the version-two allocation ledger')
    if sha256(raw).hexdigest() != binding['source_map_sha256']:
        raise ProjectError('World placement allocation source MAP changed')
    current = raw
    allocations = []
    for operation in binding['operations']:
        current, audit = allocate(current,floor,binding['scene'],operation['requests'])
        if audit['proposed_sha256'] != operation['proposed_map_sha256']:
            raise ProjectError('World placement allocation differs from complete retained native replay')
        allocations.extend(audit['allocations'])
    return current, allocations


def merge_transforms(raw, allocated, transformed):
    if any(not isinstance(data,bytes) or len(data) != 0x12000 for data in (raw,allocated,transformed)):
        raise ProjectError('World allocation composition requires complete native MAP inputs')
    result = bytearray(allocated)
    for i,(a,b) in enumerate(zip(raw,transformed)):
        if a == b: continue
        if allocated[i] != a:
            raise ProjectError('World placement allocation conflicts with a source transform')
        result[i] = b
    return bytes(result)


def compose(project, scene, raw, provenance, floor, transformed, binding=None):
    components = project.overrides.get(owner(scene),{})
    if components and set(components) != {COMPONENT}:
        raise ProjectError('World allocation owner accepts only its dedicated component')
    if binding is None:
        binding = components.get(COMPONENT)
    if binding is None: return transformed, []
    validate(project,owner(scene),binding)
    if any(binding[k] != provenance[k] for k in provenance):
        raise ProjectError('World placement allocation source provenance changed')
    allocated, audit = replay(raw,floor,binding)
    return merge_transforms(raw,allocated,transformed), audit

"""Native Current scene ownership retained by scripted World GLB exports."""
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
import re
from .core import ImportError
from .worldmap_placements import decode_worldmap_placements
from .worldmap_object_bind_allocation import _catalog
from .worldmap_object_binds import resolve_object_bind


def scripted_group_ids(placement_ids):
    if (not isinstance(placement_ids,list) or not 1<=len(placement_ids)<=32
            or any(not isinstance(i,str) or not re.fullmatch(r'placement://authored/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',i) for i in placement_ids)
            or placement_ids!=sorted(set(placement_ids))):
        raise ImportError('Scripted group export requires canonical saved scripted UUID membership')
    return deepcopy(placement_ids)


def group_metadata(result,key,placement_ids):
    placement_ids=scripted_group_ids(placement_ids)
    metadata=deepcopy(qualify_source(result,key))
    if not set(placement_ids).issubset({a['placement_id'] for a in metadata['authored_scripted_placements']}):
        raise ImportError('Scripted group export requires saved scripted UUID ownership')
    metadata['selected_placement_ids']=deepcopy(placement_ids)
    return metadata


def qualify_source(result,key):
    source=result.get('placement_source',{})
    if not isinstance(source,dict):raise ImportError('Scripted World export source is invalid')
    if (result.get('representation')!='current-scripted-placement-source' or result.get('placement_layer')!='current'
            or result.get('ground_layer')!='retail' or result.get('project_source_key')!=key
            or result.get('gameplay_verified') is not False or result.get('project_changed') is not False
            or source.get('schema_version')!='legaia.worldmap-scripted-placement-source.v1'
            or source.get('scene')!=result.get('scene') or source.get('source_key')!=key
            or source.get('read_only') is not True or source.get('gameplay_verified') is not False
            or source.get('project_changed') is not False or not source.get('binding')
            or not isinstance(source.get('authored_scripted_placements'),list) or not source['authored_scripted_placements']
            or not isinstance(source.get('authored_decorations'),list)):
        raise ImportError('Scripted World export requires saved Current native ownership')
    hashes={}
    for name,expected in [('source_map','source_record'),('current_map','current_map_sha256'),
                          ('source_man','source_man_sha256'),('current_man','current_man_sha256'),
                          ('fallback','fallback_sha256'),('retained_base_map',None)]:
        try:raw=b64decode(source[name+'_base64'],validate=True)
        except (KeyError,ValueError,TypeError):raise ImportError('Scripted World export native witness is invalid') from None
        digest=sha256(raw).hexdigest()
        expected_hash=source['source_record'].get('source_map_sha256') if expected=='source_record' else source.get(expected) if expected else source['binding'].get('base_map_sha256')
        if digest!=expected_hash:raise ImportError('Scripted World export native witness hash differs')
        hashes[name+'_sha256']=digest
    native=decode_worldmap_placements(b64decode(source['current_map_base64']),source['floor_lut'],scene=result['scene'])
    seeds={e['entity_id']:e for e in native['placements']};seen=set()
    for entity in result['scene_graph']['entities']:
        if entity.get('placement_scope')=='source_ground':continue
        seed=seeds.get(entity.get('native_entity_id',entity.get('entity_id')))
        if seed is None or any(entity.get(k)!=v for k,v in seed.items() if k not in ('entity_id','placement_scope')):
            raise ImportError('Scripted World export instance differs from complete Current native placement')
    allocations=source['authored_decorations']+source['authored_scripted_placements']
    scripted_ids={a['placement_id'] for a in source['authored_scripted_placements']}
    catalog=_catalog(b64decode(source['current_map_base64'])[0x10000:],b64decode(source['fallback_base64']),result['scene'])
    man=b64decode(source['current_man_base64'])
    for allocation in allocations:
        seed=allocation.get('native_seed',{});identity=seed.get('entity_id')
        if identity in seen or seeds.get(identity)!=seed:raise ImportError('Scripted World export allocation differs from Current native seed')
        seen.add(identity)
        entities=[e for e in result['scene_graph']['entities'] if e.get('authored_placement')==allocation]
        if len(entities)!=1:raise ImportError('Scripted World export allocation membership differs')
        scripted=allocation['placement_id'] in scripted_ids
        if entities[0].get('placement_scope')!=('authored_scripted_seed' if scripted else 'authored_spawn_seed'):
            raise ImportError('Scripted World export changed authored placement kind')
        if scripted and (allocation.get('shared_script') is not True or not isinstance(allocation.get('script_id'),str)
                         or not re.fullmatch(f"script://{result['scene']}/worldmap/man-p0/[0-9]{{4}}",allocation['script_id'])):
            raise ImportError('Scripted World export lost shared script identity')
        if scripted:
            anchor=seed['source_anchor'];bind=resolve_object_bind(catalog,man,anchor['col'],anchor['row'])
            if (bind['status']!='resolved_source_header' or bind['trigger']['table_source']!='primary'
                    or bind['shadowed_trigger_ids'] or allocation['script_id']!=f"script://{result['scene']}/worldmap/man-p0/{bind['man_record']['record_index']:04d}"):
                raise ImportError('Scripted World export shared script differs from its Current native bind')
    if result.get('authored_entity_count')!=len(allocations):raise ImportError('Scripted World export authored count differs')
    return dict(schema_version='legaia.worldmap-scripted-placement-export.v1',representation=result['representation'],source_key=key,
        **hashes,exported_map_sha256=hashes['current_map_sha256'],ground_layer='retail',floor_lut=deepcopy(source['floor_lut']),
        scripted_binding=deepcopy(source['binding']),authored_decorations=deepcopy(source['authored_decorations']),
        authored_scripted_placements=deepcopy(source['authored_scripted_placements']),authored_entity_count=len(allocations),
        changed_source_entity_count=result['changed_source_entity_count'],model_authoring=deepcopy(result['model_authoring']),
        texture_authoring=deepcopy(result['texture_authoring']),gameplay_verified=False,project_changed=False)

"""Metadata-only World object scripts and referenced source ANM resources."""
from copy import deepcopy
from hashlib import sha256

from .pipeline import _disc_context, REFERENCE_COMMIT
from .worldmap_geometry import load_worldmap_geometry, KINGDOM_BASES, _kingdom_table, _slot
from .field_map import load_field_map_catalog
from .worldmap_object_binds import resolve_object_bind
from .worldmap_object_script import inspect_object_script
from .animation import animation_record_ranges, decode_animation_record
from .actor_runtime_capacity import qualify_actor_pool
from .core import ImportError, validate_metadata_only

LIMITATIONS = [
    'Retail World source resources only; Current transforms and replacement meshes do not overwrite source associations.',
    'Object bindings and decoded script paths do not prove activation, story branches or gameplay reachability.',
    'Animation selectors resolve only supported source clips with exact native object/channel counts; zero IDs are not guessed.',
    'Playback timing, looping, live PC, runtime residency and general World script authoring remain unresolved; fixed source arguments and shared rigid ANM channels use separate reviewed project overrides.',
]


def load_worldmap_behavior_catalog(disc,scene):
    if scene not in KINGDOM_BASES:
        raise ImportError('World behavior resources require a supported kingdom')
    with _disc_context(disc) as (image,digest,_,archive):
        geometry=load_worldmap_geometry(disc,scene)
        fields=load_field_map_catalog(disc,scene)
        _,index,offset,bundle,carrier=_kingdom_table(archive,KINGDOM_BASES[scene])
        man,man_source=_slot(bundle,carrier,2)
        bank,bank_source=_slot(bundle,carrier,4)
        if fields['disc_sha256']!=digest or geometry['source_record']['disc_sha256']!=digest or bank_source['descriptor_type']!=5:
            raise ImportError('World behavior carrier differs from its verified geometry and MAP')
        proof=qualify_actor_pool(image.read_file(image.find('SCUS_942.54')))
        consumer=next(w for w in proof['functions'] if w['address']=='0x8003A55C')
        ranges=animation_record_ranges(bank)
        graph=geometry['scene_graph'];models={a['asset_id']:a for a in graph['assets']}
        scripts,animations={},{};unbound=[];unsupported=[];unsupported_records=[]
        for clip_index,(at,end) in enumerate(ranges):
            payload=bank[at:end]
            try:
                clip=decode_animation_record(payload)
                if not 1<=clip['frame_count']<=512 or not 1<=clip['bone_count']<=64:
                    raise ImportError('World rigid channel layout exceeds supported bounds')
            except ImportError as error:
                unsupported_records.append(dict(record_index=clip_index,byte_offset=at,byte_length=end-at,sha256=sha256(payload).hexdigest(),reason=str(error)))
                continue
            aid=f'animation://{scene}/worldmap/scene-anm/{clip_index:04d}'
            animations[aid]=dict(semantic_id=aid,asset_kind='animation',kind='animation',
                name=f'{scene} Object Animation {clip_index:04d}',source_scene=scene,
                authored_animation_id=f'animation://{scene}/worldmap/anm/{clip_index:04d}',
                source_record=dict(disc_sha256=digest,iso_file='PROT.DAT',prot_entry_index=index,
                    table_offset=offset,animation_slot=deepcopy(bank_source),record_index=clip_index,
                    byte_offset=at,byte_length=end-at,sha256=sha256(payload).hexdigest()),
                frame_count=clip['frame_count'],channel_count=clip['bone_count'],
                timing='unresolved',looping='unresolved',bindings=[],source_instance_ids=[],
                model_asset_ids=[],script_asset_ids=[])

        for entity in graph['entities']:
            if entity.get('source_layer')!='placed':continue
            anchor=entity['source_anchor'];bind=resolve_object_bind(fields,man,anchor['col'],anchor['row'])
            if bind['status']!='resolved_source_header':
                unbound.append(dict(entity_id=entity['entity_id'],status=bind['status']));continue
            report=inspect_object_script(bind,man,scene);sid=report['source_record_id'];record=bind['man_record']
            source=dict(disc_sha256=digest,iso_file='PROT.DAT',prot_entry_index=index,table_offset=offset,
                        man_slot=deepcopy(man_source),partition=0,record_index=record['record_index'],
                        flat_record_index=record['flat_record_index'],byte_offset=record['byte_offset'],
                        byte_length=record['byte_length'],sha256=record['sha256'])
            if sid not in scripts:
                scripts[sid]=dict(semantic_id=sid,asset_kind='script',kind='script',
                    name=f'{scene} Object Script {record["record_index"]:04d}',source_scene=scene,
                    source_record=source,entry_pc=report['entry_pc'],inspection_status=report['graph']['status'],
                    decoded_instruction_count=len(report['graph']['instructions']),
                    dialogue_segment_count=len(report['graph']['dialogues']),
                    opaque_region_count=len(report['graph']['opaque_regions']),
                    stopped_path_count=len(report['graph']['stops']),bindings=[],
                    source_instance_ids=[],model_asset_ids=[],animation_asset_ids=[])
            elif scripts[sid]['source_record']!=source:
                raise ImportError('World script identity has conflicting source ownership')
            selector=bind['encoded_animation_selector'];aid=None;animation_status='none_encoded'
            if selector:
                try:
                    clip_index=selector-1
                    if clip_index>=len(ranges):raise ImportError('Selector exceeds the source ANM bank')
                    at,end=ranges[clip_index];payload=bank[at:end];clip=decode_animation_record(payload)
                    if not 1<=clip['frame_count']<=512 or not 1<=clip['bone_count']<=256:
                        raise ImportError('Source animation exceeds supported preview frame/channel bounds')
                    if clip['bone_count']!=len(models[entity['asset_id']]['preview']['objects']):
                        raise ImportError('Source animation channels differ from native model objects')
                    aid=f'animation://{scene}/worldmap/scene-anm/{clip_index:04d}'
                    if aid not in animations:raise ImportError('Source animation record is outside the supported catalog')
                    animations[aid]['bindings'].append(dict(entity_id=entity['entity_id'],model_asset_id=entity['asset_id'],script_asset_id=sid,encoded_selector=selector))
                    animation_status='resolved_source_clip'
                except ImportError as error:
                    aid=None
                    unsupported.append(dict(entity_id=entity['entity_id'],encoded_selector=selector,reason=str(error)))
                    animation_status='unsupported_source_clip'
            scripts[sid]['bindings'].append(dict(entity_id=entity['entity_id'],model_asset_id=entity['asset_id'],
                trigger_id=bind['trigger']['semantic_id'],trigger_source_record=deepcopy(bind['trigger']['source_record']),
                anchor=dict(col=anchor['col'],row=anchor['row']),encoded_animation_selector=selector,
                animation_asset_id=aid,animation_status=animation_status))
        assets=[]
        for row in [*scripts.values(),*animations.values()]:
            row['bindings'].sort(key=lambda b:b['entity_id'])
            row['source_instance_ids']=sorted({b['entity_id'] for b in row['bindings']})
            row['model_asset_ids']=sorted({b['model_asset_id'] for b in row['bindings']})
            key='animation_asset_ids' if row['kind']=='script' else 'script_asset_ids'
            field='animation_asset_id' if row['kind']=='script' else 'script_asset_id'
            row[key]=sorted({b[field] for b in row['bindings'] if b[field] is not None})
            row.update(scope='global-worldmap-behavior-resources',runtime_state='not_observed',
                       reference_commit=REFERENCE_COMMIT,read_only=True,authoring='fixed_instruction_operands' if row['kind']=='script' else 'shared_rigid_channels' if row['bindings'] else 'source_metadata_only')
            assets.append(row)
        result=dict(scene=scene,assets=sorted(assets,key=lambda r:r['semantic_id']),
            consumer=dict(executable_sha256=proof['executable_sha256'],function=consumer),
            unbound=unbound,unsupported_animation_bindings=unsupported,unsupported_animation_records=unsupported_records,
            animation_bank=dict(record_count=len(ranges),source=deepcopy(bank_source)),limitations=list(LIMITATIONS))
        validate_metadata_only(result)
        return result

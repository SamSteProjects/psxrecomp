"""Source-qualified PROT 1203 section-2 rigid ANM for the PROT 1204 pack.

This pack/viewer rig is distinct from assembled PLAYER-file battle characters.
Reference evidence: pinned character-mesh.md and asset/player_anm.rs.
"""
from hashlib import sha256
import struct
from .core import ImportError,decode_lzs_sections,validate_metadata_only
from .pipeline import REFERENCE_COMMIT,_disc_context
from .animation import animation_record_ranges,decode_bone_transform,pose_vertices
from .battle_character_catalog import decode_catalog
from .assets import decode_tmd


def record(data):
    if not isinstance(data,bytes) or len(data)<16:raise ImportError('Pack animation record is truncated')
    a,frames,marker,flags=struct.unpack_from('<4H',data);bones=a&255
    if a>>8!=1 or marker!=0x080c or flags not in (0x201,0x401,0x402) or not 1<=bones<=64 or not 1<=frames<=512 or len(data)!=16+bones*frames*8 or any(data[-8:]):raise ImportError('Pack ANM header, extent or trailer is unsupported')
    return dict(header_a=a,header_flags=flags,bone_count=bones,frame_count=frames)


def decode_catalogue(raw,digest):
    if len(raw)>2*1024*1024:raise ImportError('Pack ANM container exceeds bounds')
    sections=decode_lzs_sections(raw)
    if len(sections)!=4 or sections[2][0].index!=2:raise ImportError('Pack ANM requires the qualified four-section container')
    section,bank,used=sections[2];ranges=animation_record_ranges(bank)
    if len(ranges)!=30:raise ImportError('Pack ANM bank differs from the 30-record corpus')
    entry_hash=sha256(raw).hexdigest();bank_hash=sha256(bank).hexdigest();clips=[]
    for i,(start,end) in enumerate(ranges):
        data=bank[start:end];layout=record(data);expected=15 if i<9 or 18<=i<27 else 16 if i<18 else 10
        if layout['bone_count']!=expected:raise ImportError('Pack ANM channel count differs from its structural bank')
        slot=0 if i<9 else 1 if i<18 else 2 if i<27 else None
        clips.append(dict(semantic_id=f'animation://legaia/battle-character-pack/{i:04d}',asset_kind='animation',name=f'Pack Reference ANM {i}',source_record=dict(disc=dict(sha256=digest,serial='SCUS-94254'),iso_file='PROT.DAT',prot_entry_index=1203,record_kind='decoded_lzs_section',container_section=2,compressed_stream_offset=section.stream_offset,compressed_bytes_consumed=used,containing_size=len(bank),containing_sha256=bank_hash,source_entry_sha256=entry_hash,record_index=i,byte_offset=start,byte_length=end-start,sha256=sha256(data).hexdigest()),**layout,model_asset_id=f'asset://legaia/models/battle-character/{slot:04x}' if slot is not None else None,association='pinned_pack_object_order_and_retail_channel_count' if slot is not None else 'unmatched_simplified_pack_rig',reference_commit=REFERENCE_COMMIT))
    catalog=dict(schema_version='legaia.battle-pack-animation-catalog.v1',source_disc_sha256=digest,source_entry_sha256=entry_hash,source_bank_sha256=bank_hash,source_key=sha256(('battle-pack-anm-v1:'+digest+':'+entry_hash+':'+bank_hash).encode()).hexdigest(),clips=clips,reference_commit=REFERENCE_COMMIT,read_only=True,project_changed=False,gameplay_verified=False,timing='unresolved',runtime_state='not_observed',limitations=['Pack/viewer ANM, not PLAYER-file assembled battle animation.','Reference object ordering plus native count agreement supports source-only pose inspection.','Runtime cadence, looping, activation, equipment and GTE rounding are not established.'])
    validate_metadata_only(catalog);return catalog,bank


def discover(disc):
    with _disc_context(disc) as (_,digest,_,archive):return decode_catalogue(archive.read_entry(archive.entry(1203)),digest)[0]


def clip_frames(disc,model_id,animation_id,model_source_key,animation_source_key):
    """Read a complete qualified pack clip once, without inferring cadence."""
    with _disc_context(disc) as (_,digest,_,archive):
        models=decode_catalog(archive.read_entry(archive.entry(1204)),digest)
        catalog,bank=decode_catalogue(archive.read_entry(archive.entry(1203)),digest)
        if models['source_key']!=model_source_key or catalog['source_key']!=animation_source_key:raise ImportError('Pack model or animation source changed')
        model=next((r for r in models['models'] if r['semantic_id']==model_id),None);clip=next((r for r in catalog['clips'] if r['semantic_id']==animation_id),None)
        if model is None or clip is None or clip['model_asset_id']!=model_id or clip['bone_count']!=model['source_record']['object_count']:raise ImportError('Choose a qualified matching pack model and clip')
        source=clip['source_record'];data=bank[source['byte_offset']:source['byte_offset']+source['byte_length']]
        frames=[]
        for frame in range(clip['frame_count']):
            transforms=[dict(object_index=i,**decode_bone_transform(data[8+(frame*clip['bone_count']+i)*8:16+(frame*clip['bone_count']+i)*8])) for i in range(clip['bone_count'])]
            frames.append(dict(object_transforms=transforms))
        return catalog,model,clip,frames


def pose(disc,model_id,animation_id,model_source_key,animation_source_key,frame_index):
    with _disc_context(disc) as (_,digest,_,archive):
        raw=archive.read_entry(archive.entry(1204));models=decode_catalog(raw,digest);catalog,bank=decode_catalogue(archive.read_entry(archive.entry(1203)),digest)
        if models['source_key']!=model_source_key or catalog['source_key']!=animation_source_key:raise ImportError('Pack model or animation source changed')
        model=next((r for r in models['models'] if r['semantic_id']==model_id),None);clip=next((r for r in catalog['clips'] if r['semantic_id']==animation_id),None)
        if model is None or clip is None or clip['model_asset_id']!=model_id or clip['bone_count']!=model['source_record']['object_count'] or type(frame_index) is not int or not 0<=frame_index<clip['frame_count']:raise ImportError('Choose a qualified matching pack model, clip and native frame')
        source=model['source_record'];geometry=decode_tmd(raw[source['byte_offset']:source['byte_offset']+source['byte_length']]);source=clip['source_record'];data=bank[source['byte_offset']:source['byte_offset']+source['byte_length']];transforms=[dict(object_index=i,**decode_bone_transform(data[8+(frame_index*clip['bone_count']+i)*8:16+(frame_index*clip['bone_count']+i)*8])) for i in range(clip['bone_count'])]
        geometry['vertices']=pose_vertices(geometry['vertices'],geometry['objects'],transforms);geometry['bounds']=dict(min=[min(v[i] for v in geometry['vertices']) for i in range(3)],max=[max(v[i] for v in geometry['vertices']) for i in range(3)]);geometry['posed']=True;geometry['coordinate_system']='retail_psx_actor_local_y_down';geometry['semantic_id']=model_id
        # Normals are not relabelled as posed; geometry rendering uses existing color fallback.
        geometry.pop('triangle_normals',None);geometry.pop('normal_preview',None)
        return models,catalog,model,clip,geometry,transforms

"""Source-selected field-party descriptor swaps; no inferred live equipment."""
from hashlib import sha256
import struct
from .core import ImportError
from .assets import decode_tmd,load_model_source

GROUPS=(0,3,5)
EQUIP_RECORD_OFFSETS=(0x196,0x199,0x19b)


def project_field_equipment(raw,slot,equip_byte):
    if type(slot) is not int or not 0<=slot<3 or type(equip_byte) is not int or not 0<=equip_byte<=255:
        raise ImportError('Field equipment requires one party source slot and an explicit equipment byte')
    original=decode_tmd(raw)
    if len(original['objects'])!=12:raise ImportError('Field equipment source must retain twelve original object descriptors')
    source=12+(11 if equip_byte==0 else 10)*28;target=12+GROUPS[slot]*28
    result=bytearray(raw);result[target:target+28]=raw[source:source+28];result=bytes(result)
    if result[:target]!=raw[:target] or result[target+28:]!=raw[target+28:]:raise ImportError('Field equipment projection changed bytes outside the target descriptor')
    decode_tmd(result)
    return result,dict(schema_version='legaia.field-equipment-projection.v1',party_slot=slot,
        selected_equipment_byte=equip_byte,selection='zero' if equip_byte==0 else 'nonzero',
        source_descriptor_index=11 if equip_byte==0 else 10,target_descriptor_index=GROUPS[slot],
        source_descriptor_offset=source,target_descriptor_offset=target,descriptor_byte_length=28,
        equipment_record_offset=EQUIP_RECORD_OFFSETS[slot],active_object_count=10,
        source_sha256=sha256(raw).hexdigest(),projected_sha256=sha256(result).hexdigest(),
        source_descriptor_sha256=sha256(raw[source:source+28]).hexdigest(),
        runtime_equipment='not_observed',authored=False,gameplay_verified=False)


def load_field_equipment_preview(disc,asset,equip_byte):
    ids=[f'asset://legaia/models/global-special/{0xf0+i:04x}' for i in range(3)]
    source=asset.get('source_record',{})
    if asset.get('semantic_id') not in ids or source.get('prot_entry_index')!=874 or source.get('container_section')!=0 or source.get('pack_slot')!=ids.index(asset['semantic_id']):raise ImportError('Field equipment requires its qualified global party source')
    raw=load_model_source(disc,asset);projected,proof=project_field_equipment(raw,ids.index(asset['semantic_id']),equip_byte);g=decode_tmd(projected)
    objects=g['objects'][:10];vertices=sum(o['vertex_count'] for o in objects);triangles=sum(o['triangle_count'] for o in objects)
    g['objects']=objects;g['vertices']=g['vertices'][:vertices]
    for key in ('triangles','triangle_colors','triangle_uvs','triangle_materials','triangle_normals'):g[key]=g[key][:triangles]
    g['bounds']=dict(min=[min(v[i] for v in g['vertices']) for i in range(3)],max=[max(v[i] for v in g['vertices']) for i in range(3)])
    g.update(semantic_id=asset['semantic_id'],source_record=source,equipment_variant=proof)
    return g

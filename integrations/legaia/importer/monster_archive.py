"""Source-qualified monster records/models in PROT 867, not live actors.

Evidence: pinned monster_archive/{mesh,record}.rs and FUN_800542C8.
The fixed 0x14000 slot selects an LZS stream. Actual consumption, including
any slot spill, is retained explicitly; no writable allocation is inferred.
"""
from hashlib import sha256
import struct
from .core import ImportError,decompress_lzs,validate_metadata_only,TMD_MAGIC
from .pipeline import REFERENCE_COMMIT,_disc_context
from .assets import decode_tmd

ENTRY=867
STRIDE=0x14000
MAX_DECODED=STRIDE*8
LIMITATIONS=[
 'Stored monster record values, not runtime-boosted battle stats or confirmed live actors.',
 'Object-local TMD only; assembly, texture relocation, motion, activation and equipment are not inferred.',
 'Actual compressed consumption is qualified against the archive; fixed slot boundaries do not establish writable capacity.',
]


def block(content,identifier):
    if not isinstance(content,bytes) or type(identifier) is not int or not 1<=identifier<=512:
        raise ImportError('Monster archive requires exact source bytes and a bounded 1-based slot')
    start=(identifier-1)*STRIDE
    if start+4>len(content):raise ImportError('Monster slot header is outside the archive')
    size=struct.unpack_from('<I',content,start)[0]
    if not 0x4c<=size<=MAX_DECODED:return None
    decoded,used=decompress_lzs(content[start+4:],size)
    return decoded,used


def decode_catalog(content,disc_sha256):
    if not isinstance(content,bytes) or not 4<=len(content)<=STRIDE*512:
        raise ImportError('Monster archive exceeds its bounded source extent')
    if not isinstance(disc_sha256,str) or len(disc_sha256)!=64 or any(c not in '0123456789abcdef' for c in disc_sha256):
        raise ImportError('Monster archive requires an immutable disc hash')
    archive_hash=sha256(content).hexdigest();models=[];textures=[];records=[];unavailable=[]
    for index in range((len(content)+STRIDE-1)//STRIDE):
        identifier=index+1;start=index*STRIDE
        try:decoded=block(content,identifier)
        except ImportError as e:
            unavailable.append(dict(monster_id=identifier,status='invalid_stream',reason=str(e)));continue
        if decoded is None:
            unavailable.append(dict(monster_id=identifier,status='empty_or_unsupported_header'));continue
        data,used=decoded;name_at,model_at,texture_at=struct.unpack_from('<3I',data)
        source=dict(disc=dict(sha256=disc_sha256,serial='SCUS-94254'),iso_file='PROT.DAT',prot_entry_index=ENTRY,
            record_kind='decoded_monster_slot',monster_id=identifier,slot_offset=start,slot_stride=STRIDE,
            compressed_stream_offset=start+4,compressed_bytes_consumed=used,compressed_sha256=sha256(content[start+4:start+4+used]).hexdigest(),
            compressed_slot_overrun=used>STRIDE-4,containing_size=len(data),containing_sha256=sha256(data).hexdigest(),
            archive_byte_length=len(content),archive_sha256=archive_hash,byte_coordinate_space='decoded_monster_slot')
        name=None
        if 0x4c<=name_at<len(data):
            end=data.find(b'\0',name_at,min(len(data),name_at+129))
            if end!=-1:
                raw=data[name_at:end].lstrip(bytes(range(32)))
                if raw and all(32<=c<127 for c in raw):name=raw.decode('ascii')
        record=dict(semantic_id=f'monster-record://legaia/867/{identifier:04d}',asset_kind='monster_record',monster_id=identifier,
            name=name,stored_stats=dict(zip(('hp','agility','mp','attack','defense_high','defense_low','intelligence','speed'),struct.unpack_from('<8H',data,12))),
            stored_rewards=dict(gold=struct.unpack_from('<H',data,0x44)[0],experience=struct.unpack_from('<H',data,0x46)[0],drop_item=data[0x48],drop_chance=data[0x49]),
            element_byte=data[0x1d],spell_entry_count=data[0x4a],name_offset=name_at,model_offset=model_at,texture_offset=texture_at,
            source_record=dict(source,byte_offset=0,byte_length=0x4c,sha256=sha256(data[:0x4c]).hexdigest()),reference_commit=REFERENCE_COMMIT)
        from .monster_textures import layout
        try:
            pool,width=layout(data,texture_at)
            texture_id=f'texture://legaia/monster-archive/{identifier:04d}/pool'
            record.update(texture_status='available',texture_asset_id=texture_id)
            textures.append(dict(semantic_id=texture_id,asset_kind='texture',name=f'Monster {identifier} Texture Pool',monster_id=identifier,
                model_asset_id=None,width=width,height=256,bpp=4,palette_count=15,
                source_record=dict(source,byte_offset=texture_at,byte_length=len(pool),sha256=sha256(pool).hexdigest()),
                palette_byte_length=480,image_byte_length=len(pool)-480,preview_supported=True,reference_commit=REFERENCE_COMMIT))
        except ImportError as e:record.update(texture_status='unsupported',texture_diagnostic=str(e))
        records.append(record)
        if model_at<0x4c or model_at+12>len(data) or struct.unpack_from('<I',data,model_at)[0]!=TMD_MAGIC:
            record['model_status']='absent_or_unsupported';continue
        # The texture pool, when following the model, bounds its source region.
        end=texture_at if model_at<texture_at<=len(data) else len(data)
        body=data[model_at:end]
        try:geometry=decode_tmd(body)
        except ImportError as e:
            record.update(model_status='unsupported',model_diagnostic=str(e));continue
        identifier_model=f'asset://legaia/models/monster-archive/{identifier:04d}'
        record.update(model_status='available',model_asset_id=identifier_model)
        for texture in textures:
            if texture['monster_id']==identifier:texture['model_asset_id']=identifier_model
        models.append(dict(semantic_id=identifier_model,asset_kind='tmd_model',name=f'Monster {identifier}'+(f' ({name})' if name else ''),monster_id=identifier,
            record_asset_id=record['semantic_id'],source_record=dict(source,byte_offset=model_at,byte_length=len(body),sha256=sha256(body).hexdigest()),
            preview_supported=True,preview_summary=dict(objects=len(geometry['objects']),vertices=len(geometry['vertices']),triangles=len(geometry['triangles'])),reference_commit=REFERENCE_COMMIT))
    catalog=dict(schema_version='legaia.monster-archive-catalog.v1',source_disc_sha256=disc_sha256,source_archive_sha256=archive_hash,
        source_archive_byte_length=len(content),source_key=sha256(('monster-archive-v1:'+disc_sha256+':'+archive_hash).encode()).hexdigest(),
        models=models,textures=textures,records=records,unavailable_slots=unavailable,slot_count=(len(content)+STRIDE-1)//STRIDE,
        limitations=LIMITATIONS.copy(),reference_commit=REFERENCE_COMMIT,read_only=True,project_changed=False,gameplay_verified=False)
    validate_metadata_only(catalog);return catalog


def discover(disc):
    with _disc_context(disc) as (_,digest,_,archive):return decode_catalog(archive.read_entry(archive.entry(ENTRY)),digest)


def preview(disc,asset_id,expected_source_key):
    with _disc_context(disc) as (_,digest,_,archive):
        raw=archive.read_entry(archive.entry(ENTRY));catalog=decode_catalog(raw,digest)
        if expected_source_key!=catalog['source_key']:raise ImportError('Monster source changed; refresh discovery')
        record=next((r for r in catalog['models'] if r['semantic_id']==asset_id),None)
        if record is None:raise ImportError('Monster model is unsupported or absent from the qualified catalog')
        data,_=block(raw,record['monster_id']);source=record['source_record'];body=data[source['byte_offset']:source['byte_offset']+source['byte_length']]
        if sha256(body).hexdigest()!=source['sha256']:raise ImportError('Monster model source changed')
        return catalog,record,decode_tmd(body),body

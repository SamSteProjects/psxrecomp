"""Bounded structural discovery of SCUS-94254 PROT 1204 battle-form resources.

Layout evidence: pinned asset/battle_char_pack.rs. Bodies use existing SDK
TMD/TIM decoders. Reference character labels and runtime assembly are not facts
established by this reader. Metadata contains no extracted payload.
"""
from hashlib import sha256
import re
import struct
from .core import ImportError, validate_metadata_only
from .pipeline import REFERENCE_COMMIT, _disc_context
from .assets import decode_tmd
from .textures import parse_tim, decode_tim, TextureCatalog, associate_material

ENTRY=1204
FIRST_ATLAS=0x25804
ATLAS_STRIDE=0x8224
CLUT_ROWS=(490,491,492,493,494,495,497)
LIMITATIONS=[
 'Structural PROT 1204 discovery; source labels do not establish runtime character identities.',
 'Models remain object-local and unposed; equipment groups, assembly, material routing and animation are not inferred.',
 'Texture spans stay within the qualified PROT entry; truncated atlas payloads are not padded or borrowed from neighboring entries.',
 'No runtime residency, activation, gameplay or complete battle/ETMD format coverage is established.',
]

def decode_catalog(content,disc_sha256):
    if not isinstance(content,bytes) or not 12<=len(content)<=2*1024*1024 or not isinstance(disc_sha256,str) or not re.fullmatch('[a-f0-9]{64}',disc_sha256):
        raise ImportError('Battle character catalog requires a bounded entry and verified disc identity')
    bank_hash=sha256(content).hexdigest();models=[];textures=[];cursor=0
    def locator(start,length,index):
        return dict(disc=dict(sha256=disc_sha256,serial='SCUS-94254'),iso_file='PROT.DAT',prot_entry_index=ENTRY,prot_entry_name='other5',record_kind='raw_prot_entry',record_index=index,byte_offset=start,byte_length=length,byte_coordinate_space='prot_entry',containing_size=len(content),containing_sha256=bank_hash,sha256=sha256(content[start:start+length]).hexdigest())
    for slot in range(5):
        if cursor+4>min(len(content),FIRST_ATLAS):raise ImportError('Battle model stream header is truncated')
        header=struct.unpack_from('<I',content,cursor)[0];size=header&0xffffff;start=cursor+4
        if header>>24!=9 or size<12 or start+size>min(len(content),FIRST_ATLAS):raise ImportError('Battle model stream type or span is unsupported')
        body=content[start:start+size];preview=decode_tmd(body)
        source=locator(start,size,slot);source.update(stream_header_offset=cursor,stream_chunk_type=9,object_count=len(preview['objects']),tmd_byte_length=size)
        models.append(dict(semantic_id=f'asset://legaia/models/battle-character/{slot:04x}',asset_kind='tmd_model',name=f'Battle Pack Model {slot}',pool='battle_character',pool_index=slot,source_record=source,preview_supported=True,preview_summary=dict(objects=len(preview['objects']),vertices=len(preview['vertices']),triangles=len(preview['triangles'])),reference_commit=REFERENCE_COMMIT))
        cursor=start+size
    if cursor+4>FIRST_ATLAS or content[cursor:cursor+4]!=bytes(4):raise ImportError('Battle model stream has no qualified zero terminator')
    for index,row in enumerate(CLUT_ROWS):
        start=FIRST_ATLAS+index*ATLAS_STRIDE;available=min(ATLAS_STRIDE,len(content)-start)
        if available<20:raise ImportError('Battle atlas header is truncated')
        magic,flags,clut_size=struct.unpack_from('<III',content,start)
        if magic!=16 or flags!=8 or clut_size!=524:raise ImportError('Battle atlas prefix is unsupported')
        cx,cy,cw,ch=struct.unpack_from('<4H',content,start+12)
        image_at=start+8+clut_size
        if image_at+12>start+available:raise ImportError('Battle atlas image header is truncated')
        image_size,ix,iy,iw,ih=struct.unpack_from('<I4H',content,image_at)
        if (cx,cy,cw,ch)!=(0,row,256,1) or (iw,ih)!=(64,256) or ix>=1024 or iy>=512 or image_size!=12+iw*ih*2:raise ImportError('Battle atlas dimensions or CLUT row differ from qualified layout')
        declared=8+clut_size+image_size;complete=declared<=available
        if complete:parse_tim(content[start:start+declared])
        source=locator(start,declared if complete else available,index);source['pack_slot']=index
        textures.append(dict(semantic_id=f'texture://legaia/battle-character/{index:04x}',asset_kind='texture',name=f'Battle Pack TIM {index}',source_record=source,width=256,height=256,bpp=4,palette_count=16,image=dict(x=ix,y=iy,width_words=iw,height=ih),clut=dict(x=cx,y=cy,width_words=cw,height=ch),declared_byte_length=declared,available_byte_length=available,preview_supported=complete,status='available' if complete else 'partial',diagnostics=[] if complete else ['TIM image payload is truncated within the qualified PROT entry'],reference_commit=REFERENCE_COMMIT))
    result=dict(schema_version='legaia.battle-character-catalog.v1',source_disc_sha256=disc_sha256,source_entry_index=ENTRY,source_entry_sha256=bank_hash,source_entry_byte_length=len(content),source_key=sha256(('battle-character-v1:'+disc_sha256+':'+bank_hash).encode()).hexdigest(),models=models,textures=textures,reference_commit=REFERENCE_COMMIT,limitations=LIMITATIONS.copy(),read_only=True,project_changed=False,gameplay_verified=False)
    validate_metadata_only(result)
    return result

def discover(disc):
    with _disc_context(disc) as (_,digest,_,archive):
        return decode_catalog(archive.read_entry(archive.entry(ENTRY)),digest)

def preview(disc,asset_id,expected_source_key,palette_index=0):
    with _disc_context(disc) as (_,digest,_,archive):
        content=archive.read_entry(archive.entry(ENTRY));catalog=decode_catalog(content,digest)
        if expected_source_key!=catalog['source_key']:raise ImportError('Battle resource source changed; refresh discovery')
        matches=[r for r in catalog['models']+catalog['textures'] if r['semantic_id']==asset_id]
        if len(matches)!=1 or not matches[0]['preview_supported']:raise ImportError('Battle resource preview is unavailable or unqualified')
        record=matches[0];source=record['source_record'];body=content[source['byte_offset']:source['byte_offset']+source['byte_length']]
        if record['asset_kind']=='tmd_model':
            if type(palette_index) is not int or palette_index!=0:raise ImportError('Battle model preview accepts no palette override')
            value=decode_tmd(body)
            value['textures']=material_textures(content,catalog,value)
        else:
            if type(palette_index) is not int or not 0<=palette_index<record['palette_count']:raise ImportError('Battle TIM palette index is outside its native local palettes')
            value=decode_tim(body,palette_index)
        return catalog,record,value


def material_textures(content,catalog,model):
    """Static pack address coverage; exclude incomplete TIMs without relocation."""
    textures=TextureCatalog('battle-character',catalog['source_disc_sha256'])
    for record in catalog['textures']:
        if record['preview_supported']:
            source=record['source_record']
            textures.textures.append((parse_tim(content[source['byte_offset']:source['byte_offset']+source['byte_length']]),{'semantic_id':record['semantic_id']}))
    result=[]
    for index,material in enumerate(model['materials']):
        uvs=[uv for triangle,m in enumerate(model['triangle_materials']) if m==index for uv in (model['triangle_uvs'][triangle] or [])]
        bounds=(min(u[0] for u in uvs),min(u[1] for u in uvs),max(u[0] for u in uvs),max(u[1] for u in uvs)) if uvs else (0,0,255,255)
        crop=associate_material(textures,material,bounds)
        result.append(dict(crop,material_index=index))
    return result

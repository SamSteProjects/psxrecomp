"""Static selected PLAYER upload reconstruction in original authoring addresses."""
from hashlib import sha256
import struct
from .core import ImportError,decompress_lzs
from .pipeline import _disc_context,REFERENCE_COMMIT
from .textures import Tim,TimBlock,TextureCatalog,associate_material

SECTIONS=[(0,128,32,128),(0,0,64,128),(64,0,32,128),(64,128,32,128),(96,128,32,128)]
RECORD0=[(32,128,32,128),(96,0,32,128)]


def placement(disc):
    with _disc_context(disc) as (image,digest,_,_):
        exe=image.read_file(image.find('SCUS_942.54'))
        if exe[:8]!=b'PS-X EXE':raise ImportError('PLAYER texture placement requires the retail executable')
        load=struct.unpack_from('<I',exe,0x18)[0];offset=0x800775b8-load+0x800
        if offset<0x800 or offset+40>len(exe) or list(struct.unpack_from('<20H',exe,offset))!=[n for r in SECTIONS for n in r]:raise ImportError('PLAYER equipment upload rectangles differ from the pinned retail table')
        return dict(disc_sha256=digest,iso_file='SCUS_942.54',file_sha256=sha256(exe).hexdigest(),byte_offset=offset,byte_length=40,sha256=sha256(exe[offset:offset+40]).hexdigest(),rectangles=[list(r) for r in SECTIONS],reference_commit=REFERENCE_COMMIT)


def uploads(raw,slot,assembly,digest):
    desc,ca,cb,budget=struct.unpack_from('<4I',raw);bank,used=decompress_lzs(raw[16:desc],budget);out=[]
    def block(decoded,offset,bound,rect,identity,kind,compressed_hash,decoded_hash):
        x,y,w,h=rect
        if offset+4>bound:raise ImportError('PLAYER upload prefix exceeds its decoded source')
        cx,cn=struct.unpack_from('<2H',decoded,offset);end=offset+4+cn*2+w*h*2
        if cx+cn>1024 or end>bound:raise ImportError('PLAYER image or CLUT run exceeds its decoded source')
        palette=list(struct.unpack_from(f'<{cn}H',decoded,offset+4));pixels=decoded[offset+4+cn*2:end]
        meta=dict(semantic_id=identity,source_record=dict(disc_sha256=digest,prot_entry_index=863+slot,source_entry_sha256=sha256(raw).hexdigest(),record_kind=kind,compressed_sha256=compressed_hash,containing_sha256=decoded_hash,containing_size=len(decoded),byte_offset=offset,byte_length=end-offset,sha256=sha256(decoded[offset:end]).hexdigest()),band_rectangle=list(rect),clut_x=cx,clut_count=cn,image_sha256=sha256(pixels).hexdigest(),palette_source_sha256=sha256(decoded[offset+4:offset+4+cn*2]).hexdigest())
        out.append(dict(metadata=meta,pixels=pixels,palette=[v|0x8000 if v else 0 for v in palette]))
    for i,(at,bound,rect) in enumerate([(ca,cb,RECORD0[0]),(cb,budget,RECORD0[1])]):
        block(bank,at,bound,rect,f'texture://legaia/player-battle/{slot:04d}/record0/{i:04d}','decoded_player_record0_texture',sha256(raw[16:16+used]).hexdigest(),sha256(bank).hexdigest());out[-1]['metadata']['record0_index']=i
    for r in assembly['sections']:
        section=r['section_index']
        at=r['byte_offset'];n=struct.unpack_from('<I',raw,at)[0];d,used=decompress_lzs(raw[at+4:at+r['byte_length']],n)
        if sha256(d).hexdigest()!=r['decoded_sha256']:raise ImportError('PLAYER selected section changed before texture reconstruction')
        if not r['upload_flag']:continue
        block(d,r['tmd_body_end'],len(d),SECTIONS[section],f'texture://legaia/player-battle/{slot:04d}/section/{section}/record/{r["record_index"]:04d}','decoded_player_equipment_texture',r['compressed_sha256'],r['decoded_sha256'])
        out[-1]['metadata'].update(section_index=section,record_index=r['record_index'],item_id=r['item_id'])
    return out


def records(raw,slot,digest):
    from .player_battle import table
    selected=[]
    for r in table(raw):
        at=r['byte_offset'];n=struct.unpack_from('<I',raw,at)[0];d,used=decompress_lzs(raw[at+4:at+r['byte_length']],n)
        selected.append(dict(r,decoded_sha256=sha256(d).hexdigest(),compressed_sha256=sha256(raw[at:at+4+used]).hexdigest(),upload_flag=struct.unpack_from('<H',d,18)[0],tmd_body_end=struct.unpack_from('<I',d,12)[0]))
    result=[]
    for b in uploads(raw,slot,{'sections':selected},digest):
        m=b['metadata'];m.update(asset_kind='player_texture_upload',name=f'PLAYER {slot} '+(f'Section {m["section_index"]} Record {m["record_index"]} Texture' if 'section_index' in m else f'Record0 Texture {m["record0_index"]}'),model_asset_id=f'asset://legaia/models/player-battle/{slot:04d}',reference_commit=REFERENCE_COMMIT)
        result.append(m)
    return result


def reconstruct(disc,model,assembly,geometry):
    from .player_battle import _sources
    digest,sources=_sources(disc);raw=sources[model['player_index']][3];proof=placement(disc)
    if digest!=model['source_record']['disc']['sha256'] or sha256(raw).hexdigest()!=model['source_record']['sha256'] or proof['disc_sha256']!=digest:raise ImportError('PLAYER texture source changed')
    return reconstruct_source(raw,model['player_index'],digest,assembly,geometry,proof)


def reconstruct_source(raw,slot,digest,assembly,geometry,proof):
    blocks=uploads(raw,slot,assembly,digest)
    # Proven loader order, not an unordered union of conflicting palette uploads.
    owners={};words={}
    for i,b in enumerate(blocks):
        for j,v in enumerate(b['palette']):x=b['metadata']['clut_x']+j;owners[x]=i;words[x]=v
    catalog=TextureCatalog('player-battle-authoring-projection',digest)
    for i,b in enumerate(blocks):
        m=b['metadata'];x,y,w,h=m['band_rectangle'];image=TimBlock(320+x,256+y,w,h,b['pixels']);runs=[];cursor=0
        while cursor<1024:
            if owners.get(cursor)!=i:cursor+=1;continue
            start=cursor
            while cursor<1024 and owners.get(cursor)==i:cursor+=1
            runs.append(TimBlock(start,480,cursor-start,1,struct.pack(f'<{cursor-start}H',*[words[j] for j in range(start,cursor)])))
        for clut in runs or [None]:catalog.textures.append((Tim(4,image,clut,len(b['pixels'])),{'semantic_id':m['semantic_id']}))
    textures=[]
    for i,material in enumerate(geometry['materials']):
        uvs=[uv for j,index in enumerate(geometry['triangle_materials']) if index==i for uv in (geometry['triangle_uvs'][j] or [])];bounds=(min(v[0] for v in uvs),min(v[1] for v in uvs),max(v[0] for v in uvs),max(v[1] for v in uvs)) if uvs else (0,0,255,255)
        textures.append(dict(associate_material(catalog,material,bounds),material_index=i))
    receipt=dict(schema_version='legaia.player-texture-assembly.v1',placement=proof,uploads=[b['metadata'] for b in blocks],projection='authoring_pages_15_16_clut_row480',upload_order='record0_A_B_then_selected_flagged_sections',palette_transform='nonzero_words_OR_8000',runtime_residency='not_observed')
    return textures,receipt
